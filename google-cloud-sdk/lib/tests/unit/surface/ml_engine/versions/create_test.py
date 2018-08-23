# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine versions create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml_engine import versions_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class CreateTestBase(object):

  # SHA256 checksum for string 'file contents'
  _SHA256_SUM = (
      '7bb6f9f7a47a63e684925af3608c059edcc371eb81188c48c9714896fb1091fd')

  def SetUp(self):
    self.StartPatch('time.sleep')
    self.model_ref = resources.REGISTRY.Parse(
        'modelId',
        params={'projectsId': self.Project()},
        collection='ml.projects.models')
    self.versions = versions_api.VersionsClient()

  def _ExpectOperationPolling(self, is_async=False):
    if not is_async:
      self.client.projects_operations.Get.Expect(
          request=self.msgs.MlProjectsOperationsGetRequest(
              name='projects/{}/operations/opId'.format(self.Project())),
          response=self.msgs.GoogleLongrunningOperation(
              name='opName', done=True))

  def _ExpectCreate(self,
                    runtime_version=None,
                    deployment_uri='gs://path/to/file',
                    description=None,
                    manual_scaling=None,
                    auto_scaling=None,
                    labels=None,
                    machine_type=None,
                    framework=None,
                    python_version=None,
                    model_class=None,
                    package_uris=None,
                    response=None):
    if framework:
      framework = self.short_msgs.Version.FrameworkValueValuesEnum(framework)
    op = self.msgs.GoogleLongrunningOperation(name='opId')
    self.client.projects_models_versions.Create.Expect(
        request=self.versions._MakeCreateRequest(
            parent='projects/{}/models/modelId'.format(self.Project()),
            version=self.short_msgs.Version(
                name='versionId',
                deploymentUri=deployment_uri,
                runtimeVersion=runtime_version,
                manualScaling=manual_scaling,
                description=description,
                autoScaling=auto_scaling,
                labels=labels,
                machineType=machine_type,
                framework=framework,
                modelClass=model_class,
                packageUris=package_uris or [],
                pythonVersion=python_version)),
        response=response or op)

  def testCreate(self):
    self._ExpectCreate()
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def _MakeLabels(self, labels):
    labels_cls = self.short_msgs.Version.LabelsValue
    return labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key=key, value=value) for key, value in
        sorted(labels.items())
    ])

  def testCreateLabels(self):
    self._ExpectCreate(
        labels=self._MakeLabels({'key1': 'value1', 'key2': 'value2'}))
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --labels key1=value1,key2=value2')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateRuntimeVersion(self):
    self._ExpectCreate(runtime_version='0.12')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --runtime-version 0.12')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateDescription(self):
    self._ExpectCreate(description='Foo')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --description "Foo"')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateAsync(self):
    self._ExpectCreate()
    self._ExpectOperationPolling(is_async=True)
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --async')
    self.AssertErrNotContains(
        'Creating version (this might take a few minutes)...')

  def testCreateFromConfig(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        manualScaling:
          nodes: 10
        labels:
          key: value
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       manual_scaling=self.short_msgs.ManualScaling(nodes=10),
                       labels=self._MakeLabels({'key': 'value'}))
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))

  # Since we defer validation of the actual autoScaling values to the API,
  # here we only test the expect behavior of the surface namely that it parses
  # the yaml values correctly and passes them to the API.
  # Specifically, the API is expected to raise errors for
  # the following conditions (based on current validation rules):
  # - invalid autoscaling field names
  # - both automaticScaling and manualScaling specified in same config
  # - invalid values for minNodes
  def testCreateFromConfigWithAutoScaling(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        autoScaling:
          minNodes: 10
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       auto_scaling=self.short_msgs.AutoScaling(minNodes=10))
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))

  def testCreateFromConfigCommandLineOverrides(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        manualScaling:
          nodes: 10
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='0.12',
                       deployment_uri='gs://path/to/file',
                       description='dummy description',
                       manual_scaling=self.short_msgs.ManualScaling(nodes=10))
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {} --origin gs://path/to/file '
             '--runtime-version 0.12'.format(yaml_path))

  def testCreateMissingDeploymentUri(self):
    with self.AssertRaisesExceptionMatches(
        versions_util.InvalidArgumentCombinationError,
        'Either `--origin` must be provided or `deploymentUri` must be '
        'provided in the file given by `--config`.'):
      self.Run('ml-engine versions create versionId --model modelId')

  def testCreate_LocalPathNoStagingBucket(self):
    """Tests an error from an invalid combination of flags."""
    with self.assertRaisesRegex(exceptions.Error,
                                r'If --origin is provided as a local path, '
                                r'--staging-bucket must be given as well\.'):
      self.Run('ml-engine versions create versionId --model modelId '
               '--origin ' + self.temp_path)

  def testCreate_LocalPath(self):
    """Tests an error from an invalid combination of flags."""
    self._ExpectCreate(
        deployment_uri='gs://bucket/{}/'.format(self._SHA256_SUM))
    self._ExpectOperationPolling()
    self.Touch(self.temp_path, 'file', contents='file contents')
    object_ = storage_util.GetMessages().Object(bucket='bucket',
                                                name=self._SHA256_SUM + '/file')

    copy_file_mock = self.StartObjectPatch(storage_api.StorageClient,
                                           'CopyFileToGCS')
    copy_file_mock.return_value = object_

    self.Run('ml-engine versions create versionId --model modelId '
             '--staging-bucket gs://bucket/ '
             '--origin ' + self.temp_path)

    copy_file_mock.assert_called_once_with(
        storage_util.BucketReference.FromBucketUrl('gs://bucket/'),
        os.path.join(self.temp_path, 'file'), self._SHA256_SUM + '/file')

  def testCreateFrameworkFlag(self):
    self._ExpectCreate(framework='XGBOOST')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --framework xgboost')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateFrameworkFromConfig(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        framework: SCIKIT_LEARN
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       framework='SCIKIT_LEARN')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFlag(self):
    self._ExpectCreate(python_version='2.7')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --python-version 2.7')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFromConfig(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        pythonVersion: '3.4'
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       python_version='3.4')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')


class CreateGaTest(CreateTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CreateGaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.GA


class CreateBetaTest(CreateTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(CreateBetaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateMachineTypeFlag(self):
    self._ExpectCreate(machine_type='mls1-c1-m2')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --machine-type=mls1-c1-m2')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateInvalidMachineType(self):

    class ErrorResponse(object):

      class Error(object):
        message = 'Invalid machine_type: mls1-c1-m4'

      done = True
      response = ''
      error = Error

    self._ExpectCreate(machine_type='mls1-c1-m4', response=ErrorResponse)
    error_msg = r'Invalid machine_type: mls1-c1-m4'
    with self.assertRaisesRegex(waiter.OperationError, error_msg):
      self.Run('ml-engine versions create versionId --model modelId '
               '--origin gs://path/to/file --machine-type=mls1-c1-m4')


class CreateAlphaTest(CreateTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CreateAlphaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateMachineTypeFlag(self):
    self._ExpectCreate(machine_type='mls1-c1-m2')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --machine-type=mls1-c1-m2')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateMachineTypeFromConfig(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        machineType: 'mls1-c1-m2'
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(
        runtime_version='1.0',
        deployment_uri='gs://foo/bar',
        description='dummy description',
        machine_type='mls1-c1-m2')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFlag(self):
    self._ExpectCreate(python_version='2.7')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file --python-version 2.7')
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFromConfig(self):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        pythonVersion: '3.4'
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       python_version='3.4')
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--config {}'.format(yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateInvalidMachineType(self):

    class ErrorResponse(object):

      class Error(object):
        message = 'Invalid machine_type: mls1-c1-m4'

      done = True
      response = ''
      error = Error

    self._ExpectCreate(machine_type='mls1-c1-m4', response=ErrorResponse)
    error_msg = r'Invalid machine_type: mls1-c1-m4'
    with self.assertRaisesRegex(waiter.OperationError, error_msg):
      self.Run('ml-engine versions create versionId --model modelId '
               '--origin gs://path/to/file --machine-type=mls1-c1-m4')

  def testUserCode(self):
    self._ExpectCreate(model_class='my_package.SequenceModel',
                       package_uris=['gs://path/to/file', 'gs://path/to/file2'])
    self._ExpectOperationPolling()
    self.Run('ml-engine versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--model-class my_package.SequenceModel '
             '--package-uris gs://path/to/file,gs://path/to/file2')

  def testUserCode_ConfigFile(self):
    yaml_contents = """\
        modelClass: my_package.SequenceModel
        packageUris:
        - gs://path/to/file
        - gs://path/to/file2
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(model_class='my_package.SequenceModel',
                       package_uris=['gs://path/to/file', 'gs://path/to/file2'])
    self._ExpectOperationPolling()
    self.Run(('ml-engine versions create versionId --model modelId '
              '--origin gs://path/to/file '
              '--config {}').format(yaml_path))


if __name__ == '__main__':
  test_case.main()
