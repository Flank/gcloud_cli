# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for runtime fingerprinting and config generation."""

from __future__ import absolute_import
import contextlib
import os
import re
import textwrap

import enum

from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app import ext_runtime_adapter
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.api_lib.app.runtimes import go
from googlecloudsdk.api_lib.app.runtimes import java
from googlecloudsdk.api_lib.app.runtimes import nodejs
from googlecloudsdk.api_lib.app.runtimes import python
from googlecloudsdk.api_lib.app.runtimes import python_compat
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
from googlecloudsdk.third_party.appengine.api import appinfo
import mock

BASE_DOCKERFILE = textwrap.dedent("""\
    # Dockerfile extending the generic Node image with application files for a
    # single application.
    FROM gcr.io/google_appengine/nodejs
    """)
GO_DOCKERFILE = go.DOCKERFILE


class FakeConfigurator(ext_runtime.Configurator):

  def __init__(self, module):
    self.module = module

  def GenerateConfigs(self):
    self.module.configs_generated = True

  def GenerateConfigData(self):
    return ['myfile']

# Don't complain about using 'appinfo' as a variable name.
# pylint:disable=redefined-outer-name


class FakeRuntimeModule(object):

  NAME = 'Fake'
  ALLOWED_RUNTIME_NAMES = None

  def __init__(self):
    self.configs_generated = False
    self.params = None

  def Fingerprint(self, path, params):
    self.params = params
    if os.path.exists(os.path.join(path, 'fake')):
      return FakeConfigurator(self)
    else:
      return None


@test_case.Filters.DoNotRunIf(not properties.VALUES.app.runtime_root.Get(),
                              'No app runtime root is configured')
class RuntimeSelectionTests(sdk_test_base.WithLogCapture,
                            test_case.WithOutputCapture):

  def SetUp(self):
    self._nodejs = ext_runtime_adapter.CoreRuntimeLoader(
        'nodejs', 'Node.js', ['nodejs', 'custom'])

  def MatchingDirectoryTest(self, gen_configs):
    self.fake_runtime = FakeRuntimeModule()
    with mock.patch('googlecloudsdk.api_lib.app.runtimes.fingerprinter'
                    '.RUNTIMES',
                    [self.fake_runtime]):
      self.Touch(directory=self.temp_path,
                 name='fake', contents='fake contents')
      gen_configs()
    self.assertTrue(self.fake_runtime.configs_generated)

  def AssertGenfileExistsWithContents(self, gen_files, filename, contents):
    """Check for filename/contents in list of ext_runtime.GeneratedFile objs."""
    for gen_file in gen_files:
      if gen_file.filename == filename:
        self.assertEqual(gen_file.contents, contents)
        break
    else:
      self.fail('filename %r not found in gen_files %r', filename, gen_files)

  def testMatchingDirectory(self):
    self.MatchingDirectoryTest(
        lambda: fingerprinter.GenerateConfigs(self.temp_path))
    self.assertEqual(self.fake_runtime.params.appinfo, None)

  def testMatchingDirectoryWithParams(self):
    fake_params = ext_runtime.Params()
    self.MatchingDirectoryTest(
        lambda: fingerprinter.GenerateConfigs(self.temp_path, fake_params))
    self.assertEqual(self.fake_runtime.params, fake_params)

  def testCustomTranslationToFlag(self):
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: custom
        env: 2
        """))
    self.MatchingDirectoryTest(
        lambda: fingerprinter.GenerateConfigs(
            self.temp_path,
            ext_runtime.Params(appinfo=config, deploy=True)))
    self.assertTrue(self.fake_runtime.params.custom)

    # Make sure the translation doesn't always happen
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: nodejs
        env: 2
        """))
    self.MatchingDirectoryTest(
        lambda: fingerprinter.GenerateConfigs(
            self.temp_path,
            ext_runtime.Params(appinfo=config, deploy=True)))
    self.assertFalse(self.fake_runtime.params.custom)

  def testNodeJSServerJSOnly(self):
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    fingerprinter.GenerateConfigs(self.temp_path)
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='nodejs'),
        self.temp_path,
        'app.yaml')

    fingerprinter.GenerateConfigs(self.temp_path,
                                  ext_runtime.Params(deploy=True))
    self.AssertFileExistsWithContents(BASE_DOCKERFILE + textwrap.dedent("""\
        COPY . /app/
        CMD node server.js
        """), self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(nodejs.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testNodeJSServerJSOnlyNoWrite(self):
    """Test GenerateConfigData with nodejs server app."""
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    fingerprinter.GenerateConfigs(self.temp_path)
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='nodejs'),
        self.temp_path,
        'app.yaml')

    cfg_files = fingerprinter.GenerateConfigData(
        self.temp_path,
        ext_runtime.Params(deploy=True))
    self.assertEqual({'.dockerignore', 'Dockerfile'},
                     {cfg_file.filename for cfg_file in cfg_files})
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         BASE_DOCKERFILE + textwrap.dedent("""\
        COPY . /app/
        CMD node server.js
        """))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         nodejs.DOCKERIGNORE)

  def testNodeJSPackageJson(self):
    self.Touch(directory=self.temp_path,
               name='foo.js', contents='bogus contents')
    self.Touch(directory=self.temp_path,
               name='package.json', contents='{"scripts": {"start": "foo.js"}}')
    fingerprinter.GenerateConfigs(self.temp_path)
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='nodejs'),
        self.temp_path,
        'app.yaml')

    fingerprinter.GenerateConfigs(self.temp_path,
                                  ext_runtime.Params(deploy=True))

    self.AssertFileExistsWithContents(BASE_DOCKERFILE + textwrap.dedent("""\
        COPY . /app/
        # You have to specify "--unsafe-perm" with npm install
        # when running as root.  Failing to do this can cause
        # install to appear to succeed even if a preinstall
        # script fails, and may have other adverse consequences
        # as well.
        # This command will also cat the npm-debug.log file after the
        # build, if it exists.
        RUN npm install --unsafe-perm || \\
          ((if [ -f npm-debug.log ]; then \\
              cat npm-debug.log; \\
            fi) && false)
        CMD npm start
        """), self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(nodejs.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testNodeJSPackageJsonNoWrite(self):
    """Test GenerateConfigData with nodejs and package.json."""
    self.Touch(directory=self.temp_path,
               name='foo.js', contents='bogus contents')
    self.Touch(directory=self.temp_path,
               name='package.json', contents='{"scripts": {"start": "foo.js"}}')
    fingerprinter.GenerateConfigs(self.temp_path)
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='nodejs'),
        self.temp_path,
        'app.yaml')

    cfg_files = fingerprinter.GenerateConfigData(
        self.temp_path,
        ext_runtime.Params(deploy=True))
    self.assertEqual({'.dockerignore', 'Dockerfile'},
                     {cfg_file.filename for cfg_file in cfg_files})
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         BASE_DOCKERFILE + textwrap.dedent("""\
        COPY . /app/
        # You have to specify "--unsafe-perm" with npm install
        # when running as root.  Failing to do this can cause
        # install to appear to succeed even if a preinstall
        # script fails, and may have other adverse consequences
        # as well.
        # This command will also cat the npm-debug.log file after the
        # build, if it exists.
        RUN npm install --unsafe-perm || \\
          ((if [ -f npm-debug.log ]; then \\
              cat npm-debug.log; \\
            fi) && false)
        CMD npm start
        """))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         nodejs.DOCKERIGNORE)

  def testNodeJSWithEngines(self):
    self.Touch(directory=self.temp_path,
               name='foo.js', contents='bogus contents')
    self.Touch(directory=self.temp_path,
               name='package.json',
               contents='{"scripts": {"start": "foo.js"},'
               '"engines": {"node": "0.12.3"}}')
    fingerprinter.GenerateConfigs(self.temp_path,
                                  ext_runtime.Params(deploy=True))
    dockerfile_path = os.path.join(self.temp_path, 'Dockerfile')
    self.assertTrue(os.path.exists(dockerfile_path))

    # This just verifies that the install line is generated, it
    # says nothing about whether or not it works.
    with open(dockerfile_path) as f:
      contents = f.read()
    self.assertIn('\nRUN /usr/local/bin/install_node', contents)

  def testNodeJSWithEnginesNoWrite(self):
    """Test GenerateConfigData with nodejs and engines in package.json."""
    self.Touch(directory=self.temp_path,
               name='foo.js', contents='bogus contents')
    self.Touch(directory=self.temp_path,
               name='package.json',
               contents='{"scripts": {"start": "foo.js"},'
               '"engines": {"node": "0.12.3"}}')
    cfg_files = fingerprinter.GenerateConfigData(
        self.temp_path,
        ext_runtime.Params(deploy=True))
    self.assertIn('Dockerfile',
                  [f.filename for f in cfg_files])
    for cfg_file in cfg_files:
      if cfg_file.filename == 'Dockerfile':
        self.assertIn('\nRUN /usr/local/bin/install_node', cfg_file.contents)

  def testNodeJSNothingCreated(self):
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    self.Touch(directory=self.temp_path,
               name='Dockerfile', contents='fake contents')
    self.Touch(directory=self.temp_path,
               name='app.yaml', contents='fake contents')
    self.Touch(directory=self.temp_path,
               name='.dockerignore', contents='fake contents')
    self.assertFalse(fingerprinter.GenerateConfigs(self.temp_path))
    self.AssertErrContains(
        'All config files already exist, not generating anything.')

  def testNodeJSCustomRuntime(self):
    """Test GenerateConfigData with custom nodejs."""
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    fingerprinter.GenerateConfigs(self.temp_path,
                                  ext_runtime.Params(custom=True))
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='custom'),
        self.temp_path,
        'app.yaml')
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'server.js', 'app.yaml',
                      '.dockerignore', 'Dockerfile'})

  def testNodeJSCustomRuntimeNoWrite(self):
    """Test GenerateConfigData with nodejs and custom=True."""
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    cfg_files = fingerprinter.GenerateConfigData(
        self.temp_path,
        ext_runtime.Params(custom=True))
    self.AssertFileExistsWithContents(
        nodejs.NODEJS_APP_YAML.format(runtime='custom'),
        self.temp_path,
        'app.yaml')
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'server.js', 'app.yaml'})
    self.assertEqual({'.dockerignore', 'Dockerfile'},
                     {f.filename for f in cfg_files})

  def testNodeJSRuntimeField(self):
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: nodejs
        env: 2
        """))
    self.assertTrue(
        self._nodejs.Fingerprint(self.temp_path,
                                 ext_runtime.Params(appinfo=config)))

  def testNodeJSCustomRuntimeField(self):
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: custom
        env: 2
        """))
    self.assertTrue(
        self._nodejs.Fingerprint(self.temp_path,
                                 ext_runtime.Params(appinfo=config)))

  def testNodeJSInvalidRuntimeField(self):
    self.Touch(directory=self.temp_path,
               name='server.js', contents='fake contents')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: bogus
        env: 2
        """))
    self.assertIsNone(
        fingerprinter.IdentifyDirectory(self.temp_path,
                                        ext_runtime.Params(appinfo=config)))

  def testNodeJSFingerprint(self):
    """Ensure that appinfo will be generated in detect method."""
    self.Touch(directory=self.temp_path, name='foo.js',
               contents='fake contents')
    self.Touch(directory=self.temp_path, name='package.json',
               contents='{"scripts": {"start": "foo.js"}}')
    configurator = fingerprinter.IdentifyDirectory(self.temp_path)
    self.assertEqual(configurator.generated_appinfo,
                     {'runtime': 'nodejs',
                      'env': 'flex'})

  def testNodeJSFingerprintCustom(self):
    """Ensure that appinfo is correct with custom=True."""
    self.Touch(directory=self.temp_path, name='foo.js',
               contents='fake contents')
    self.Touch(directory=self.temp_path, name='package.json',
               contents='{"scripts": {"start": "foo.js"}}')
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path,
        params=ext_runtime.Params(custom=True))
    self.assertEqual(configurator.generated_appinfo,
                     {'runtime': 'custom',
                      'env': 'flex'})

  def testNodeJSFingerprintNoStartNoServer(self):
    """Ensure that fingerprinting works if no npm_start and no server.js."""
    self.Touch(directory=self.temp_path, name='foo.js',
               contents='fake contents')
    self.Touch(directory=self.temp_path, name='package.json',
               contents='{"scripts": {"not-start": "foo.js"}}')
    configurator = fingerprinter.IdentifyDirectory(self.temp_path)
    self.assertEqual(configurator, None)
    self.AssertErrContains('node.js checker: Neither "start" in the "scripts" '
                           'section of "package.json" nor the "server.js" file '
                           'were found.')

  def testNodeJSFingerprintNoStartWithServer(self):
    """Ensure that fingerprinting works if no npm_start but server.js exists."""
    self.Touch(directory=self.temp_path, name='foo.js',
               contents='fake contents')
    self.Touch(directory=self.temp_path, name='package.json',
               contents='{"scripts": {"start": "foo.js"}}')
    configurator = fingerprinter.IdentifyDirectory(self.temp_path)
    self.assertEqual(configurator.generated_appinfo,
                     {'runtime': 'nodejs',
                      'env': 'flex'})

  def testUnmatchedDirectory(self):
    self.assertIsNone(fingerprinter.IdentifyDirectory(self.temp_path))

  def AssertNoFile(self, filename):
    """Asserts that the relative path 'filename' does not exist."""
    self.assertFalse(os.path.exists(os.path.join(self.temp_path, filename)))

  def GenerateJava(self, deploy=False, config=None, custom=False):
    return fingerprinter.GenerateConfigs(self.temp_path,
                                         ext_runtime.Params(appinfo=config,
                                                            deploy=deploy,
                                                            custom=custom))

  def GenerateJavaConfigData(self, deploy=False, config=None, custom=False):
    return fingerprinter.GenerateConfigData(self.temp_path,
                                            ext_runtime.Params(
                                                appinfo=config,
                                                deploy=deploy,
                                                custom=custom))

  def testJavaAllDefaults(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    self.GenerateJava()

    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='java'),
        self.temp_path,
        'app.yaml')
    self.AssertNoFile('Dockerfile')
    self.AssertNoFile('.dockerignore')

    self.GenerateJava(deploy=True)

    self.AssertFileExistsWithContents(java.DOCKERIGNORE,
                                      self.temp_path, '.dockerignore')
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')

  def testJavaAllDefaultsNoWrite(self):
    """Test GenerateConfigData with java and existing app.yaml.

    After running GenerateConfigs to generate app.yaml, GenerateConfigData()
    should correctly return java dockerfiles.
    """
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    self.GenerateJava()

    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='java'),
        self.temp_path,
        'app.yaml')
    self.AssertNoFile('Dockerfile')
    self.AssertNoFile('.dockerignore')

    cfg_files = self.GenerateJavaConfigData(deploy=True)
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))

  def testJavaCustom(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    self.GenerateJava(deploy=False, custom=True)

    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='custom'),
        self.temp_path,
        'app.yaml')

    self.AssertFileExistsWithContents(java.DOCKERIGNORE,
                                      self.temp_path, '.dockerignore')
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')

  def testJavaCustomNoWrite(self):
    """Test GenerateConfigData with java and custom runtime."""
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    cfg_files = self.GenerateJavaConfigData(deploy=False, custom=True)

    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='custom'),
        self.temp_path,
        'app.yaml')

    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))

  def testJavaFilesNoJava(self):
    self.Touch(directory=self.temp_path, name='foo.nojava', contents='')
    self.assertIsNone(fingerprinter.IdentifyDirectory(self.temp_path))

  def testJavaFilesWithWar(self):
    self.Touch(directory=self.temp_path, name='foo.war', contents='')

    self.GenerateJava()
    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='java'),
        self.temp_path,
        'app.yaml')
    self.AssertNoFile('Dockerfile')
    self.AssertNoFile('.dockerignore')

    self.GenerateJava(deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JETTY_PREAMBLE,
        java.DOCKERFILE_INSTALL_WAR.format('foo.war'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWarNoWrite(self):
    """Test GenerateConfigData with java .war."""
    self.Touch(directory=self.temp_path, name='foo.war', contents='')

    self.GenerateJava()

    cfg_files = self.GenerateJavaConfigData(deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JETTY_PREAMBLE,
        java.DOCKERFILE_INSTALL_WAR.format('foo.war'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithJar(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    self.GenerateJava()
    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='java'),
        self.temp_path,
        'app.yaml')
    self.AssertNoFile('Dockerfile')
    self.AssertNoFile('.dockerignore')

    self.GenerateJava(deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithJarNoWrite(self):
    """Test GenerateConfigData with .jar."""
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    self.GenerateJava()

    cfg_files = self.GenerateJavaConfigData(deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithWebInf(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')

    self.GenerateJava()
    self.AssertFileExistsWithContents(
        java.JAVA_APP_YAML.format(runtime='java'),
        self.temp_path,
        'app.yaml')
    self.AssertNoFile('Dockerfile')
    self.AssertNoFile('.dockerignore')

    self.GenerateJava(deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWebInfNoWrite(self):
    """Test GenerateConfigData with java and WEB-INF."""
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')

    self.GenerateJava()

    cfg_files = self.GenerateJavaConfigData(deploy=True)

    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithTooManyArtifacts(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')

    with self.assertRaises(fingerprinter.UnidentifiedDirectoryError):
      fingerprinter.GenerateConfigs(self.temp_path)
    self.assertIn('Too many java artifacts to deploy', self.GetErr())

  def testJavaFilesWithWarAndYamlMvm(self):
    self.Touch(directory=self.temp_path, name='foo.war', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: true
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JETTY9_PREAMBLE,
        java.DOCKERFILE_INSTALL_WAR.format('foo.war'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWarAndYamlMvmNoWrite(self):
    """Test GenerateConfigData with .war and given appinfo."""
    self.Touch(directory=self.temp_path, name='foo.war', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: true
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    cfg_files = self.GenerateJavaConfigData(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JETTY9_PREAMBLE,
        java.DOCKERFILE_INSTALL_WAR.format('foo.war'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithWarAndYamlFlex(self):
    self.Touch(directory=self.temp_path, name='foo.war', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: flex
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JETTY_PREAMBLE,
        java.DOCKERFILE_INSTALL_WAR.format('foo.war'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithJarAndYamlMvm(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: true
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA8_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithJarAndYamlFlex(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: flex
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_JAVA_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('foo.jar'),
        java.DOCKERFILE_JAVA8_JAR_CMD.format('foo.jar'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWebInfAndYamlAndEnv2(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: 2
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWebInfAndYamlAndEnv2NoWrite(self):
    """Test GenerateConfigData with .war and appinfo with env = 2."""
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: 2
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    cfg_files = self.GenerateJavaConfigData(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithWebInfAndYamlAndNoEnv2(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: True
        runtime_config:
          server: jetty9
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_LEGACY_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWebInfAndYamlAndNoEnv2NoWrite(self):
    """Test GenerateConfigData with WEB-INF and appinfo with no env = 2."""
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: True
        runtime_config:
          server: jetty9
        """))
    cfg_files = self.GenerateJavaConfigData(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_LEGACY_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithWebInfAndYamlAndOpenJdk8NoEnv2(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: True
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJavaFilesWithWebInfAndYamlAndOpenJdk8NoEnv2NoWrite(self):
    """Test GenerateConfigData with WEB-INF and appinfo with jdk: openjdk8."""
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        vm: True
        runtime_config:
          jdk: openjdk8
          server: jetty9
        """))
    cfg_files = self.GenerateJavaConfigData(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_COMPAT_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def testJavaFilesWithConfigError(self):
    self.Touch(directory=self.temp_path, name='foo.war', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: 2
        runtime_config:
          jdk: openjdk9
        """))
    with self.assertRaises(fingerprinter.UnidentifiedDirectoryError):
      fingerprinter.GenerateConfigs(
          self.temp_path, ext_runtime.Params(appinfo=config, deploy=True))
    self.assertIn('Unknown JDK : openjdk9.', self.GetErr())

  def testJavaCustomRuntimeField(self):
    self.Touch(directory=self.temp_path, name='foo.jar', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java
        env: 2
        """))
    self.assertTrue(fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(appinfo=config)))

  def testJava7Runtime(self):
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java7
        vm: true
        """))
    self.GenerateJava(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_LEGACY_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertFileExistsWithContents(''.join(dockerfile_contents),
                                      self.temp_path, 'Dockerfile')
    self.AssertFileExistsWithContents(java.DOCKERIGNORE, self.temp_path,
                                      '.dockerignore')

  def testJava7RuntimeNoWrite(self):
    """Test GenerateConfigData with java 7 runtime."""
    self.Touch(directory=self.temp_path, name='WEB-INF', contents='')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: java7
        vm: true
        """))
    cfg_files = self.GenerateJavaConfigData(config=config, deploy=True)
    dockerfile_contents = [
        java.DOCKERFILE_LEGACY_PREAMBLE,
        java.DOCKERFILE_INSTALL_APP.format('.'),
    ]
    self.AssertGenfileExistsWithContents(cfg_files, 'Dockerfile',
                                         ''.join(dockerfile_contents))
    self.AssertGenfileExistsWithContents(cfg_files, '.dockerignore',
                                         java.DOCKERIGNORE)

  def GeneratePython(self, config=None, custom=False, deploy=False):
    """Run generate configs on a python directory.

    Args:
      config: (apphosting.api.appinfo.AppInfoExternal or None)
      custom: (bool) True to generate a custom runtime.
      deploy: (bool) True to do deployment-phase generation.

    Returns:
      (bool) True if configs written
    """
    with mock.patch.object(console_io, 'CanPrompt', lambda: True):
      with mock.patch.object(console_io, 'PromptResponse',
                             lambda _: 'my_entrypoint'):
        return fingerprinter.GenerateConfigs(
            self.temp_path,
            ext_runtime.Params(appinfo=config, custom=custom,
                               deploy=deploy))

  def GeneratePythonConfigData(self, config=None, custom=False, deploy=False):
    """Run GenerateConfigData on a python directory.

    Args:
      config: (apphosting.api.appinfo.AppInfoExternal or None)
      custom: (bool) True to generate a custom runtime.
      deploy: (bool) True to do deployment-phase generation.

    Returns:
      ([ext_runtime.GeneratedFile]) a list of generated files (None if files
      were written to disk)
    """
    with mock.patch.object(console_io, 'CanPrompt', lambda: True):
      with mock.patch.object(console_io, 'PromptResponse',
                             lambda _: 'my_entrypoint'):
        return fingerprinter.GenerateConfigData(
            self.temp_path,
            ext_runtime.Params(appinfo=config, custom=custom,
                               deploy=deploy))

  def GetPythonDockerfileContents(self, config=None, custom=False,
                                  deploy=False):
    """Run generate configs on a python directory.

    Args:
      config: (apphosting.api.appinfo.AppInfoExternal or None)
      custom: (bool) True to generate a custom runtime.
      deploy: (bool) True to do deployment-phase generation.

    Returns:
      (str): Generated dockerfile contents
    """
    self.GeneratePython(config=config, custom=custom, deploy=deploy)
    dockerfile = os.path.join(self.temp_path, 'Dockerfile')
    if os.path.exists(dockerfile):
      with open(dockerfile) as f:
        contents = f.read()
    else:
      contents = None
    return contents

  def testPython(self):
    self.Touch(directory=self.temp_path, name='requirements.txt',
               contents='requirements')
    contents = self.GetPythonDockerfileContents(deploy=True)
    self.assertMultiLineEqual(contents,
                              python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_REQUIREMENTS_TXT +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD my_entrypoint\n')

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'app.yaml', 'requirements.txt',
                      'Dockerfile', '.dockerignore'})

  def testPythonNoWrite(self):
    """Test GenerateConfigData with python and requirements.txt."""
    self.Touch(directory=self.temp_path, name='requirements.txt',
               contents='requirements')
    cfg_files = self.GeneratePythonConfigData(deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_REQUIREMENTS_TXT +
        python.DOCKERFILE_INSTALL_APP +
        'CMD my_entrypoint\n')

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'app.yaml', 'requirements.txt'})
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonNoRequirementsTxt(self):
    self.Touch(directory=self.temp_path, name='foo.py',
               contents='# python code')
    contents = self.GetPythonDockerfileContents(custom=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD my_entrypoint\n',
                              contents)

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'foo.py', 'app.yaml', 'Dockerfile', '.dockerignore'})

  def testPythonNoRequirementsTxtNoWrite(self):
    """Test GenerateConfigData with single python file, no requirements.txt."""
    self.Touch(directory=self.temp_path, name='foo.py',
               contents='# python code')
    cfg_files = self.GeneratePythonConfigData(custom=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD my_entrypoint\n')

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'foo.py', 'app.yaml'})
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonWithAppYaml(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD exec run_me_some_python!\n',
                              contents)

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithExecFormatEntrypoint(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: "['python', 'run_me_some_python.py']"
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              "CMD ['python', 'run_me_some_python.py']\n",
                              contents)

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithShellFormatExecPrependedEntrypoint(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: exec run_me_some_python!
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD exec run_me_some_python!\n',
                              contents)

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithAppYamlNoWrite(self):
    """Test GenerateConfigData with python and appinfo given."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        handlers:
        - url: .*
          script: request
        """))
    cfg_files = self.GeneratePythonConfigData(config, deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD exec run_me_some_python!\n')

    self.assertEqual(os.listdir(self.temp_path),
                     ['test.py'])
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonAppYamlNoEntrypoint(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD my_entrypoint\n',
                              contents)

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonAppYamlNoEntrypointNoWrite(self):
    """Test GenerateConfigData with python, appinfo given and no entrypoint."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        handlers:
        - url: .*
          script: request
        """))
    cfg_files = self.GeneratePythonConfigData(config, deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD my_entrypoint\n')

    self.assertEqual(os.listdir(self.temp_path),
                     ['test.py'])
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonWithRuntimeConfigButNoPythonVersion(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          some_other_key: true
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD exec run_me_some_python!\n',
                              contents)
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithRuntimeConfigButNoPythonVersionNoWrite(self):
    """Test GenerateConfigData with python, no python version in appinfo."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          some_other_key: true
        handlers:
        - url: .*
          script: request
        """))
    cfg_files = self.GeneratePythonConfigData(config, deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD exec run_me_some_python!\n')
    self.assertEqual(os.listdir(self.temp_path), ['test.py'])
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonWithExplicitPython2(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          python_version: 2
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD exec run_me_some_python!\n',
                              contents)
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithExplicitPython2NoWrite(self):
    """Test GenerateConfigData with python version 2 in appinfo."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          python_version: 2
        handlers:
        - url: .*
          script: request
        """))
    cfg_files = self.GeneratePythonConfigData(config, deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
            python_version='') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD exec run_me_some_python!\n')
    self.assertEqual(os.listdir(self.temp_path), ['test.py'])
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonWithExplicitPython3(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          python_version: 3
        handlers:
        - url: .*
          script: request
        """))
    contents = self.GetPythonDockerfileContents(config, deploy=True)
    self.assertMultiLineEqual(python.DOCKERFILE_PREAMBLE +
                              python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                                  python_version='3.6') +
                              python.DOCKERFILE_INSTALL_APP +
                              'CMD exec run_me_some_python!\n',
                              contents)
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'.dockerignore', 'Dockerfile', 'test.py'})

  def testPythonWithExplicitPython3NoWrite(self):
    """Test GenerateConfigData with python version 3 in appinfo."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          python_version: 3
        handlers:
        - url: .*
          script: request
        """))
    cfg_files = self.GeneratePythonConfigData(config, deploy=True)
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python.DOCKERFILE_PREAMBLE +
        python.DOCKERFILE_VIRTUALENV_TEMPLATE.format(python_version='3.6') +
        python.DOCKERFILE_INSTALL_APP +
        'CMD exec run_me_some_python!\n')
    self.assertEqual(os.listdir(self.temp_path), ['test.py'])
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonWithInvalidVersion(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python
        env: 2
        entrypoint: run_me_some_python!
        runtime_config:
          python_version: invalid_version
        handlers:
        - url: .*
          script: request
        """))
    with self.assertRaises(fingerprinter.UnidentifiedDirectoryError):
      self.GeneratePython(config, deploy=True)

  def testPythonCustomRuntime(self):
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    self.GeneratePython(custom=True)
    with open(os.path.join(self.temp_path, 'app.yaml')) as f:
      app_yaml_contents = f.read()
    self.assertMultiLineEqual(
        app_yaml_contents,
        textwrap.dedent("""\
            entrypoint: my_entrypoint
            env: flex
            runtime: custom
            """))
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'test.py', 'app.yaml', 'Dockerfile', '.dockerignore'})

  def testPythonCustomRuntimeNoWrite(self):
    """Test GenerateConfigData with python and custom=True."""
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    cfg_files = self.GeneratePythonConfigData(custom=True)
    with open(os.path.join(self.temp_path, 'app.yaml')) as f:
      app_yaml_contents = f.read()
    self.assertMultiLineEqual(
        app_yaml_contents,
        textwrap.dedent("""\
            entrypoint: my_entrypoint
            env: flex
            runtime: custom
            """))
    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'test.py', 'app.yaml'})
    self.assertEqual({f.filename for f in cfg_files},
                     {'Dockerfile', '.dockerignore'})

  def testPythonCustomRuntimeField(self):
    # verify that a runtime field of "custom" works.
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: custom
        vm: true
        entrypoint: my_entrypoint
        """))
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path,
        ext_runtime.Params(appinfo=config))

    self.assertEqual(configurator.runtime.name, 'python')

  def testPythonInvalidRuntimeField(self):
    # verify that a runtime field of "custom" works.
    self.Touch(directory=self.temp_path, name='test.py',
               contents='test file')
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: bogus
        vm: true
        entrypoint: my_entrypoint
        """))

    # This doesn't really need to be None, it just needs to not be python.
    # But it's easier to check for None.
    self.assertIsNone(
        fingerprinter.IdentifyDirectory(self.temp_path,
                                        ext_runtime.Params(appinfo=config)))

  def testPythonNonInteractive(self):
    self.Touch(directory=self.temp_path, name='test.py', contents='blah')
    with contextlib.nested(
        mock.patch.object(console_io, 'CanPrompt', lambda: False),
        mock.patch.object(ext_runtime, '_NO_DEFAULT_ERROR',
                          'xx123unlikely {0}')):
      fingerprinter.IdentifyDirectory(self.temp_path)
    self.AssertLogContains('xx123unlikely')

  def testPythonCompat(self):
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python-compat
        env: flex
        entrypoint: my_entrypoint
        """))
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(appinfo=config, deploy=True))
    self.assertIsInstance(configurator, python_compat.PythonConfigurator)

    # Verify that we get a python-compat dockerfile.
    configurator.GenerateConfigs()
    self.AssertFileExistsWithContents(
        python_compat.COMPAT_DOCKERFILE_PREAMBLE +
        python_compat.DOCKERFILE_INSTALL_APP +
        python_compat.DOCKERFILE_INSTALL_REQUIREMENTS_TXT,
        self.temp_path, 'Dockerfile')

  def testPythonCompatNoWrite(self):
    """Test GenerateConfigData with python-compat runtime."""
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python-compat
        env: flex
        entrypoint: my_entrypoint
        """))
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(appinfo=config, deploy=True))
    self.assertIsInstance(configurator, python_compat.PythonConfigurator)

    # Verify that we get a python-compat dockerfile.
    cfg_files = configurator.GenerateConfigData()
    self.AssertGenfileExistsWithContents(
        cfg_files, 'Dockerfile',
        python_compat.COMPAT_DOCKERFILE_PREAMBLE +
        python_compat.DOCKERFILE_INSTALL_APP +
        python_compat.DOCKERFILE_INSTALL_REQUIREMENTS_TXT)

  def testPythonCompatAppYaml(self):
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(runtime='python27'))
    configurator.GenerateConfigs()

    self.AssertErrContains(python_compat.APP_YAML_WARNING)
    self.AssertFileExistsWithContents(
        python_compat.PYTHON_APP_YAML.format(runtime='python27'),
        self.temp_path, 'app.yaml')

  def testPythonCompatAppYamlNoWrite(self):
    """Test GenerateConfigData app.yaml and warning for python-compat."""
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(runtime='python27'))
    configurator.GenerateConfigData()

    self.AssertErrContains(python_compat.APP_YAML_WARNING)
    self.AssertFileExistsWithContents(
        python_compat.PYTHON_APP_YAML.format(runtime='python27'),
        self.temp_path, 'app.yaml')

  def testPythonCompatConfigFilesExist(self):
    config = appinfo.LoadSingleAppInfo(textwrap.dedent("""\
        runtime: python-compat
        vm: true
        entrypoint: my_entrypoint
        """))

    self.Touch(directory=self.temp_path, name='Dockerfile',
               contents='test file')
    self.Touch(directory=self.temp_path, name='.dockerignore',
               contents='test file')
    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params(appinfo=config, deploy=True))

    # Verify that we don't generate another file.
    self.assertIsInstance(configurator, python_compat.PythonConfigurator)
    with mock.patch('googlecloudsdk.core.log.info') as p:
      configurator.GenerateConfigs()
      p.assert_called_with(
          'All config files already exist, not generating anything.')

  def testExternalRuntime(self):
    with mock.patch('googlecloudsdk.api_lib.app.runtimes.fingerprinter'
                    '.RUNTIMES',
                    [ext_runtime.ExternalizedRuntime.Load(
                        sdk_test_base.SdkBase.Resource(
                            'tests', 'unit', 'api_lib', 'app',
                            'testdata', 'runtime_def'),
                        ext_runtime_adapter.GCloudExecutionEnvironment())]):
      fingerprinter.GenerateConfigs(self.temp_path)

    self.AssertFileExistsWithContents('this is foo', self.temp_path, 'foo')
    self.AssertFileExistsWithContents('this is bar', self.temp_path, 'bar')

    self.assertEqual(set(os.listdir(self.temp_path)),
                     {'foo', 'bar', 'exists', 'info'})

  def testExternalRuntimeNoWrite(self):
    """Test GenerateConfigData with test runtime."""
    with mock.patch('googlecloudsdk.api_lib.app.runtimes.fingerprinter'
                    '.RUNTIMES',
                    [ext_runtime.ExternalizedRuntime.Load(
                        sdk_test_base.SdkBase.Resource(
                            'tests', 'unit', 'api_lib', 'app',
                            'testdata', 'runtime_def'),
                        ext_runtime_adapter.GCloudExecutionEnvironment())]):
      cfg_files = fingerprinter.GenerateConfigData(self.temp_path)

    self.AssertGenfileExistsWithContents(cfg_files, 'foo', 'this is foo')
    self.AssertGenfileExistsWithContents(cfg_files, 'bar', 'this is bar')

    self.assertEqual(os.listdir(self.temp_path),
                     [])
    self.assertEqual({f.filename for f in cfg_files},
                     {'foo', 'bar', 'exists', 'info'})

  def testExternalRuntimeRaises(self):
    """Test error handling if InvalidRuntimeDefinition raised."""
    with mock.patch(
        'googlecloudsdk.api_lib.app.runtimes.fingerprinter.RUNTIMES',
        [ext_runtime.ExternalizedRuntime.Load(
            sdk_test_base.SdkBase.Resource(
                'tests', 'unit', 'api_lib', 'app',
                'testdata', 'runtime_def'),
            ext_runtime_adapter.GCloudExecutionEnvironment())]) as runtime_def:
      with self.StartObjectPatch(
          runtime_def[0], 'GenerateConfigData',
          side_effect=ext_runtime.InvalidRuntimeDefinition('message')):
        with self.assertRaisesRegex(fingerprinter.ExtRuntimeError, r'message'):
          fingerprinter.GenerateConfigData(self.temp_path)

  # These tests verify that the correct runtime is selected when there are
  # multiple possibilities.  They are the only tests that will belong in this
  # file once all runtimes are externalized.

  def testCustomFirst(self):
    # Whenever there's a Dockerfile, we should match "custom".
    self.Touch(directory=self.temp_path, name='Dockerfile', contents='blech')
    self.Touch(directory=self.temp_path, name='server.js', contents='blech')
    self.Touch(directory=self.temp_path, name='test.py', contents='blah')
    self.Touch(directory=self.temp_path, name='Gemfile', contents='blart')
    self.Touch(directory=self.temp_path, name='main.go',
               contents='package main\nfunc main\n')
    self.Touch(directory=self.temp_path, name='javaapp.war', contents='blava')

    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params())
    self.assertEqual(configurator.runtime.name, 'custom')

  def testPHPRuntimeDetection(self):
    self.Touch(directory=self.temp_path, name='index.php', contents='foo')

    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params())
    self.assertEqual(configurator.runtime.name, 'php')

  def testPHPRuntimeWithPackageJSON(self):
    # For examples of PHP applications that also have a package.json check out:
    #   *  https://github.com/laravel/laravel
    #   *  https://github.com/sjlu/CodeIgniter-Sunrise

    self.Touch(directory=self.temp_path, name='index.php', contents='foo')
    self.Touch(directory=self.temp_path, name='package.json',
               contents='{"scripts": {"start": ""}}}')

    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params())
    self.assertEqual(configurator.runtime.name, 'php')

  def testRubyRuntimeDetection(self):
    self.Touch(directory=self.temp_path, name='index.rb', contents='ruby')
    self.Touch(directory=self.temp_path, name='config.ru', contents='run App')
    self.Touch(directory=self.temp_path, name='Gemfile', contents='rubygems')

    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params())
    self.assertEqual(configurator.runtime.name, 'ruby')

  def testGoRuntimeDetection(self):
    self.Touch(directory=self.temp_path, name='main.go',
               contents='package main\nfunc main() {}')

    configurator = fingerprinter.IdentifyDirectory(
        self.temp_path, ext_runtime.Params())
    self.assertEqual(configurator.runtime.name, 'go')


if __name__ == '__main__':
  test_case.main()
