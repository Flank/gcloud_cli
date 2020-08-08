# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform versions create tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml_engine import versions_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
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
                    prediction_class=None,
                    package_uris=None,
                    response=None,
                    accelerator=None,
                    service_account=None,
                    explain_config=None,
                    container=None,
                    routes=None):
    if framework:
      framework = self.short_msgs.Version.FrameworkValueValuesEnum(framework)
    op = self.msgs.GoogleLongrunningOperation(name='opId')
    self.client.projects_models_versions.Create.Expect(
        request=self.versions._MakeCreateRequest(
            parent='projects/{}/models/modelId'.format(self.Project()),
            version=self.short_msgs.Version(
                name='versionId',
                acceleratorConfig=accelerator,
                deploymentUri=deployment_uri,
                runtimeVersion=runtime_version,
                manualScaling=manual_scaling,
                description=description,
                autoScaling=auto_scaling,
                labels=labels,
                machineType=machine_type,
                framework=framework,
                predictionClass=prediction_class,
                packageUris=package_uris or [],
                pythonVersion=python_version,
                serviceAccount=service_account,
                explanationConfig=explain_config,
                container=container,
                routes=routes)),
        response=response or op)

  def testCreate(self, module_name):
    self._ExpectCreate()
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def _MakeLabels(self, labels):
    labels_cls = self.short_msgs.Version.LabelsValue
    return labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key=key, value=value) for key, value in
        sorted(labels.items())
    ])

  def testCreateLabels(self, module_name):
    self._ExpectCreate(
        labels=self._MakeLabels({'key1': 'value1', 'key2': 'value2'}))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --labels key1=value1,key2=value2'.format(
            module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateRuntimeVersion(self, module_name):
    self._ExpectCreate(runtime_version='0.12')
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --runtime-version 0.12'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateDescription(self, module_name):
    self._ExpectCreate(description='Foo')
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --description "Foo"'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateAsync(self, module_name):
    self._ExpectCreate()
    self._ExpectOperationPolling(is_async=True)
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file --async'.format(module_name))
    self.AssertErrNotContains(
        'Creating version (this might take a few minutes)...')

  def testCreateFromConfig(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))

  # Since we defer validation of the actual autoScaling values to the API,
  # here we only test the expect behavior of the surface namely that it parses
  # the yaml values correctly and passes them to the API.
  # Specifically, the API is expected to raise errors for
  # the following conditions (based on current validation rules):
  # - invalid autoscaling field names
  # - both automaticScaling and manualScaling specified in same config
  # - invalid values for minNodes
  def testCreateFromConfigWithAutoScaling(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))

  def testCreateFromConfigCommandLineOverrides(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {} --origin gs://path/to/file '
             '--runtime-version 0.12'.format(module_name, yaml_path))

  def testCreateMissingDeploymentUri(self, module_name):
    with self.AssertRaisesExceptionMatches(
        versions_util.InvalidArgumentCombinationError,
        'Either `--origin` must be provided or `deploymentUri` must be '
        'provided in the file given by `--config`.'):
      self.Run(
          '{} versions create versionId --model modelId'.format(module_name))

  def testCreate_LocalPathNoStagingBucket(self, module_name):
    """Tests an error from an invalid combination of flags."""
    with self.assertRaisesRegex(exceptions.Error,
                                r'If --origin is provided as a local path, '
                                r'--staging-bucket must be given as well\.'):
      self.Run('{} versions create versionId --model modelId '
               '--origin '.format(module_name) + self.temp_path)

  def testCreate_LocalPath(self, module_name):
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

    self.Run('{} versions create versionId --model modelId '
             '--staging-bucket gs://bucket/ '
             '--origin '.format(module_name) + self.temp_path)

    copy_file_mock.assert_called_once_with(
        os.path.join(self.temp_path, 'file'),
        storage_util.ObjectReference.FromUrl(
            'gs://bucket/' + self._SHA256_SUM + '/file'))

  def testCreateFrameworkFlag(self, module_name):
    self._ExpectCreate(framework='XGBOOST')
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --framework xgboost'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateFrameworkFromConfig(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFlag(self, module_name):
    self._ExpectCreate(python_version='2.7')
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --python-version 2.7'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testPythonVersionFromConfig(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateMachineTypeFlag(self, module_name):
    self._ExpectCreate(machine_type='mls1-c1-m2')
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file --machine-type=mls1-c1-m2'.format(
                 module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateNewMachineTypeWithAccelerator(self, module_name):
    accelerator_config = self.msgs.GoogleCloudMlV1AcceleratorConfig(
        count=2,
        type=(self.msgs.GoogleCloudMlV1AcceleratorConfig.TypeValueValuesEnum
              .NVIDIA_TESLA_K80))
    self._ExpectCreate(
        accelerator=accelerator_config, machine_type='n1-standard-4')
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--machine-type=n1-standard-4 '
             '--accelerator=type=nvidia-tesla-k80,count=2'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  def testCreateAcceleratorFlag(self, module_name):
    accelerator_config = self.msgs.GoogleCloudMlV1AcceleratorConfig(
        count=2,
        type=(self.msgs.GoogleCloudMlV1AcceleratorConfig.TypeValueValuesEnum
              .NVIDIA_TESLA_K80))
    self._ExpectCreate(accelerator=accelerator_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--accelerator type=nvidia-tesla-k80,count=2'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')


class CreateGaTest(CreateTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CreateGaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.GA


class CreateBetaTest(CreateTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(CreateBetaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testUserCode(self, module_name):
    self._ExpectCreate(prediction_class='my_package.SequenceModel',
                       package_uris=['gs://path/to/file', 'gs://path/to/file2'])
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--prediction-class my_package.SequenceModel '
             '--package-uris gs://path/to/file,gs://path/to/file2'.format(
                 module_name))

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testUserCode_ConfigFile(self, module_name):
    yaml_contents = """\
        predictionClass: my_package.SequenceModel
        packageUris:
        - gs://path/to/file
        - gs://path/to/file2
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(prediction_class='my_package.SequenceModel',
                       package_uris=['gs://path/to/file', 'gs://path/to/file2'])
    self._ExpectOperationPolling()
    self.Run(('{0} versions create versionId --model modelId '
              '--origin gs://path/to/file '
              '--config {1}').format(module_name, yaml_path))

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testServiceAccountFlag(self, module_name):
    self._ExpectCreate(service_account='testsa@google.com')
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file --service-account testsa@google.com'
             .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testServiceAccountFromConfig(self, module_name):
    yaml_contents = """\
        description: dummy description
        deploymentUri: gs://foo/bar
        runtimeVersion: '1.0'
        serviceAccount: testsa@google.com
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    self._ExpectCreate(runtime_version='1.0', deployment_uri='gs://foo/bar',
                       description='dummy description',
                       service_account='testsa@google.com')
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilityIntegratedGradients(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    ig_config = self.msgs.GoogleCloudMlV1IntegratedGradientsAttribution()
    ig_config.numIntegralSteps = 42
    explain_config.integratedGradientsAttribution = ig_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method integrated-gradients '
             '--num-integral-steps 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilitySamplingShap(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    shap_config = self.msgs.GoogleCloudMlV1SampledShapleyAttribution()
    shap_config.numPaths = 42
    explain_config.sampledShapleyAttribution = shap_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method sampled-shapley '
             '--num-paths 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilityXrai(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    xrai_config = self.msgs.GoogleCloudMlV1XraiAttribution()
    xrai_config.numIntegralSteps = 42
    explain_config.xraiAttribution = xrai_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method xrai '
             '--num-integral-steps 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')


class CreateAlphaTest(CreateTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(CreateAlphaTest, self).SetUp()
    self.track = calliope_base.ReleaseTrack.ALPHA

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testPythonVersionFlag(self, module_name):
    self._ExpectCreate(python_version='2.7')
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file --python-version 2.7'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testPythonVersionFromConfig(self, module_name):
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
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilityIntegratedGradients(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    ig_config = self.msgs.GoogleCloudMlV1IntegratedGradientsAttribution()
    ig_config.numIntegralSteps = 42
    explain_config.integratedGradientsAttribution = ig_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method integrated-gradients '
             '--num-integral-steps 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilityXrai(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    xrai_config = self.msgs.GoogleCloudMlV1XraiAttribution()
    xrai_config.numIntegralSteps = 42
    explain_config.xraiAttribution = xrai_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method xrai '
             '--num-integral-steps 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateExplainabilitySamplingShap(self, module_name):
    explain_config = self.msgs.GoogleCloudMlV1ExplanationConfig()
    shap_config = self.msgs.GoogleCloudMlV1SampledShapleyAttribution()
    shap_config.numPaths = 42
    explain_config.sampledShapleyAttribution = shap_config
    self._ExpectCreate(explain_config=explain_config)
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--origin gs://path/to/file '
             '--explanation-method sampled-shapley '
             '--num-paths 42'.format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateFromConfigWithContainers(self, module_name):
    yaml_contents = """\
        container:
          image: tensorflow/serving:2.1.0
          args: [
            "--rest_api_port=8080",
            "--model_name=mymodel",
            "--model_base_path=$(AIP_STORAGE_URI)"
          ]
        routes:
          predict: /v1/models/mymodel:predict
          health: /v1/models/mymodel
    """
    yaml_path = self.Touch(self.temp_path, 'version.yaml', yaml_contents)
    # Must explicitly set deploymentUri to None because the default is not
    # None and it would be unwise to change the default.
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='tensorflow/serving:2.1.0',
            args=[
                '--rest_api_port=8080', '--model_name=mymodel',
                '--model_base_path=$(AIP_STORAGE_URI)'
            ]),
        routes=self.short_msgs.RouteMap(
            predict='/v1/models/mymodel:predict', health='/v1/models/mymodel'))
    self._ExpectOperationPolling()
    self.Run('{} versions create versionId --model modelId '
             '--config {}'.format(module_name, yaml_path))

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithImage(self, module_name):
    self._ExpectCreate(
        deployment_uri='gs://path/to/file',
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0'))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--origin gs://path/to/file '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithSimpleCommand(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            command=['/bin/bash']))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--command=/bin/bash'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithTwoSeparateCommands(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            command=['/bin/bash', '-c']))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--command=/bin/bash --command=-c'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithCsvCommand(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            command=['/bin/bash', '-c']))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--command /bin/bash,-c'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithCsvArgs(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            args=['--arg1', '--arg2=a']))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--args=--arg1,--arg2=a'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithMultipleArgs(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            args=['--arg1', '--arg2=a']))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--args=--arg1 --args=--arg2=a'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithEnvVars(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            env=[
                self.short_msgs.EnvVar(name='A', value='a'),
                self.short_msgs.EnvVar(name='B', value='b')
            ]))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--env-vars=A=a,B=b'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithMultipleEnvVars(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            env=[
                self.short_msgs.EnvVar(name='A', value='a'),
                self.short_msgs.EnvVar(name='B', value='b')
            ]))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--env-vars=A=a --env-vars=B=b'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithSinglePort(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            ports=[self.short_msgs.ContainerPort(containerPort=3141)]))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--ports=3141'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithMultiplePorts(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0',
            ports=[
                self.short_msgs.ContainerPort(containerPort=3141),
                self.short_msgs.ContainerPort(containerPort=1234)
            ]))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--ports=3141,1234'
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithRoutes(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0'),
        routes=self.short_msgs.RouteMap(predict='/a/b/c', health='/x/y/z'))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        '--predict-route=/a/b/c '
        '--health-route=/x/y/z '
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateVersionWithImageNoOrigin(self, module_name):
    self._ExpectCreate(
        deployment_uri=None,
        container=self.short_msgs.ContainerSpec(
            image='gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0'))
    self._ExpectOperationPolling()
    self.Run(
        '{} versions create versionId --model modelId '
        '--image gcr.io/op-beta-walkthrough/tensorflow-serving:2.1.0 '
        .format(module_name))
    self.AssertErrContains('Creating version (this might take a few minutes)')

  # Note: Since we inherit from the GA Base class, we need to override the
  # original test to check for the new error message. This would be better
  # named testCreateMissingDeploymentUriAndImage.
  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateMissingDeploymentUri(self, module_name):
    with self.AssertRaisesExceptionMatches(
        versions_util.InvalidArgumentCombinationError,
        'Either `--origin`, `--image`, or equivalent parameters in a config '
        'file (from `--config`) must be specified.'):
      self.Run(
          '{} versions create versionId --model modelId'.format(module_name))

  @parameterized.parameters('ml-engine', 'ai-platform')
  def testCreateWithCommandAndArgsButNotImage(self, module_name):
    with self.AssertRaisesExceptionMatches(
        ValueError,
        '--image was not provided, but other container related flags were '
        'specified. Please specify --image or remove the following flags: '
        '--args, --command'):
      self.Run(
          '{} versions create versionId --model modelId '
          '--command /bin/bash --args=--a,--b'.format(module_name))


if __name__ == '__main__':
  test_case.main()
