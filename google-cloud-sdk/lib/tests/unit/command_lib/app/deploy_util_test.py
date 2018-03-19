# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for deployable services and configs."""
import os

from googlecloudsdk.api_lib.app import build
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import deploy_util
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import api_test_util
from googlecloudsdk.third_party.appengine.api import appinfo

import mock


VALID_RUNTIME = 'go'
VALID_RUNTIME_WITH_DOT = 'go-1.8'
PINNED_BUILDER_RUNTIME = 'gs://foo/bar.yaml'
RUNTIME_CUSTOM = 'custom'


class GetRuntimeBuilderStrategyTest(sdk_test_base.SdkBase):
  """Tests for deploy_util.GetRuntimeBuilderStrategy."""

  ALPHA = base.ReleaseTrack.ALPHA
  BETA = base.ReleaseTrack.BETA
  GA = base.ReleaseTrack.GA
  TRACKS = (ALPHA, BETA, GA)

  def testGetRuntimeBuilderStrategy_WhitelistByDefault(self):
    """Tests release track default behavior."""
    self.assertEqual(
        deploy_util.GetRuntimeBuilderStrategy(self.BETA),
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_BETA)
    self.assertEqual(
        deploy_util.GetRuntimeBuilderStrategy(self.GA),
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_GA)
    with self.assertRaisesRegexp(ValueError, 'Unrecognized release track'):
      deploy_util.GetRuntimeBuilderStrategy(self.ALPHA)

  def testGetRuntimeBuilderStrategy_PropertyTrue(self):
    """Tests that an explicit property overrides release track default."""
    properties.VALUES.app.use_runtime_builders.Set('true')
    for release_track in self.TRACKS:
      self.assertEqual(
          deploy_util.GetRuntimeBuilderStrategy(release_track),
          runtime_builders.RuntimeBuilderStrategy.ALWAYS)

  def testGetRuntimeBuilderStrategy_PropertyFalse(self):
    """Tests that an explicit property overrides release track default."""
    properties.VALUES.app.use_runtime_builders.Set('false')
    for release_track in self.TRACKS:
      self.assertEqual(
          deploy_util.GetRuntimeBuilderStrategy(release_track),
          runtime_builders.RuntimeBuilderStrategy.NEVER)


class ServiceDeployerTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.service_mock = mock.MagicMock()
    self.fake_image = u'appengine.gcr.io/gcloud/1.default'
    fake_image_artifact = build.BuildArtifact.MakeImageArtifact(self.fake_image)
    self.fake_image_artifact = fake_image_artifact
    self.fake_version = version_util.Version(self.Project(), 'default', '1')
    deploy_options = deploy_util.DeployOptions.FromProperties(
        runtime_builders.RuntimeBuilderStrategy.NEVER,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.deployer = deploy_util.ServiceDeployer(self.mock_client,
                                                deploy_options)

  def testDoesntRequireImage(self):
    self.service_mock.RequiresImage.return_value = False
    result = self.deployer._PossiblyBuildAndPush(
        None, self.service_mock, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNone(result)

  def testBuildsImageIfNone(self):
    self.service_mock.RequiresImage.return_value = True
    self.StartObjectPatch(
        deploy_command_util,
        'BuildAndPushDockerImage',
        return_value=self.fake_image_artifact)
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertEqual(result.identifier, self.fake_image)

  def testRequiresImageAndImageExists(self):
    self.service_mock.RequiresImage.return_value = True
    self.service_mock.parsed.skip_files.regex.return_value = True
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.AssertErrContains(
        'WARNING: Deployment of service [default] will ignore the skip_files '
        'field in the configuration file, because the image has already been '
        'built.')
    self.assertEqual(result.identifier, self.fake_image)

  def testDoesntRequireImageAndImageExists(self):
    """If an image is provided, it should always be added to the deployment."""
    self.service_mock.RequiresImage.return_value = False
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertEqual(result.identifier, self.fake_image)

  def testBuildOnServer(self):
    """If build image on server, don't build the image in client."""
    self.service_mock.GetAppYamlBasename.return_value = 'zap.yaml'
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertEqual(result.identifier, {'appYamlPath': 'zap.yaml'})

  def testBuildOnServer_CloudBuildTimeout(self):
    """If build image on server, don't build the image in client."""
    self.service_mock.GetAppYamlBasename.return_value = 'zap.yaml'
    properties.VALUES.app.cloud_build_timeout.Set('333')
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertEqual(result.identifier,
                     {'appYamlPath': 'zap.yaml',
                      'cloudBuildTimeout': '333'})

  def testPossiblyUploadFiles_BuildOnClient(self):
    """If build image on client, and non-hermetic service, upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    self.StartObjectPatch(deploy_app_command_util, 'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        None, mock_service_info, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNotNone(result)

  def testPossiblyUploadFiles_BuildOnServer(self):
    """If build image on server, and non-hermetic service, upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    self.StartObjectPatch(deploy_app_command_util, 'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        None, mock_service_info, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertIsNotNone(result)


class PrintPostDeployHintsTest(sdk_test_base.WithLogCapture):
  """Tests for PrintPostDeployHints."""

  def testProjectFlagUsed(self):
    properties.VALUES.core.project.Set('project2')
    deploy_util.PrintPostDeployHints([mock.MagicMock(service='default')], [])
    self.AssertLogContains('gcloud app browse --project=project2')

  def testProjectFlagUnused(self):
    deploy_util.PrintPostDeployHints([mock.MagicMock(service='default')], [])
    self.AssertLogNotContains('--project')


def _MakeConfig(runtime, env='flex'):
  module = 'my-module'
  source_dir = 'my-module'
  app_yaml = appinfo.AppInfoExternal(runtime=runtime, env=env)
  source_dir = os.path.join(source_dir, module)
  app_yaml_path = os.path.join(source_dir, 'app.yaml')
  yaml_info = yaml_parsing.ServiceYamlInfo(app_yaml_path, app_yaml)
  return yaml_info


def _MakeDeployer(use_runtime_builders=True):
  if use_runtime_builders:
    strategy = runtime_builders.RuntimeBuilderStrategy.ALWAYS
  else:
    strategy = runtime_builders.RuntimeBuilderStrategy.NEVER
  deploy_options = deploy_util.DeployOptions(
      False, False, strategy,
      deploy_util.FlexImageBuildOptions.ON_CLIENT)
  return deploy_util.ServiceDeployer(None, deploy_options)


if __name__ == '__main__':
  test_case.main()
