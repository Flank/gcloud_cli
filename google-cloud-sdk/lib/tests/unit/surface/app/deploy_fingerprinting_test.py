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
"""Small test to verify that deploy behaves as expected."""

import os
import textwrap

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import cloud_build
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.api_lib.cloudbuild import build
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.app import deploy_util
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import util
import mock

BASE_DOCKERFILE = textwrap.dedent("""\
    # Dockerfile extending the generic Node image with application files for a
    # single application.
    FROM gcr.io/google_appengine/nodejs
    """)
NODEJS_APP_YAML = textwrap.dedent("""\
    runtime: nodejs
    env: flex
    api_version: 1

    handlers:
    - url: /static
      static_dir: static
    """)
NODEJS_APP_YAML_VM_TRUE = textwrap.dedent("""\
    vm: true
    runtime: nodejs
    """)
CUSTOM_APP_YAML = textwrap.dedent("""\
    env: flex
    api_version: 1
    """)
DOCKERFILE_CONTENTS = BASE_DOCKERFILE + textwrap.dedent("""\
    COPY package.json /app/
    RUN npm install
    COPY . /app/
    CMD npm start
    """)

JAVA_V1_APP_YAML = textwrap.dedent("""\
    runtime: java7
    api_version: 1

    handlers:
    - url: /static
      static_dir: static
    """)


class FingerprintingTestBase(cli_test_base.CliTestBase, util.WithAppData,
                             sdk_test_base.WithFakeAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set('myproject')
    # don't actually try to do anything.
    self.StartObjectPatch(appengine_client, 'AppengineClient')
    self.StartObjectPatch(output_helpers, 'DisplayProposedDeployment')
    self.StartObjectPatch(appengine_api_client, 'AppengineApiClient')
    self.StartObjectPatch(cloud_build, 'UploadSource')
    self.StartObjectPatch(enable_api, 'EnableServiceIfDisabled')
    self.StartObjectPatch(build.CloudBuildClient, 'ExecuteCloudBuild')
    self.StartObjectPatch(deploy_app_command_util, 'CopyFilesToCodeBucket')
    self.StartObjectPatch(deploy_util, '_RaiseIfStopped')
    self.path = None
    self.params = None
    self.track = calliope_base.ReleaseTrack.BETA
    self.addCleanup(properties.VALUES.app.use_runtime_builders.Set,
                    properties.VALUES.app.use_runtime_builders.Get())
    properties.VALUES.app.use_runtime_builders.Set(False)

  def FingerprintMock(self, path, params):
    self.path = path
    self.params = params
    return mock.MagicMock()


@test_case.Filters.RunOnlyIf(properties.VALUES.app.runtime_root.Get(),
                             'No app runtime root is configured')
class GenConfigTest(FingerprintingTestBase):

  def SetUp(self):
    self.WriteNodeFiles()
    self.StartPatch(
        'gae_ext_runtime.ext_runtime.ExternalizedRuntime.Fingerprint',
        new=self.FingerprintMock)

  def WriteNodeFiles(self):
    self.WriteFile('app.yaml', NODEJS_APP_YAML)
    self.WriteJSON('package.json', {'scripts': {'start': 'node foo.js'}})
    self.WriteFile('foo.js', 'console.log("hello")')

  def testFileGeneration(self):
    # This test needs to run in the GA track because the Node.js beta track
    # uses the Runtime Builder that (by design) doesn't do fingerprinting.
    self.track = calliope_base.ReleaseTrack.GA
    self.Run('app deploy %s/app.yaml --bucket=gs://bucket' % self.temp_path)
    self.assertTrue(self.params)
    self.assertFalse(self.params.custom)
    self.assertTrue(self.params.appinfo)
    self.assertFalse(self.params.appinfo.vm)
    self.assertEqual(self.params.appinfo.env, 'flex')

  def testGenConfigCustomFlag(self):
    self.WriteFile('app.yaml', CUSTOM_APP_YAML)
    self.Run('app gen-config --custom %s' % self.temp_path)
    self.assertTrue(self.params)
    self.assertTrue(self.params.appinfo)
    self.assertTrue(self.params.custom)

  def testGenConfigAppYamlFlag(self):
    os.remove(os.path.join(self.temp_path, 'app.yaml'))
    self.WriteFile('foobar.yaml', CUSTOM_APP_YAML)
    with self.assertRaises(fingerprinter.ConflictingConfigError):
      self.Run('app gen-config --config %s/foobar.yaml' % self.temp_path)
    self.AssertErrContains('already exists')

  def testGenConfigNoAppYaml(self):
    os.remove(os.path.join(self.temp_path, 'app.yaml'))
    self.Run('app gen-config %s' % self.temp_path)
    self.assertTrue(self.params)
    self.assertFalse(self.params.appinfo)
    self.assertFalse(self.params.custom)

  def testConfigCustomWithBadAppYaml(self):
    self.WriteFile('app.yaml', NODEJS_APP_YAML)
    self.Run('app gen-config --custom %s' % self.temp_path)
    self.AssertErrContains(output_helpers.RUNTIME_MISMATCH_MSG.format(
        os.path.join(self.temp_path, 'app.yaml'), normalize_space=True))

  def testGenConfigAppYamlFlex(self):
    """Test that params are generated with an `vm: true` app.yaml."""
    # This test needs to run in the GA track because the Node.js beta track
    # uses the Runtime Builder that (by design) doesn't do fingerprinting.
    self.track = calliope_base.ReleaseTrack.GA
    self.WriteFile('app.yaml', NODEJS_APP_YAML_VM_TRUE)
    self.Run('app deploy %s/app.yaml --bucket=gs://bucket' % self.temp_path)
    self.assertTrue(self.params)
    self.assertFalse(self.params.custom)
    self.assertTrue(self.params.appinfo)
    self.assertTrue(self.params.appinfo.vm)
    self.assertFalse(self.params.appinfo.env, 'flex')


@test_case.Filters.RunOnlyIf(properties.VALUES.app.runtime_root.Get(),
                             'No app runtime root is configured')
class DeployFingerprintingTest(FingerprintingTestBase,
                               sdk_test_base.WithTempCWD):

  def SetUp(self):
    self.temp_path = os.getcwd()

  def testDeployNoAppYaml(self):
    """Test that nodejs deployment writes app.yaml if necessary."""
    # This test needs to run in the GA track because the Node.js beta track
    # uses the Runtime Builder that (by design) doesn't do fingerprinting.
    self.track = calliope_base.ReleaseTrack.GA
    self.WriteJSON('package.json', {'scripts': {'start': 'node foo.js'}})
    self.WriteFile('foo.js', 'console.log("hello")')
    self.Run('app deploy --bucket=gs://bucket')
    self.assertTrue('app.yaml' in os.listdir(self.temp_path))

  def testGAEV1Java(self):
    """Verify that we don't call fingerprinting for java v1."""
    self.WriteFile('app.yaml', JAVA_V1_APP_YAML)
    self.StartPatch(
        'gae_ext_runtime.ext_runtime.ExternalizedRuntime.Fingerprint',
        new=self.FingerprintMock)
    self.Run('app deploy %s/app.yaml --bucket=gs://bucket' % self.temp_path)
    self.assertFalse(self.params)

  # TODO(b/36053575): test that we respond sanely when runtime: nodejs and we
  # can't fingerprint.


if __name__ == '__main__':
  test_case.main()
