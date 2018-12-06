# -*- coding: utf-8 -*- #
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
"""Small test to verify that the gen-config command works as advertised."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import util
from googlecloudsdk.third_party.appengine.api import appinfo
import mock


DOCKER_IDENTIFIER_GO = 'FROM gcr.io/google_appengine/golang'
DOCKER_IDENTIFIER_NODEJS = 'FROM gcr.io/google_appengine/nodejs'
ORIGINAL_DOCKERFILE_CONTENTS = 'Original dockerfile contents'
ORIGINAL_APP_YAML_CONTENTS = 'env: flex\napi_version: 1\n'

GO_SOURCE = textwrap.dedent("""\
    package main
    func main() {}
    """)

APP_YAML_NODEJS = textwrap.dedent("""\
    env: flex
    api_version: 1
    runtime: nodejs
    """)

# Legacy Managed VM:s app.yaml
APP_YAML_NODEJS_VM_TRUE = textwrap.dedent("""\
    api_version: 1
    runtime: nodejs
    vm: true
    """)

# Updated runtime field will unfortunately not (yet) remove api_version or other
# runtime specific fields
APP_YAML_NODEJS_TO_CUSTOM = textwrap.dedent("""\
    env: flex
    api_version: 1
    runtime: custom
    """)

APP_YAML_GO = textwrap.dedent("""\
    env: flex
    api_version: go1
    runtime: go
    """)

APP_YAML_GO_VM_FALSE = textwrap.dedent("""\
    api_version: go1
    runtime: go
    handlers:
    - url: /
      script: test
    """)


@test_case.Filters.SkipOnPy3('Deprecated command; no py3 support', 'b/76013940')
@test_case.Filters.DoNotRunIf(not properties.VALUES.app.runtime_root.Get(),
                              'No app runtime root is configured')
class GenConfigTest(cli_test_base.CliTestBase, util.WithAppData,
                    sdk_test_base.WithTempCWD):
  """Tests for gcloud [beta] app gen-config.

  We attempt at testing standard combinations of the --runtime, --custom and
  --config flags. This is basically end-to-end tests, since we use actual
  fingerprinting with actual runtimes. Go and nodejs have been chosen as
  runtimes because they do not require additional configuration. Go has
  precedence during detection, which is utilized for testing purposes.

  TODO(b/36049790): Tests for runtimes that require (interactive) custom fields.
  TODO(b/36054659): Tests for externalized (user provided) runtimes.
  TODO(b/36049935): Potentially decouple tests from actual runtimes because they
    might change in the future.
  """

  def SetUp(self):
    properties.VALUES.core.project.Set('myproject')
    self.temp_path = os.getcwd()  # Symlinks might put us somewhere else
    self.track = calliope_base.ReleaseTrack.BETA

  def _WriteNodeFiles(self):
    self.WriteJSON('package.json', {'scripts': {'start': 'node foo.js'}})
    self.WriteFile('foo.js', 'console.log("hello")')

  def _WriteGoFiles(self):
    self.WriteFile('main.go', GO_SOURCE)

  def _AssertAppYamlGenerated(self, runtime=None):
    """Check that app.yaml was generated verbosely with an optional runtime.

    Args:
      runtime: str, The effective runtime field that should be in app.yaml
    """
    self.AssertErrContains('Writing [app.yaml] to '
                           '[{0}].'.format(self.temp_path))
    self.AssertFileExists('app.yaml')
    if runtime:
      with open('app.yaml') as appyaml:
        config = appinfo.LoadSingleAppInfo(appyaml)
        assert config.IsVm()
        assert config.GetEffectiveRuntime() == runtime

  def _AssertDockerFilesGenerated(self, docker_identifier=None,
                                  check_update_msg=False):
    """Check that docker files were generated with an optional identifier.

    Args:
      docker_identifier: str, A substring to look for in Dockerfile
      check_update_msg: bool, Check that messages about updating the runtime
          field has been printed.
    """
    self.AssertErrContains('Writing [Dockerfile] to '
                           '[{0}].'.format(self.temp_path))
    self.AssertErrContains('Writing [.dockerignore] to '
                           '[{0}].'.format(self.temp_path))
    self.AssertFileExists('Dockerfile')
    self.AssertFileExists('.dockerignore')
    if docker_identifier:
      self.AssertFileContains(docker_identifier, 'Dockerfile')
    if check_update_msg:
      appyaml_path = os.path.join(self.temp_path, 'app.yaml')
      self.AssertErrContains("You've generated a Dockerfile that may be "
                             'customized for your application.  To use this '
                             'Dockerfile, the runtime field in [{0}] must be '
                             'set to custom.'
                             .format(appyaml_path.replace('\\', '\\\\')))
      self.AssertErrContains('Please update [{0}] manually by changing the '
                             'runtime field to custom.'.format(appyaml_path))

  def testDefault(self):
    """Generate an app.yaml from the current nodejs directory.

    Default test case, same directory, only one runtime matches. The resulting
    app.yaml should have runtime: nodejs. Also, make sure no Docker files are
    generated.
    """
    self._WriteNodeFiles()
    self.Run('app gen-config')
    self._AssertAppYamlGenerated(runtime='nodejs')
    self.AssertFileNotExists('Dockerfile')
    self.AssertFileNotExists('.dockerignore')

  def testMultipleRuntimes(self):
    """Generate app.yaml from two-runtime dir and respect implicit precedence.

    Two runtimes should be identified, and the one with highest precedence
    should be chosen. The order is hard coded in fingerprinter.py.
    """
    self._WriteNodeFiles()
    self._WriteGoFiles()
    self.Run('app gen-config')
    self._AssertAppYamlGenerated(runtime='go')

  def testMultipleRuntimesEnforce(self):
    """Make sure --runtime is respected when multiple runtimes detected.

    Generate app.yaml from two-runtime dir but override implicit precedence.
    """
    self._WriteNodeFiles()
    self._WriteGoFiles()
    # go has precedence normally, so here we enforce nodejs
    self.Run('app gen-config --runtime=nodejs')
    self._AssertAppYamlGenerated(runtime='nodejs')

  def testCustom(self):
    """Generate app.yaml and docker files in one go by using --custom."""
    self._WriteNodeFiles()
    self.Run('app gen-config --custom')
    self._AssertAppYamlGenerated(runtime='custom')
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS)

  def testCustomWithConfig(self):
    """Provide manual app.yaml, then generate docker files with --custom."""
    self._WriteNodeFiles()
    self.WriteFile('app.yaml', APP_YAML_NODEJS)
    self.Run('app gen-config --custom')
    # TODO(b/25833320): Assert that runtime field is changed instead.
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS,
                                     check_update_msg=True)

  def testCustomWithConfig_VMTrue(self):
    """Same as testCustomWithConfig but make sure vm:true works too."""
    self._WriteNodeFiles()
    self.WriteFile('app.yaml', APP_YAML_NODEJS_VM_TRUE)
    self.Run('app gen-config --custom')
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS,
                                     check_update_msg=True)

  def testDefaultThenCustom(self):
    """First generate app.yaml, then generate docker files using --custom."""
    self._WriteNodeFiles()
    self.Run('app gen-config')
    self._AssertAppYamlGenerated(runtime='nodejs')
    self.Run('app gen-config --custom')
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS)

  def testCustomEnforceRuntimeByFlag(self):
    """Make sure --runtime is respected in conjunction with --custom."""
    self._WriteNodeFiles()
    self._WriteGoFiles()
    # go has precedence normally, so here we enforce nodejs
    self.Run('app gen-config --runtime=nodejs --custom')
    self._AssertAppYamlGenerated(runtime='custom')
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS)

  def testCustomEnforceRuntimeByConfig(self):
    """Make sure existing runtime field in app.yaml is respected with --custom.

    Directory contains two runtimes. Pre-populate app.yaml with low precedence
    runtime. Run gen-config --custom without runtime specifier (to lure it into
    picking the higher precedence runtime), and check that it in fact respected
    the runtime from the app.yaml. This is a design decision.
    """
    self._WriteNodeFiles()
    self._WriteGoFiles()
    # go has precedence normally, but here we use nodejs
    self.WriteFile('app.yaml', APP_YAML_NODEJS)
    self.Run('app gen-config --custom')
    self._AssertDockerFilesGenerated(docker_identifier=DOCKER_IDENTIFIER_NODEJS,
                                     check_update_msg=True)

  def testUnidentifiedDirectory(self):
    """Make sure that an empty directory does not identify as a runtime."""
    with self.assertRaises(fingerprinter.UnidentifiedDirectoryError):
      self.Run('app gen-config')
    self.AssertErrContains('Unrecognized directory type')
    self.AssertFileNotExists('app.yaml')

  def testExistingConfig(self):
    """Make sure that we fail if there is already an app.yaml and no --custom.
    """
    self.WriteFile('app.yaml', APP_YAML_NODEJS)
    with self.assertRaises(fingerprinter.ConflictingConfigError):
      self.Run('app gen-config')
    self.AssertErrContains('Configuration file already exists.')
    self.AssertFileExistsWithContents(APP_YAML_NODEJS, 'app.yaml')

  def testCustomWithVmFalse(self):
    """Make sure that we cannot generate docker files if vm: false."""
    self.WriteFile('app.yaml', APP_YAML_GO_VM_FALSE)
    with self.assertRaises(fingerprinter.ConflictingConfigError):
      self.Run('app gen-config --custom')
    self.AssertErrContains('gen-config is only supported for App Engine '
                           'Flexible.')
    self.AssertFileNotExists('Dockerfile')
    self.AssertFileNotExists('.dockerignore')

  def testConfigFlag(self):
    """Make sure --config, for alt location of existing app.yaml, is respected.

    TODO(b/36057404): Needs better specification and more testing. What should
    happen if there is an app.yaml in the directory too? Is it only usable in
    conjunction with --custom? What if we want to change app.yaml (say add
    runtime: custom), should we do try to edit this file then?
    """
    config_dir = self.CreateTempDir()
    config_path = os.path.join(config_dir, 'appyaml.conf')
    self.WriteFile(config_path, APP_YAML_NODEJS)
    self._WriteNodeFiles()
    self.Run('app gen-config --custom --config="%s"' % config_path)
    self._AssertDockerFilesGenerated(DOCKER_IDENTIFIER_NODEJS)

  def testRuntimeAltered(self):
    """Check that the app.yaml runtime field is altered properly."""
    self._WriteNodeFiles()
    self.WriteFile('app.yaml', APP_YAML_NODEJS)
    with mock.patch.object(console_io, 'CanPrompt', lambda: True):
      with mock.patch.object(console_io, 'PromptContinue',
                             lambda **kwargs: True):
        self.Run('app gen-config --custom')
    self.AssertFileExistsWithContents(APP_YAML_NODEJS_TO_CUSTOM, 'app.yaml')

  def testRuntimeAlteredException(self):
    """Check that the right error is thrown when app.yaml is read only."""
    self._WriteNodeFiles()
    self.WriteFile('app.yaml', APP_YAML_NODEJS)
    os.chmod('app.yaml', 0o444)
    with mock.patch.object(console_io, 'CanPrompt', lambda: True):
      with mock.patch.object(console_io, 'PromptContinue',
                             lambda **kwargs: True):
        with self.assertRaises(fingerprinter.AlterConfigFileError):
          self.Run('app gen-config --custom')
    self.AssertErrContains('Could not alter app.yaml due to an internal error')
    self.AssertErrContains('Please update app.yaml manually.')
    self.AssertFileExistsWithContents(APP_YAML_NODEJS, 'app.yaml')
    os.chmod('app.yaml', 0o666)


if __name__ == '__main__':
  test_case.main()
