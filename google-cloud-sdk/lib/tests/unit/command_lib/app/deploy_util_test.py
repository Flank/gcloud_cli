# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.app import build
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.app import deploy_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
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

  ALPHA = calliope_base.ReleaseTrack.ALPHA
  BETA = calliope_base.ReleaseTrack.BETA
  GA = calliope_base.ReleaseTrack.GA
  TRACKS = (ALPHA, BETA, GA)

  def testGetRuntimeBuilderStrategy_WhitelistByDefault(self):
    """Tests release track default behavior."""
    self.assertEqual(
        deploy_util.GetRuntimeBuilderStrategy(self.BETA),
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_BETA)
    self.assertEqual(
        deploy_util.GetRuntimeBuilderStrategy(self.GA),
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_GA)
    with self.assertRaisesRegex(ValueError, 'Unrecognized release track'):
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


class ServiceDeployerTest(parameterized.TestCase, api_test_util.ApiTestBase):

  def SetUp(self):
    self.service_mock = mock.MagicMock()
    self.fake_image = 'appengine.gcr.io/gcloud/1.default'
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
        None, self.service_mock, None, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNone(result)

  def testBuildsImageIfNone(self):
    self.service_mock.RequiresImage.return_value = True
    self.StartObjectPatch(
        deploy_command_util,
        'BuildAndPushDockerImage',
        return_value=self.fake_image_artifact)
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertEqual(result.identifier, self.fake_image)

  def testRequiresImageAndImageExists_onClient(self):
    self.service_mock.RequiresImage.return_value = True
    self.service_mock.parsed.skip_files.regex.return_value = True
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None,
        self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.AssertErrContains(
        'WARNING: Deployment of service [default] will ignore the skip_files '
        'field in the configuration file, because the image has already been '
        'built.')
    self.assertEqual(result.identifier, self.fake_image)

  def testRequiresImageAndImageExists_onServer(self):
    self.service_mock.RequiresImage.return_value = True
    self.service_mock.parsed.skip_files.regex.return_value = True
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None,
        self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
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
        self.fake_version, self.service_mock, None, None,
        self.fake_image, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertEqual(result.identifier, self.fake_image)

  def testBuildOnServer(self):
    """If build image on server, don't build the image in client."""
    self.service_mock.GetAppYamlBasename.return_value = 'zap.yaml'
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertEqual(result.identifier, {'appYamlPath': 'zap.yaml'})

  @parameterized.parameters(('333', '333s'), ('333s', '333s'), ('6m', '360s'))
  def testBuildOnServer_CloudBuildTimeoutWithoutSuffix(self, timeout_property,
                                                       expected):
    self.service_mock.GetAppYamlBasename.return_value = 'zap.yaml'
    properties.VALUES.app.cloud_build_timeout.Set(timeout_property)
    self.StartObjectPatch(deploy_command_util, 'BuildAndPushDockerImage')
    result = self.deployer._PossiblyBuildAndPush(
        self.fake_version, self.service_mock, None, None, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertEqual(result.identifier, {
        'appYamlPath': 'zap.yaml',
        'cloudBuildTimeout': expected
    })

  def testPossiblyUploadFiles_imageUrl(self):
    """If image-url on client, and hermetic service, don't upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = True
    mock_service_info.env = env.FLEX
    copy_files_mock = self.StartObjectPatch(deploy_app_command_util,
                                            'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        self.fake_image, mock_service_info, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNone(result)
    copy_files_mock.assert_not_called()

  def testPossiblyUploadFiles_BuildOnClient_hermetic(self):
    """If image-url on client, and hermetic service, don't upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = True
    mock_service_info.env = env.FLEX
    copy_files_mock = self.StartObjectPatch(deploy_app_command_util,
                                            'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        self.fake_image, mock_service_info, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNone(result)
    copy_files_mock.assert_not_called()

  def testPossiblyUploadFiles_BuildOnClient_nonHermetic(self):
    """If build image on client, and non-hermetic service, upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    mock_service_info.env = env.FLEX
    copy_files_mock = self.StartObjectPatch(
        deploy_app_command_util, 'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        None, mock_service_info, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_CLIENT)
    self.assertIsNotNone(result)
    copy_files_mock.assert_called_once_with(
        None, None, None, max_file_size=None)

  def testPossiblyUploadFiles_BuildOnServer(self):
    """If build image on server, and hermetic service, upload files."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = True
    mock_service_info.env = env.FLEX
    copy_files_mock = self.StartObjectPatch(
        deploy_app_command_util, 'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        None, mock_service_info, None, None, None,
        deploy_util.FlexImageBuildOptions.ON_SERVER)
    self.assertIsNotNone(result)
    copy_files_mock.assert_called_once_with(
        None, None, None, max_file_size=None)

  def testPossiblyUploadFiles_Java8Standard(self):
    """Check the standard path, specifically file size limit."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    mock_service_info.env = env.STANDARD
    mock_service_info.runtime = 'java8'
    copy_files_mock = self.StartObjectPatch(deploy_app_command_util,
                                            'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(None, mock_service_info, None,
                                                None, None, None)
    self.assertIsNotNone(result)
    # Check that the file size limitation is in effect
    copy_files_mock.assert_called_once_with(
        None, None, None, max_file_size=32 * 1024 * 1024)

  def testPossiblyUploadFiles_PythonStandard(self):
    """Check the standard path, specifically file size limit."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    mock_service_info.env = env.STANDARD
    mock_service_info.runtime = 'python27'
    copy_files_mock = self.StartObjectPatch(deploy_app_command_util,
                                            'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(None, mock_service_info, None,
                                                None, None, None)
    self.assertIsNotNone(result)
    # Check that the file size limitation is in effect
    copy_files_mock.assert_called_once_with(
        None, None, None, max_file_size=32 * 1024 * 1024)

  def testPossiblyUploadFiles_Java11Standard(self):
    """Check the standard path, specifically file size limit."""
    mock_service_info = mock.MagicMock()
    mock_service_info.is_hermetic = False
    mock_service_info.env = env.STANDARD
    mock_service_info.runtime = 'java8'
    copy_files_mock = self.StartObjectPatch(
        deploy_app_command_util, 'CopyFilesToCodeBucket')
    result = self.deployer._PossiblyUploadFiles(
        None, mock_service_info, None, None, None, None)
    self.assertIsNotNone(result)
    # Check that the file size limitation is in effect
    copy_files_mock.assert_called_once_with(
        None, None, None, max_file_size=32 * 1024 * 1024)


class PrintPostDeployHintsTest(sdk_test_base.WithLogCapture):
  """Tests for PrintPostDeployHints."""

  def testProjectFlagUsed(self):
    properties.VALUES.core.project.Set('project2')
    deploy_util.PrintPostDeployHints([mock.MagicMock(service='default')], [])
    self.AssertLogContains('gcloud app browse --project=project2')

  def testProjectFlagUnused(self):
    deploy_util.PrintPostDeployHints([mock.MagicMock(service='default')], [])
    self.AssertLogNotContains('--project')


def _MakeConfig(runtime, environment='flex'):
  module = 'my-module'
  source_dir = 'my-module'
  app_yaml = appinfo.AppInfoExternal(runtime=runtime, env=environment)
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


class FlexBuildOptionTest(sdk_test_base.SdkBase):
  """Tests GetFlexImageBuildOption, which determines where the build occurs.

  The method lets you specify a default build strategy in the argument (whose
  default is ON_CLIENT), and then a property `app/trigger_build_server_side`
  to override that behavior. Here we exhaustively test the relevant
  combinations of those.
  """

  ON_CLIENT = deploy_util.FlexImageBuildOptions.ON_CLIENT  # Simple short cuts
  ON_SERVER = deploy_util.FlexImageBuildOptions.ON_SERVER

  def testVanilla(self):
    actual = deploy_util.GetFlexImageBuildOption()
    self.assertEqual(actual, self.ON_CLIENT)

  def testChangeDefault(self):
    actual = deploy_util.GetFlexImageBuildOption(self.ON_SERVER)
    self.assertEqual(actual, self.ON_SERVER)

  def testOverrideWithProperty_OnServer(self):
    properties.VALUES.app.trigger_build_server_side.Set('true')
    actual = deploy_util.GetFlexImageBuildOption()
    self.assertEqual(actual, self.ON_SERVER)

  def testOverrideWithProperty_OnClient(self):
    properties.VALUES.app.trigger_build_server_side.Set('false')
    actual = deploy_util.GetFlexImageBuildOption(self.ON_SERVER)
    self.assertEqual(actual, self.ON_CLIENT)


if __name__ == '__main__':
  test_case.main()
