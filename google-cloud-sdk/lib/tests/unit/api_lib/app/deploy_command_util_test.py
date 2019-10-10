# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for deploy_command_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json
import logging
import os
import uuid

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import appengine_client
from googlecloudsdk.api_lib.app import cloud_build
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import util as app_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.images import config
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.api_lib.app.runtimes import go
from googlecloudsdk.api_lib.app.runtimes import python_compat
from googlecloudsdk.api_lib.app.runtimes import ruby
from googlecloudsdk.api_lib.cloudbuild import build
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import build_base
from tests.lib.apitools import http_error
from tests.lib.surface.app import source_context_util
from tests.lib.surface.app import util
from googlecloudsdk.third_party.appengine.api import appinfo
from googlecloudsdk.third_party.appengine.tools import context_util

import mock
import six.moves.urllib.error

PROJECT = 'fakeproject'
ACCOUNT = 'fakeaccount'
APPENGINE_API = 'appengine'
APPENGINE_API_VERSION = appengine_api_client.AppengineApiClient.ApiVersion()


def Config(module=None, vm=None, runtime=None, tmpdir=None, env=None):
  tmpdir = tmpdir or ''
  appyaml = appinfo.AppInfoExternal(module=module, vm=vm, runtime=runtime,
                                    env=env)
  # This is needed because of some hackery in appinfo.py. If users specify
  # vm: true or env: flex or env: 2, we set 'runtime' to 'vm' and place the
  # specified runtime in vm_settings.vm_runtime.
  if appyaml.vm:
    appyaml.vm_settings = appinfo.VmSettings(vm_runtime=appyaml.runtime)
    appyaml.runtime = 'vm'
  source_dir = os.path.join(tmpdir, module)
  files.MakeDir(source_dir)
  return yaml_parsing.ServiceYamlInfo(
      os.path.join(source_dir, 'app.yaml'),
      appyaml)


class PushTestBase(util.WithAppData, build_base.BuildBase):

  def _MakeConfig(self, module='foo', vm=None, runtime='python27', env='flex'):
    return Config(module=module, vm=vm, runtime=runtime, env=env,
                  tmpdir=self.temp_path)

  def SetUp(self):
    # Global configuration
    properties.VALUES.core.project.Set(PROJECT)
    properties.VALUES.core.account.Set(ACCOUNT)

    # Mocks
    self.upload_mock = self.StartObjectPatch(cloud_build, 'UploadSource',
                                             return_value=True)
    self.execute_cloud_build_mock = self.StartObjectPatch(
        build.CloudBuildClient, 'ExecuteCloudBuild')
    self.execute_cloud_build_async_mock = self.StartObjectPatch(
        build.CloudBuildClient,
        'ExecuteCloudBuildAsync',
        return_value=self.build_op)
    self.context_mock = self.StartObjectPatch(
        context_util, 'CalculateExtendedSourceContexts')

    # Pre-created objects/utilities
    self.service_config = self._MakeConfig(module='foo', env='flex',
                                           runtime='python27')
    self.code_bucket_ref = storage_util.BucketReference.FromUrl(
        'gs://bucket/')
    self.source_dir = os.path.dirname(self.service_config.file)
    self.app_files = ['f1.txt', 'f2.png']
    self.messages = cloudbuild_util.GetMessagesModule()

    # For briefer typing
    self.substitution_types = (
        self.messages.BuildOptions.SubstitutionOptionValueValuesEnum)

  def TearDown(self):
    # Wait for all threads to finish, like the ProgressTracker ticker thread.
    self.JoinAllThreads()


class PushTestRuntimeBuilders(PushTestBase):

  def SetUp(self):
    self.generate_configs_mock = self.StartObjectPatch(
        python_compat.PythonConfigurator, 'GenerateConfigData', return_value=[])
    self.context_mock.side_effect = context_util.GenerateSourceContextError

  def _MockLoadCloudBuild(self):
    self.StartObjectPatch(
        runtime_builders.Resolver, 'GetBuilderReference',
        autospec=True, side_effect=
        lambda self: runtime_builders.BuilderReference(self.runtime, 'path'))
    self.load_cloud_build_mock = self.StartObjectPatch(
        runtime_builders.BuilderReference, 'LoadCloudBuild',
        return_value=self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            steps=[],
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE)))

  def testModuleBuildUseRuntimeBuilders(self):
    """Tests the scenario when the runtime_builder_strategy flag is turned on.

    The differences here from the other test cases:
    - no dockerfile generation
    - instead of using a default Build() message, one is loaded via
      LoadCloudBuild (mocked)
    """
    self._MockLoadCloudBuild()
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref,
        gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.ALWAYS)

    self.generate_configs_mock.assert_not_called()
    self.load_cloud_build_mock.assert_called_once_with(
        {'_OUTPUT_IMAGE': 'blah.gcr.io/fakeproject/appengine/foo.1.2:latest',
         '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[],
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE)),
        project='fakeproject')

  def testModuleBuildUseRuntimeBuildersDifferentApplicationYamlPath(self):
    """Tests the scenario when the runtime_builder_strategy flag is turned on.

    The differences here from the other test cases:
    - no dockerfile generation
    - instead of using a default Build() message, one is loaded via
      LoadCloudBuild (mocked)
    - the application YAML file is not called "app.yaml"
    """
    self._MockLoadCloudBuild()
    self.service_config.file = os.path.join(self.source_dir, 'subdir',
                                            'bar.yaml')
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref,
        gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.ALWAYS)

    self.generate_configs_mock.assert_not_called()
    self.load_cloud_build_mock.assert_called_once_with(
        {'_OUTPUT_IMAGE': 'blah.gcr.io/fakeproject/appengine/foo.1.2:latest',
         '_GAE_APPLICATION_YAML_PATH': 'subdir/bar.yaml'})
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[],
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE)),
        project='fakeproject')

  def testModuleBuildUseRuntimeBuildersDifferentApplicationYamlDirectory(self):
    """Tests the scenario when the runtime_builder_strategy flag is turned on.

    The differences here from the other test cases:
    - no dockerfile generation
    - instead of using a default Build() message, one is loaded via
      LoadCloudBuild (mocked)
    - the application YAML file is not called "app.yaml", and it is not in the
      source directory
    """
    self._MockLoadCloudBuild()
    old_relpath = os.path.relpath
    def _FakeRelPath(path, start='.'):
      if not os.path.abspath(path).startswith(os.path.abspath(start)):
        raise ValueError('relpath can raise on Windows in this circumstance.')
      return old_relpath(path, start=start)
    self.StartObjectPatch(os.path, 'relpath', _FakeRelPath)
    self.service_config.file = os.path.join(self.temp_path, 'subdir',
                                            'bar.yaml')
    self.Touch(os.path.join(self.temp_path, 'subdir'), 'bar.yaml',
               contents='yaml contents', makedirs=True)
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref,
        gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.ALWAYS)

    self.generate_configs_mock.assert_not_called()
    # echo -n 'yaml contents' | sha256sum
    checksum_path = ('_app_f4a49b7a0ea6708939d6f4b149db7bb5597ddbd71855c46c'
                     '6a9e8d56ec1ca72b.yaml')
    self.load_cloud_build_mock.assert_called_once_with(
        {'_OUTPUT_IMAGE': 'blah.gcr.io/fakeproject/appengine/foo.1.2:latest',
         '_GAE_APPLICATION_YAML_PATH': checksum_path})
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[],
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE)),
        project='fakeproject')
    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            checksum_path: 'yaml contents'
        }
    )

  def testModuleBuildUseRuntimeBuilders_CustomRuntimeDockerfile(self):
    """Tests the scenario when the runtime_builder_strategy flag is turned on.

    The differences here from the other test cases:
    - the runtime is custom, and there is a Dockerfile
    - this means we should use the default Build() message
    """
    self._MockLoadCloudBuild()
    self.service_config = self._MakeConfig(runtime='custom')
    self.Touch(self.source_dir, 'Dockerfile', makedirs=True)
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref, gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.ALWAYS)

    self.generate_configs_mock.assert_not_called()
    self.load_cloud_build_mock.assert_not_called()
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=[
                        'build',
                        '-t',
                        'blah.gcr.io/fakeproject/appengine/foo.1.2:latest', '.'
                    ]
                )
            ]),
        project='fakeproject')

  def testModuleBuildUseRuntimeBuilders_CustomRuntimeCloudbuildYaml(self):
    """Tests the scenario when the runtime_builder_strategy flag is turned on.

    The differences here from the other test cases:
    - the runtime is custom, and there is a cloudbuild.yaml (no Dockerfile)
    - this means we should use a build message from that cloudbuild.yaml
    """
    self.service_config = self._MakeConfig(runtime='custom')
    self.Touch(
        self.source_dir, 'cloudbuild.yaml', makedirs=True, contents="""\
            steps:
            - name: 'us.gcr.io/cloud-builders/erlang-builder'
            - name: 'us.gcr.io/cloud-builders/docker'
              args: ['build', '-t', '$_OUTPUT_IMAGE', '.']
            images: ['$_OUTPUT_IMAGE']
            """)
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref, gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.ALWAYS)

    self.generate_configs_mock.assert_not_called()
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['$_OUTPUT_IMAGE'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[
                self.messages.BuildStep(
                    name='us.gcr.io/cloud-builders/erlang-builder',
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']
                ),
                self.messages.BuildStep(
                    name='us.gcr.io/cloud-builders/docker',
                    args=['build', '-t', '$_OUTPUT_IMAGE', '.'],
                    env=['GAE_APPLICATION_YAML_PATH='
                         '${_GAE_APPLICATION_YAML_PATH}']
                )
            ],
            substitutions=self.messages.Build.SubstitutionsValue(
                additionalProperties=[
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_GAE_APPLICATION_YAML_PATH',
                        value='app.yaml'
                    ),
                    self.messages.Build.SubstitutionsValue.AdditionalProperty(
                        key='_OUTPUT_IMAGE',
                        value='blah.gcr.io/fakeproject/appengine/foo.1.2:latest'
                    )
                ]
            ),
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE),
        ),
        project='fakeproject')

  def testModuleBuildUseRuntimeBuildersWhitelistedRuntime(self):
    """Tests runtime_builder_strategy of "whitelist" for a whitelisted runtime.

    The differences here from the other test cases:
    - no dockerfile generation
    - instead of using a default Build() message, one is loaded via
      LoadCloudBuild (mocked)
    """
    self._MockLoadCloudBuild()
    self.service_config = self._MakeConfig(runtime='test-beta')
    runtime_builder_strategy = (
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_BETA)

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        code_bucket_ref=self.code_bucket_ref,
        gcr_domain='blah.gcr.io',
        runtime_builder_strategy=runtime_builder_strategy)

    self.generate_configs_mock.assert_not_called()
    self.load_cloud_build_mock.assert_called_once_with(
        {'_OUTPUT_IMAGE': 'blah.gcr.io/fakeproject/appengine/foo.1.2:latest',
         '_GAE_APPLICATION_YAML_PATH': 'app.yaml'})
    self.execute_cloud_build_mock.assert_called_once_with(
        self.messages.Build(
            images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
            steps=[],
            options=self.messages.BuildOptions(
                substitutionOption=self.substitution_types.ALLOW_LOOSE)),
        project='fakeproject')

  def testModuleBuildUseRuntimeBuildersNonWhitelistedRuntime(self):
    """Tests runtime_builder_strategy "whitelist" for a non-whitelisted runtime.

    Identical to case where whitelisting is turned off.
    """
    modules = [
        Config(module='foo', env='flex', runtime='python27',
               tmpdir=self.temp_path),
        Config(module='baz', env='flex', runtime='python27',
               tmpdir=self.temp_path),
        Config(module='bar', runtime='python', tmpdir=self.temp_path)
    ]
    runtime_builder_strategy = (
        runtime_builders.RuntimeBuilderStrategy.WHITELIST_BETA)
    for module in modules:
      source_dir = os.path.dirname(module.file)
      deploy_command_util.BuildAndPushDockerImage(
          'fakeproject', module, source_dir, self.app_files,
          version_id='1.2',
          code_bucket_ref=self.code_bucket_ref,
          gcr_domain='blah.gcr.io',
          runtime_builder_strategy=runtime_builder_strategy)

    self.assertEqual(self.generate_configs_mock.call_count, 2)
    self.context_mock.assert_has_calls(
        [
            mock.call(os.path.dirname(info.file))
            for info in modules if info.RequiresImage()],
        any_order=True)

  def testDockerfileAndRuntimeBuilder(self):
    dockerfile_path = os.path.join(self.source_dir, config.DOCKERFILE)
    self.WriteFile(dockerfile_path, 'empty')

    runtime_builder_strategy = runtime_builders.RuntimeBuilderStrategy.ALWAYS
    with self.assertRaises(deploy_command_util.DockerfileError):
      deploy_command_util.BuildAndPushDockerImage(
          PROJECT, self.service_config, self.source_dir, self.app_files,
          version_id='1.2',
          code_bucket_ref=self.code_bucket_ref,
          gcr_domain='blah.gcr.io',
          runtime_builder_strategy=runtime_builder_strategy)

  def testCloudbuildYamlAndRuntimeBuilder(self):
    cloudbuild_yaml_path = os.path.join(self.source_dir, 'cloudbuild.yaml')
    self.WriteFile(cloudbuild_yaml_path, 'empty')

    runtime_builder_strategy = runtime_builders.RuntimeBuilderStrategy.ALWAYS
    with self.assertRaises(deploy_command_util.CloudbuildYamlError):
      deploy_command_util.BuildAndPushDockerImage(
          PROJECT, self.service_config, self.source_dir, self.app_files,
          version_id='1.2',
          code_bucket_ref=self.code_bucket_ref,
          gcr_domain='blah.gcr.io',
          runtime_builder_strategy=runtime_builder_strategy)


class PushTest(PushTestBase, test_case.WithOutputCapture):

  def SetUp(self):
    self.generate_configs_mock = self.StartObjectPatch(
        python_compat.PythonConfigurator, 'GenerateConfigData', return_value=[])
    self.context_mock.side_effect = context_util.GenerateSourceContextError
    self.fake_image = mock.MagicMock()
    self.fake_image.tagged_repo = ('blah.gcr.io/fakeproject/appengine'
                                   '/foo.1.2:latest')
    self.fake_build = self.messages.Build(
        images=['blah.gcr.io/fakeproject/appengine/foo.1.2:latest'],
        logsBucket='bucket',
        source=self.messages.Source(storageSource=self.messages.StorageSource(
            bucket='bucket',
            object='blah.gcr.io/fakeproject/appengine/foo.1.2:latest')),
        steps=[],
        options=self.messages.BuildOptions(
            substitutionOption=self.substitution_types.ALLOW_LOOSE))

  def testModuleBuildVMTrue(self):
    """Sanity check to make sure `vm: true` is also identified as vm."""
    self.service_config = self._MakeConfig(env=None, vm=True)

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    self.assertEqual(self.generate_configs_mock.call_count, 1)
    self.assertTrue(self.service_config.RequiresImage())

  def testModuleBuild(self):
    modules = [
        Config(module='foo', env='flex', runtime='python27',
               tmpdir=self.temp_path),
        Config(module='baz', env='flex', runtime='python27',
               tmpdir=self.temp_path),
        Config(module='bar', runtime='python', tmpdir=self.temp_path)
    ]
    for module in modules:
      source_dir = os.path.dirname(module.file)
      deploy_command_util.BuildAndPushDockerImage(
          'fakeproject', module, source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io',
          code_bucket_ref=self.code_bucket_ref)

    self.assertEqual(self.generate_configs_mock.call_count, 2)
    self.context_mock.assert_has_calls(
        [
            mock.call(os.path.dirname(info.file))
            for info in modules if info.RequiresImage()],
        any_order=True)

  def testModuleBuild_OSErrorExceedsMaxPath(self):
    # MAX_PATH limitation is specific to Windows
    self.StartObjectPatch(platforms.OperatingSystem, 'Current',
                          return_value=platforms.OperatingSystem.WINDOWS)
    long_filename = 'a' * 1000 + '.txt'
    self.upload_mock.side_effect = OSError(None, None, long_filename)
    self.StartObjectPatch(context_util, 'GetSourceContextFilesCreator',
                          side_effect={})

    module = Config(module='foo', env='flex', runtime='python27',
                    tmpdir=self.temp_path)
    with self.assertRaisesRegex(deploy_command_util.WindowMaxPathError,
                                long_filename):
      source_dir = os.path.dirname(module.file)
      deploy_command_util.BuildAndPushDockerImage(
          'fakeproject', module, source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io',
          code_bucket_ref=self.code_bucket_ref)

  def testModuleBuild_OSErrorNoFilename(self):
    self.upload_mock.side_effect = OSError(None, None, None)
    self.StartObjectPatch(context_util, 'GetSourceContextFilesCreator',
                          side_effect={})

    module = Config(module='foo', env='flex', runtime='python27',
                    tmpdir=self.temp_path)
    with self.assertRaises(OSError):
      source_dir = os.path.dirname(module.file)
      deploy_command_util.BuildAndPushDockerImage(
          'fakeproject', module, source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io',
          code_bucket_ref=self.code_bucket_ref)

  def testModuleBuild_OSErrorNotExceedsMaxPath(self):
    self.upload_mock.side_effect = OSError(None, None, 'foo.txt')
    self.StartObjectPatch(context_util, 'GetSourceContextFilesCreator',
                          side_effect={})

    module = Config(module='foo', env='flex', runtime='python27',
                    tmpdir=self.temp_path)
    with self.assertRaises(OSError):
      source_dir = os.path.dirname(module.file)
      deploy_command_util.BuildAndPushDockerImage(
          'fakeproject', module, source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io',
          code_bucket_ref=self.code_bucket_ref)

  def testDockerfileAndRuntime(self):
    dockerfile_path = os.path.join(self.source_dir, config.DOCKERFILE)
    self.WriteFile(dockerfile_path, 'empty')

    with self.assertRaises(deploy_command_util.DockerfileError):
      deploy_command_util.BuildAndPushDockerImage(
          PROJECT, self.service_config, self.source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io', code_bucket_ref=self.code_bucket_ref)

  def testDockerfileAndCloudbuildRuntimeCustom(self):
    """Tests that a user cannot provide both Dockerfile and cloudbuild.yaml.

    This is bad because it's impossible to figure out which one they want us to
    use.
    """
    self.service_config = self._MakeConfig(runtime='custom')
    dockerfile_path = os.path.join(self.source_dir, config.DOCKERFILE)
    self.WriteFile(dockerfile_path, 'empty')
    cloudbuild_path = os.path.join(self.source_dir,
                                   runtime_builders.Resolver.CLOUDBUILD_FILE)
    self.WriteFile(cloudbuild_path, 'empty')

    with self.assertRaises(deploy_command_util.CustomRuntimeFilesError):
      deploy_command_util.BuildAndPushDockerImage(
          PROJECT, self.service_config, self.source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io', code_bucket_ref=self.code_bucket_ref)

  def testDockerfileAndRuntimeCustom(self):
    self.service_config.runtime = 'custom'
    dockerfile_path = os.path.join(self.source_dir, config.DOCKERFILE)
    self.WriteFile(dockerfile_path, 'empty')
    fingerprint_mock = self.StartObjectPatch(fingerprinter, 'IdentifyDirectory')

    deploy_command_util.BuildAndPushDockerImage(
        PROJECT, self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io', code_bucket_ref=self.code_bucket_ref)

    fingerprint_mock.assert_not_called()

  def testUnsatisfiedRequirements(self):
    self.StartObjectPatch(fingerprinter, 'IdentifyDirectory', return_value=None)

    with self.assertRaises(deploy_command_util.UnsatisfiedRequirementsError):
      deploy_command_util.BuildAndPushDockerImage(
          PROJECT, self.service_config, self.source_dir, self.app_files,
          version_id='1.2',
          gcr_domain='blah.gcr.io', code_bucket_ref=self.code_bucket_ref)

  def testGetDomainAndDisplayId(self):
    self.assertEqual(('myapp', None),
                     deploy_command_util._GetDomainAndDisplayId('myapp'))
    self.assertEqual(
        ('myapp', 'google.com'),
        deploy_command_util._GetDomainAndDisplayId('google.com:myapp'))

  def testGetImageName(self):
    self.assertEqual(
        'blah.gcr.io/google.com/myapp/appengine/module.version',
        deploy_command_util._GetImageName('google.com:myapp',
                                          'module', 'version', 'blah.gcr.io'))

  def testParallelSubmitBuild(self):
    result = deploy_command_util._SubmitBuild(self.fake_build, self.fake_image,
                                              PROJECT, True)
    self.assertEqual(result.identifier, 'build-id')

  def testSerialSubmitBuild(self):
    result = deploy_command_util._SubmitBuild(self.fake_build, self.fake_image,
                                              PROJECT, False)
    self.assertEqual(result.identifier, self.fake_image.tagged_repo)

  def testSubmitBuildWithTimeoutInt(self):
    timeout = '1000'
    properties.VALUES.app.cloud_build_timeout.Set(timeout)
    log.SetVerbosity(logging.INFO)

    result = deploy_command_util._SubmitBuild(self.fake_build, self.fake_image,
                                              PROJECT, True)
    self.assertEqual(result.identifier, self.fake_image.tagged_repo)
    self.AssertErrContains(
        'Property cloud_build_timeout configured to [{0}], which exceeds '
        'the maximum build time for parallelized beta deployments of [{1}] '
        'seconds. Performing serial deployment.'.format(
            timeout, deploy_command_util.MAX_PARALLEL_BUILD_TIME))

  def testSubmitBuildWithTimeoutSuffix(self):
    timeout = '1000'
    properties.VALUES.app.cloud_build_timeout.Set(timeout + 's')
    log.SetVerbosity(logging.INFO)

    result = deploy_command_util._SubmitBuild(self.fake_build, self.fake_image,
                                              PROJECT, True)
    self.assertEqual(result.identifier, self.fake_image.tagged_repo)
    self.AssertErrContains(
        'Property cloud_build_timeout configured to [{0}], which exceeds '
        'the maximum build time for parallelized beta deployments of [{1}] '
        'seconds. Performing serial deployment.'.format(
            timeout, deploy_command_util.MAX_PARALLEL_BUILD_TIME))


class PushTestSourceContexts(PushTestBase):

  def SetUp(self):
    self.context_mock.side_effect = None
    self.context_mock.return_value = source_context_util.FAKE_CONTEXTS
    self.generate_configs_mock = self.StartObjectPatch(
        python_compat.PythonConfigurator, 'GenerateConfigData', return_value=[])

  def testModuleBuildWithContext(self):
    """Test BuildAndPushDockerImage uploads correct source context files."""
    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    self.generate_configs_mock.assert_called_once()
    self.assertFalse(os.path.exists(
        os.path.join(self.source_dir, 'source-context.json')))
    # Check that source context file is sent correctly for upload
    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            'source-context.json': mock.ANY
        }
    )
    _, kwargs = self.upload_mock.call_args
    self.assertEqual(
        json.loads(kwargs['gen_files']['source-context.json']),
        source_context_util.REMOTE_CONTEXT['context'])


class PushTestGenerateConfigs(PushTestBase):

  def SetUp(self):
    self.context_mock.side_effect = context_util.GenerateSourceContextError(
        'Could not list remote URLs from source directory.')

  def testModuleBuildGenerateConfigs(self):
    """Test BuildAndPushDockerImage uploads correct dockerfiles."""
    log.SetVerbosity(logging.INFO)

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    self.context_mock.assert_called_once_with(self.source_dir)

    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            'Dockerfile': (python_compat.PYTHON27_DOCKERFILE_PREAMBLE +
                           python_compat.DOCKERFILE_INSTALL_APP),
            '.dockerignore': python_compat.DOCKERIGNORE
        }
    )
    self.AssertErrContains(
        'Could not generate [source-context.json]: Could not '
        'list remote URLs from source directory.\nStackdriver '
        'Debugger may not be configured or enabled on this '
        'application. See https://cloud.google.com/debugger/ for '
        'more information.')

  def testModuleBuildGenerateConfigsGo(self):
    """Test that we upload correct dockerfiles with non-ext go configurator."""
    self.service_config = self._MakeConfig(runtime='go')
    self.StartObjectPatch(fingerprinter, 'IdentifyDirectory',
                          side_effect=go.GoConfigurator)

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            'Dockerfile': go.DOCKERFILE,
            '.dockerignore': go.DOCKERIGNORE
        })

  def testModuleBuildGenerateConfigsRuby(self):
    """Test that we upload correct dockerfiles w/ non-ext ruby configurator."""
    self.service_config = self._MakeConfig(runtime='ruby')
    def RubyConfig(path, params):
      return ruby.RubyConfigurator(path, params, ruby.FOREMAN_VERSION,
                                   ruby.ENTRYPOINT_FOREMAN, [])
    self.StartObjectPatch(fingerprinter, 'IdentifyDirectory',
                          side_effect=RubyConfig)

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    dockerfile = '\n'.join([
        ruby.DOCKERFILE_HEADER,
        ruby.DOCKERFILE_CUSTOM_INTERPRETER.format(ruby.FOREMAN_VERSION),
        ruby.DOCKERFILE_NO_MORE_PACKAGES,
        ruby.DOCKERFILE_GEM_INSTALL,
        ruby.DOCKERFILE_ENTRYPOINT.format(ruby.ENTRYPOINT_FOREMAN)])
    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            'Dockerfile': dockerfile,
            '.dockerignore': ruby.DOCKERIGNORE_CONTENTS
        })

  def testModuleBuildWithContextAndConfigs(self):
    """Test we upload correct dockerfiles and contexts when both exist."""
    self.context_mock.side_effect = None
    self.context_mock.return_value = source_context_util.FAKE_CONTEXTS

    deploy_command_util.BuildAndPushDockerImage(
        'fakeproject', self.service_config, self.source_dir, self.app_files,
        version_id='1.2',
        gcr_domain='blah.gcr.io',
        code_bucket_ref=self.code_bucket_ref)

    self.context_mock.assert_called_once_with(self.source_dir)
    self.upload_mock.assert_called_once_with(
        self.source_dir, self.app_files,
        mock.ANY,
        gen_files={
            'source-context.json': mock.ANY,
            'Dockerfile': mock.ANY,
            '.dockerignore': mock.ANY
        })


class HostnameTest(sdk_test_base.SdkBase, test_case.WithOutputCapture):

  def SetUp(self):
    self.deployment_warning_msg = (
        'This deployment will result in an invalid SSL certificate '
        'for service [{0}]. The total length of your subdomain in the format '
        '{1} should not exceed {2} characters. Please verify that the '
        'certificate corresponds to the parent domain of your application '
        'when you connect.')
    self.browser_warning_msg = ('Most browsers will reject the SSL certificate '
                                'for service [{0}].')
    self.version_id = 'veryveryveryveryverylongversionid'  # 33 chars
    self.service_id = 'veryveryveryveryverylongserviceid'  # 33 chars
    self.app_id = 'veryveryveryveryverylongappid'  # 29 chars
    self.messages = core_apis.GetMessagesModule(APPENGINE_API,
                                                APPENGINE_API_VERSION)
    self.app = self.messages.Application(
        name='apps/{0}'.format(self.app_id),
        id=self.app_id,
        defaultHostname='{0}.appspot.com'.format(self.app_id))

  def testGetAppHostnameLongSubdomain(self):
    """Test GetAppHostname returns correct hostname, warns on long subdomains.
    """
    # If SSL is not needed, no warnings should be given, and '.' is used as
    # a separator.
    hostname = deploy_command_util.GetAppHostname(app=self.app,
                                                  service=self.service_id,
                                                  version=None,
                                                  use_ssl=appinfo.SECURE_HTTP)
    self.assertEqual(hostname,
                     'http://{0}.{1}.appspot.com'.format(self.service_id,
                                                         self.app_id))
    self.AssertErrNotContains(self.deployment_warning_msg.format(
        self.service_id,
        '$SERVICE_ID-dot-$APP_ID',
        deploy_command_util.MAX_DNS_LABEL_LENGTH
    ))
    self.AssertErrNotContains(self.browser_warning_msg.format(self.service_id))

  def testGetAppHostnameLongSubdomain_OptionalSSL(self):
    """Test GetAppHostname with long subdomain, SSL optional.
    """
    # If SSL is optional, '.' will be used as a separator with http,
    # and a deployment warning should be given.
    hostname = deploy_command_util.GetAppHostname(
        app=self.app,
        service=self.service_id,
        version=self.version_id,
        use_ssl=appinfo.SECURE_HTTP_OR_HTTPS)
    self.assertEqual(hostname,
                     'http://{0}.{1}.{2}.appspot.com'.format(self.version_id,
                                                             self.service_id,
                                                             self.app_id))
    self.AssertErrContains(self.deployment_warning_msg.format(
        self.service_id,
        '$VERSION_ID-dot-$SERVICE_ID-dot-$APP_ID',
        deploy_command_util.MAX_DNS_LABEL_LENGTH))
    self.AssertErrNotContains(self.browser_warning_msg.format(self.service_id))

  def testGetAppHostnameLongSubdomain_AlwaysSSL(self):
    """Test GetAppHostname with long subdomain, SSL required.
    """
    # If SSL is non-optional, '.' will be used as a separator with https, and a
    # deployment warning should be given.
    hostname = deploy_command_util.GetAppHostname(
        app=self.app,
        service=deploy_command_util.DEFAULT_SERVICE,
        version=self.version_id,
        use_ssl=appinfo.SECURE_HTTPS)
    self.assertEqual(hostname,
                     'https://{0}.{1}.appspot.com'.format(self.version_id,
                                                          self.app_id))
    self.AssertErrContains(self.deployment_warning_msg.format(
        deploy_command_util.DEFAULT_SERVICE,
        '$VERSION_ID-dot-$APP_ID',
        deploy_command_util.MAX_DNS_LABEL_LENGTH))
    self.AssertErrNotContains(
        self.browser_warning_msg.format(deploy_command_util.DEFAULT_SERVICE))

  def testGetAppHostnameLongSubdomain_NoDeploy(self):
    """Test GetAppHostname with long subdomain, deploy=False."""
    # If the service isn't being deployed, warn only that SSL invalid
    hostname = deploy_command_util.GetAppHostname(app=self.app,
                                                  service=self.service_id,
                                                  version=self.version_id,
                                                  use_ssl=appinfo.SECURE_HTTPS,
                                                  deploy=False)
    self.AssertErrNotContains(self.deployment_warning_msg.format(
        self.service_id,
        '$VERSION_ID-dot-$SERVICE_ID-dot-$APP_ID',
        deploy_command_util.MAX_DNS_LABEL_LENGTH))
    self.AssertErrContains(self.browser_warning_msg.format(self.service_id))
    self.assertEqual(hostname,
                     'https://{0}.{1}.{2}.appspot.com'.format(self.version_id,
                                                              self.service_id,
                                                              self.app_id))


class NonDefaultHostnameTest(sdk_test_base.SdkBase,
                             test_case.WithOutputCapture):

  def SetUp(self):
    self.version_id = 'versionid'  # 33 chars
    self.service_id = 'serviceid'  # 33 chars
    self.app_id = 'appid'  # 29 chars
    self.messages = core_apis.GetMessagesModule(APPENGINE_API,
                                                APPENGINE_API_VERSION)
    self.app = self.messages.Application(
        name='apps/{0}'.format(self.app_id),
        id=self.app_id,
        defaultHostname='{0}.a.b.c.com'.format(self.app_id))

  def testGetAppHostname(self):
    """Test GetAppHostname returns correct hostname."""
    hostname = deploy_command_util.GetAppHostname(app=self.app,
                                                  service=self.service_id,
                                                  version=None,
                                                  use_ssl=appinfo.SECURE_HTTP)
    self.assertEqual(hostname,
                     'http://{0}.{1}.a.b.c.com'.format(self.service_id,
                                                       self.app_id))

  def testGetAppHostnameWithVersion(self):
    """Test GetAppHostname returns correct hostname when version is specified.
    """
    hostname = deploy_command_util.GetAppHostname(app=self.app,
                                                  service=self.service_id,
                                                  version=self.version_id,
                                                  use_ssl=appinfo.SECURE_HTTP)
    self.assertEqual(hostname,
                     'http://{0}.{1}.{2}.a.b.c.com'.format(
                         self.version_id, self.service_id, self.app_id))


class DoPrepareManagedVmsTest(sdk_test_base.WithOutputCapture,
                              sdk_test_base.WithFakeAuth):

  def TearDown(self):
    # Wait for all threads to finish, like the ProgressTracker ticker thread.
    self.JoinAllThreads()

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    self.prepare_mock = self.StartObjectPatch(appengine_client.AppengineClient,
                                              'PrepareVmRuntime')
    self.gae_client = appengine_client.AppengineClient()
    self.StartPatch('time.sleep')

  def Project(self):
    return 'fake-project'

  def testDoPrepareManagedVms(self):
    """Tests that Flex preparation is called."""
    deploy_command_util.DoPrepareManagedVms(self.gae_client)
    self.prepare_mock.assert_called_once()

  def testDoPrepareManagedVms_Failure(self):
    """Tests that Flex preparation failure is handled with a warning."""
    url_error = six.moves.urllib.error.HTTPError(
        'http://www.example.com', 400,
        'HTTP Error 400: Bad Request Unexpected HTTP status 400', {},
        io.BytesIO())
    self.prepare_mock.side_effect = app_util.RPCError(url_error,
                                                      body='Test error')
    deploy_command_util.DoPrepareManagedVms(self.gae_client)
    self.prepare_mock.assert_called_once()
    self.AssertErrContains(
        'WARNING: We couldn\'t validate that your project is ready to deploy '
        'to App Engine Flexible Environment. If deployment fails, please check '
        'the following message and try again:\n'
        'Server responded with code [400]:\n'
        '  HTTP Error 400: Bad Request Unexpected HTTP status 400.\n'
        '  Test error')


class PossiblyEnableFlexTest(sdk_test_base.WithOutputCapture,
                             sdk_test_base.WithFakeAuth):

  def TearDown(self):
    # Wait for all threads to finish, like the ProgressTracker ticker thread.
    self.JoinAllThreads()

  def SetUp(self):
    self.project = 'fakeproject'

  def testPossiblyEnableFlex_Succeeds(self):
    """Test that PossiblyEnableFlex succeeds if EnableServiceIfDisabled does."""
    self.enable_mock = self.StartObjectPatch(enable_api,
                                             'EnableServiceIfDisabled')
    # Assuming no errors thrown, this should succeed.
    deploy_command_util.PossiblyEnableFlex(self.project)
    self.enable_mock.assert_called_once_with(
        self.project, 'appengineflex.googleapis.com')

  def testPossiblyEnableFlex_ListFailure(self):
    """Test that PossiblyEnableFlex proceeds if unable to list services."""
    self.enable_mock = self.StartObjectPatch(enable_api,
                                             'EnableServiceIfDisabled')
    self.enable_mock.side_effect = (
        exceptions.GetServicePermissionDeniedException('message'))
    deploy_command_util.PossiblyEnableFlex(self.project)
    self.AssertErrContains(
        'Unable to verify that the Appengine Flexible API is enabled for '
        'project [fakeproject]. You may not have permission to list enabled '
        'services on this project. If it is not enabled, this may cause '
        'problems in running your deployment. Please ask the project owner to '
        'ensure that the Appengine Flexible API has been enabled and that this '
        'account has permission to list enabled APIs.')
    self.AssertErrNotContains(
        'Note: When deploying with a service account, the Service Management '
        'API needs to be enabled in order to verify that the Appengine '
        'Flexible API is enabled. Please ensure the Service Management API '
        'has been enabled on this project by the project owner.')

  def testPossiblyEnableFlex_ListFailure_ServiceAccount(self):
    """Test that PossiblyEnableFlex proceeds if unable to list services."""
    self.enable_mock = self.StartObjectPatch(enable_api,
                                             'EnableServiceIfDisabled')
    self.enable_mock.side_effect = (
        exceptions.GetServicePermissionDeniedException('message'))
    self.StartObjectPatch(creds.CredentialType, 'FromCredentials',
                          return_value=creds.CredentialType.SERVICE_ACCOUNT)
    deploy_command_util.PossiblyEnableFlex(self.project)
    self.AssertErrContains(
        'Unable to verify that the Appengine Flexible API is enabled for '
        'project [fakeproject]. You may not have permission to list enabled '
        'services on this project. If it is not enabled, this may cause '
        'problems in running your deployment. Please ask the project owner to '
        'ensure that the Appengine Flexible API has been enabled and that this '
        'account has permission to list enabled APIs.')
    self.AssertErrContains(
        'Note: When deploying with a service account, the Service Management '
        'API needs to be enabled in order to verify that the Appengine '
        'Flexible API is enabled. Please ensure the Service Management API '
        'has been enabled on this project by the project owner.')

    self.ClearErr()
    properties.VALUES.auth.disable_credentials.Set(True)
    deploy_command_util.PossiblyEnableFlex(self.project)
    self.AssertErrContains(
        'Unable to verify that the Appengine Flexible API is enabled for '
        'project [fakeproject]. You may not have permission to list enabled '
        'services on this project. If it is not enabled, this may cause '
        'problems in running your deployment. Please ask the project owner to '
        'ensure that the Appengine Flexible API has been enabled and that this '
        'account has permission to list enabled APIs.')

    self.AssertErrNotContains(
        'Note: When deploying with a service account, the Service Management '
        'API needs to be enabled in order to verify that the Appengine '
        'Flexible API is enabled. Please ensure the Service Management API '
        'has been enabled on this project by the project owner.')

  def testPossiblyEnableFlex_EnableServiceFailure(self):
    """Test that PossiblyEnableFlex proceeds if unable to list services."""
    self.enable_mock = self.StartObjectPatch(enable_api,
                                             'EnableServiceIfDisabled')
    self.enable_mock.side_effect = (
        exceptions.EnableServicePermissionDeniedException('message'))
    with self.assertRaisesRegex(
        deploy_command_util.PrepareFailureError,
        r'Enabling the Appengine Flexible API failed on project '
        r'\[fakeproject\]'):
      deploy_command_util.PossiblyEnableFlex(self.project)

  def testPossiblyEnableFlex_EnableServicesGenericError(self):
    """Test that PossiblyEnableFlex proceeds if unable to list services."""
    error_details = [
        {
            '@type': 'type.googleapis.com/google.rpc.DebugInfo',
            'detail': 'Error details.'
        }
    ]
    api_error = http_error.MakeDetailedHttpError(
        code=400, message='Arbitrary message.',
        details=error_details)
    su_client = apitools_mock.Client(
        core_apis.GetClientClass('serviceusage', 'v1'),
        real_client=core_apis.GetClientInstance(
            'serviceusage', 'v1', no_http=True))
    su_client.Mock()
    self.addCleanup(su_client.Unmock)
    su_messages = core_apis.GetMessagesModule('serviceusage', 'v1')
    su_client.services.Get.Expect(
        su_messages.ServiceusageServicesGetRequest(
            name='projects/fakeproject/services/appengineflex.googleapis.com',),
        response=None,
        exception=api_error)
    regex = (r'Error \[400\] Arbitrary message.\n'
             'Detailed error information:\n'
             '- \'@type\': type.googleapis.com/google.rpc.DebugInfo\n'
             '  detail: Error details.')
    with self.assertRaisesRegex(api_lib_exceptions.HttpException, regex):
      deploy_command_util.PossiblyEnableFlex(self.project)


class ShouldUseRuntimeBuildersTest(sdk_test_base.SdkBase):

  ALWAYS = runtime_builders.RuntimeBuilderStrategy.ALWAYS
  WHITELIST_GA = runtime_builders.RuntimeBuilderStrategy.WHITELIST_GA

  # The whitelist is defined in googlecloudsdk.api_lib.app.runtime_builders
  WHITELISTED_RUNTIME = 'test-ga'
  NON_WHITELISTED_RUNTIME = 'not-whitelisted'

  def _RunTest(self, requires_image, strategy, runtime, needs_dockerfile):
    # Flex runtimes always require an image; *implicit* standard runtimes do
    # not (that is, env=None, not env='standard').
    env = 'flex' if requires_image else None
    service = Config(module='my-module', runtime=runtime, tmpdir=self.temp_path,
                     env=env)

    return deploy_command_util.ShouldUseRuntimeBuilders(service, strategy,
                                                        needs_dockerfile)

  def testShouldUseRuntimeBuilders_NoRequiresImage(self):
    # TODO(b/64121645): Parameterize this test
    for strategy in (self.WHITELIST_GA, self.ALWAYS):
      for runtime in (self.NON_WHITELISTED_RUNTIME, self.WHITELISTED_RUNTIME):
        for needs_dockerfile in (True, False):
          self.assertFalse(
              self._RunTest(False, strategy, runtime, needs_dockerfile),
              'If an app doesn\'t requires an image to be build, it should '
              'NEVER use runtime builders.')

  def testShouldUseRuntimeBuilders_RequiresImageAlwaysStrategy(self):
    # TODO(b/64121645): Parameterize this test
    for runtime in (self.NON_WHITELISTED_RUNTIME, self.WHITELISTED_RUNTIME):
      self.assertTrue(
          self._RunTest(True, self.ALWAYS, runtime, True),
          'With strategy ALWAYS, any non-custom runtime should use runtime '
          'builders.')

  def testShouldUseRuntimeBuilders_RequiresImageWhitelistStrategy(self):
    # TODO(b/64121645): Parameterize this test
    for needs_dockerfile in (True, False):
      self.assertTrue(
          self._RunTest(True, self.WHITELIST_GA, self.WHITELISTED_RUNTIME,
                        needs_dockerfile),
          'A whitelisted runtime should use runtime builders.')
      self.assertFalse(
          self._RunTest(True, self.WHITELIST_GA, self.NON_WHITELISTED_RUNTIME,
                        needs_dockerfile),
          'A non-whitelisted runtime should NOT use runtime builders.')

  def testShouldUseRuntimeBuilders_RequiresImageCustomRuntime(self):
    # TODO(b/64121645): Parameterize this test
    for strategy in (self.WHITELIST_GA, self.ALWAYS):
      self.assertTrue(
          self._RunTest(True, strategy, 'custom', True),
          'A custom runtime that requires a Dockerfile should use runtime '
          'builders.')
      self.assertFalse(
          self._RunTest(True, strategy, 'custom', False),
          'A custom runtime that already has a Dockerfile should not use '
          'runtime builders.')


class NeedsDockerfileTest(sdk_test_base.SdkBase):
  """Tests _NeedsDockerfile.

  Here's a chart of the inputs and expected outputs:

   runtime | dockerfile | cloudbuild | output
  ---------+------------+------------+---------
    canned |          n |          n | True
    canned |          n |          y | has cloudbuild error
    canned |          y |          n | has dockerfile error
    canned |          y |          y | has dockerfile error*
    custom |          n |          n | missing dockerfile error
    custom |          n |          y | True
    custom |          y |          n | False
    custom |          y |          y | has both files error

  * This could be either "has Dockerfile" or "has cloudbuild.yaml" error in
    theory, but in practice we want to direct users toward Dockerfiles.
  """

  CUSTOM = 'custom'
  CANNED = 'python'

  def _MakeSourceDir(self, has_dockerfile=False, has_cloudbuild_yaml=False):
    source_dir = os.path.join(self.temp_path, str(uuid.uuid1()))
    files.MakeDir(source_dir)

    if has_dockerfile:
      self.Touch(source_dir, 'Dockerfile')
    if has_cloudbuild_yaml:
      self.Touch(source_dir, 'cloudbuild.yaml')
    return source_dir

  def _RunTest(self, runtime, has_dockerfile, has_cloudbuild_yaml):
    return deploy_command_util._NeedsDockerfile(
        Config(module='my-module', runtime=runtime, env='flex',
               tmpdir=self.temp_path),
        self._MakeSourceDir(has_dockerfile=has_dockerfile,
                            has_cloudbuild_yaml=has_cloudbuild_yaml))

  def testNeedsDockerfile_CannedRuntimeNeedsDockerfile(self):
    self.assertTrue(
        self._RunTest(self.CANNED, has_dockerfile=False,
                      has_cloudbuild_yaml=False),
        'Canned runtime with neither a Dockerfile nor cloudbuild.yaml needs a '
        'Dockerfile.')

  def testNeedsDockerfile_CannedInvalidFilesError(self):
    """Tests scenarios when a Dockerfile must be generated."""
    # TODO(b/64121645): Use parameterized tests when available
    for has_cloudbuild_yaml in (True, False):
      with self.assertRaises(
          deploy_command_util.DockerfileError,
          msg=('Canned runtime with a Dockerfile should result in an error.')):
        self._RunTest(self.CANNED, has_dockerfile=True,
                      has_cloudbuild_yaml=has_cloudbuild_yaml)

    with self.assertRaises(
        deploy_command_util.CloudbuildYamlError,
        msg=('Canned runtime with cloudbuild.yaml should result in an error.')):
      self._RunTest(self.CANNED, has_dockerfile=False, has_cloudbuild_yaml=True)

  def testNeedsDockerfile_CustomInvalidFilesError(self):
    """Tests scenarios when a Dockerfile must be generated."""
    with self.assertRaises(
        deploy_command_util.NoDockerfileError,
        msg=('Custom runtime with neither a Dockerfile nor a cloudbuild.yaml '
             'should result in an error.')):
      self._RunTest(self.CUSTOM, has_dockerfile=False,
                    has_cloudbuild_yaml=False)

    with self.assertRaises(
        deploy_command_util.CustomRuntimeFilesError,
        msg=('Custom runtime with both a Dockerfile and a cloudbuild.yaml '
             'should result in an error.')):
      self._RunTest(self.CUSTOM, has_dockerfile=True, has_cloudbuild_yaml=True)

  def testNeedsDockerfile_CustomRuntimeMayNeedDockerfile(self):
    self.assertTrue(
        self._RunTest(self.CUSTOM, has_dockerfile=False,
                      has_cloudbuild_yaml=True),
        'Custom runtime should need a Dockerfile if it has only a '
        'cloudbuild.yaml')

    self.assertFalse(
        self._RunTest(self.CUSTOM, has_dockerfile=True,
                      has_cloudbuild_yaml=False),
        'Custom runtime should not need a Dockerfile if it has one.')

  def testNeedsDockerfile_CustomWithDockerfile(self):
    """Tests scenarios when a Dockerfile must be generated."""
    self.assertFalse(self._RunTest(self.CUSTOM, has_dockerfile=True,
                                   has_cloudbuild_yaml=False))


if __name__ == '__main__':
  test_case.main()
