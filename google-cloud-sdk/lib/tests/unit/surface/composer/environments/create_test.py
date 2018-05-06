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
"""Unit tests for environments create."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
import six


class EnvironmentsCreateTest(base.EnvironmentsUnitTest):

  def SetUp(self):
    # pylint: disable=invalid-name
    self.NODE_COUNT = 5
    self.LOCATION_SHORT_NAME = 'us-central1-a'
    self.LOCATION_RELATIVE_NAME = 'projects/{}/zones/{}'.format(
        self.TEST_PROJECT, self.LOCATION_SHORT_NAME)
    self.MACHINE_TYPE_SHORT_NAME = 'n1-standard-1'
    self.MACHINE_TYPE_RELATIVE_NAME = (
        'projects/{}/zones/{}/machineTypes/{}'.format(
            self.TEST_PROJECT, self.LOCATION_SHORT_NAME,
            self.MACHINE_TYPE_SHORT_NAME))
    self.NETWORK_SHORT_NAME = 'test-net'
    self.NETWORK_RELATIVE_NAME = 'projects/{}/global/networks/{}'.format(
        self.TEST_PROJECT, self.NETWORK_SHORT_NAME)
    self.SUBNETWORK_SHORT_NAME = 'test-subnet'
    self.SUBNETWORK_RELATIVE_NAME = (
        'projects/{}/regions/{}/subnetworks/{}'.format(
            self.TEST_PROJECT, self.TEST_LOCATION,
            self.SUBNETWORK_SHORT_NAME))
    self.DEFAULT_DISK_SIZE_GB = 100
    self.NODE_CONFIG = api_util.GetMessagesModule().NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    self.CONFIG = api_util.GetMessagesModule().EnvironmentConfig(
        nodeCount=self.NODE_COUNT, nodeConfig=self.NODE_CONFIG)
    self.LABELS_DICT = {'label1': 'value1', 'label2': 'value2'}
    self.LABELS_STR = ','.join(
        '{}={}'.format(k, v) for k, v in six.iteritems(self.LABELS_DICT))
    self.ENV_VARS_DICT = {'VAR1': 'value 1', 'VAR2': 'value 2'}
    self.ENV_VARS_STR = ','.join(
        '{}={}'.format(k, v) for k, v in six.iteritems(self.ENV_VARS_DICT))
    self.AIRFLOW_CONFIG_OVERRIDES_DICT = {
        'core-load_examples': 'True',
        'webserver-expose_config': 'False'
    }
    self.AIRFLOW_CONFIG_OVERRIDES_STR = ','.join(
        '{}={}'.format(k, v)
        for k, v in six.iteritems(self.AIRFLOW_CONFIG_OVERRIDES_DICT))
    self.SERVICE_ACCOUNT = 'foo@bar.gserviceaccount.com'
    self.OAUTH_SCOPES = ['https://www.googleapis.com/auth/scope1',
                         'https://www.googleapis.com/auth/scope2']
    self.TAGS = ['tag1', 'tag2']

    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)

  def testSuccessfulCreate_synchronous(self):
    """Tests a successful synchronous creation.

    The progress tracker should be activated and terminated.
    """
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    successful_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=successful_op)

    self.RunEnvironments('create', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, self.TEST_ENVIRONMENT_ID)
    self.AssertErrMatches(
        r'^<START PROGRESS TRACKER>Waiting for \[{}] to be created with \[{}]'
        r'\s*^<END PROGRESS TRACKER>SUCCESS'.format(self.TEST_ENVIRONMENT_NAME,
                                                    self.TEST_OPERATION_NAME))

  def testFailedCreate_synchronous(self):
    """Tests a failed synchronous creation.

    A command_util.Error or a subclass thereof hould be raised.
    """
    # pylint: disable=invalid-name
    ERROR_DESCRIPTION = 'ERROR DESCRIPTION'
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    failed_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=True,
        error=self.messages.Status(message=ERROR_DESCRIPTION))
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    self.ExpectOperationGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        response=failed_op)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Error creating \[{}]: Operation \[{}] failed: {}'.format(
            self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME,
            ERROR_DESCRIPTION)):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           self.TEST_ENVIRONMENT_ID)

  def testSuccessfulAsyncCreateWithCustomConfiguration_network(self):
    """Tests a successful asynchronous creation with a custom network."""
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.CONFIG,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION, '--node-count',
        str(self.NODE_COUNT), '--zone', self.LOCATION_RELATIVE_NAME,
        '--machine-type', self.MACHINE_TYPE_RELATIVE_NAME, '--network',
        self.NETWORK_RELATIVE_NAME, '--subnetwork',
        self.SUBNETWORK_RELATIVE_NAME, '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulAsyncCreateWithCustomConfiguration_subnetwork(self):
    """Tests a successful asynchronous creation with a custom subnetwork."""
    node_config = api_util.GetMessagesModule().NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeCount=self.NODE_COUNT, nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION, '--node-count',
        str(self.NODE_COUNT), '--zone', self.LOCATION_RELATIVE_NAME,
        '--machine-type', self.MACHINE_TYPE_RELATIVE_NAME, '--network',
        self.NETWORK_RELATIVE_NAME, '--subnetwork',
        self.SUBNETWORK_RELATIVE_NAME, '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulAsyncCreateWithLabels(self):
    """Test that creating an environment with labels works."""
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        labels=self.LABELS_DICT,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--labels', self.LABELS_STR,
                                     self.TEST_ENVIRONMENT_ID, '--async')
    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Create in progress for environment \[{}] with operation \[{}]'
        .format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testSuccessfulAsyncCreateWithEnvVariables(self):
    """Test that user-provided env variables are conveyed in the API call."""
    # pylint: disable=invalid-name
    SoftwareConfig = api_util.GetMessagesModule().SoftwareConfig

    software_config = SoftwareConfig(
        envVariables=SoftwareConfig.EnvVariablesValue(additionalProperties=[
            SoftwareConfig.EnvVariablesValue.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems(self.ENV_VARS_DICT)
        ]))
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--env-variables', self.ENV_VARS_STR,
                                     self.TEST_ENVIRONMENT_ID, '--async')
    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Create in progress for environment \[{}] with operation \[{}]'
        .format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testSuccessfulAsyncCreateWithAirflowConfigOverrides(self):
    """Test that Airflow config property overrides are conveyed to the API."""
    # pylint: disable=invalid-name
    SoftwareConfig = api_util.GetMessagesModule().SoftwareConfig
    AirflowConfigOverrides = SoftwareConfig.AirflowConfigOverridesValue

    software_config = SoftwareConfig(
        airflowConfigOverrides=AirflowConfigOverrides(additionalProperties=[
            AirflowConfigOverrides.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems(self.AIRFLOW_CONFIG_OVERRIDES_DICT)
        ]))
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--airflow-configs',
        self.AIRFLOW_CONFIG_OVERRIDES_STR, self.TEST_ENVIRONMENT_ID, '--async')
    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Create in progress for environment \[{}] with operation '
        r'\[{}]'.format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testCreateWithoutUserProvidedConfigValues(self):
    """Test that creating an environment with minimal config values works."""
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testCreateAlreadyExists(self):
    """Tests a creation attempt when the environment already exists.

    There should be an HTTP 409 ALREADY EXISTS
    """
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.CONFIG,
        exception=http_error.MakeHttpError(code=409, message='ALREADY_EXISTS'))

    with self.AssertRaisesExceptionMatches(api_exceptions.HttpException,
                                           'ALREADY_EXISTS'):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--node-count',
                           str(self.NODE_COUNT), '--zone',
                           self.LOCATION_RELATIVE_NAME, '--machine-type',
                           self.MACHINE_TYPE_RELATIVE_NAME, '--network',
                           self.NETWORK_RELATIVE_NAME, '--subnetwork',
                           self.SUBNETWORK_RELATIVE_NAME,
                           self.TEST_ENVIRONMENT_ID)

  def testNameValidation(self):
    """Test that environment name validation fails fast."""
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Invalid environment name'):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, 'foo_bar')

  def testMultipleAirflowConfigsMerged(self):
    """Test merging when --airflow-configs is provided many times."""
    # pylint: disable=invalid-name
    SoftwareConfig = api_util.GetMessagesModule().SoftwareConfig
    AirflowConfigOverrides = SoftwareConfig.AirflowConfigOverridesValue

    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = SoftwareConfig(
        airflowConfigOverrides=AirflowConfigOverrides(additionalProperties=[
            AirflowConfigOverrides.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems({
                'a': '1',
                'b': '2',
                'c': '3',
                'd': '4'
            })
        ]))
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    self.RunEnvironments('create', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, '--airflow-configs', 'a=1,b=2',
                         '--airflow-configs', 'c=3,d=4',
                         self.TEST_ENVIRONMENT_ID, '--async')

  def testMultipleEnvVarsMerged(self):
    """Test merging when --env-variables is provided many times."""
    # pylint: disable=invalid-name
    SoftwareConfig = api_util.GetMessagesModule().SoftwareConfig

    software_config = SoftwareConfig(
        envVariables=SoftwareConfig.EnvVariablesValue(additionalProperties=[
            SoftwareConfig.EnvVariablesValue.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems({
                'a': '1',
                'b': '2',
                'c': '3',
                'd': '4'
            })
        ]))
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    self.RunEnvironments('create', '--project', self.TEST_PROJECT, '--location',
                         self.TEST_LOCATION, '--env-variables', 'a=1,b=2',
                         '--env-variables', 'c=3,d=4', self.TEST_ENVIRONMENT_ID,
                         '--async')

  def testServiceAccount(self):
    node_config = api_util.GetMessagesModule().NodeConfig(
        serviceAccount=self.SERVICE_ACCOUNT,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT,
        '--location', self.TEST_LOCATION,
        '--service-account', self.SERVICE_ACCOUNT,
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testOauthScopes(self):
    node_config = api_util.GetMessagesModule().NodeConfig(
        oauthScopes=self.OAUTH_SCOPES,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT,
        '--location', self.TEST_LOCATION,
        '--oauth-scopes', ','.join(self.OAUTH_SCOPES),
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testTags(self):
    node_config = api_util.GetMessagesModule().NodeConfig(
        tags=self.TAGS,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT,
        '--location', self.TEST_LOCATION,
        '--tags', ','.join(self.TAGS),
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testZoneExpansion(self):
    """Tests that if --zone is provided as a short name, it is expanded.
    """
    node_config = api_util.GetMessagesModule().NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION,
        '--zone', self.LOCATION_SHORT_NAME,
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testMachineTypeExpansion(self):
    """Tests that if --machine-type is provided as a short name, it is expanded.
    """
    node_config = api_util.GetMessagesModule().NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION,
        '--zone', self.LOCATION_SHORT_NAME,
        '--machine-type', self.MACHINE_TYPE_SHORT_NAME,
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testNetworkExpansion(self):
    """Tests that if --network is provided as a short name, it is expanded.
    """
    node_config = api_util.GetMessagesModule().NodeConfig(
        network=self.NETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION,
        '--network', self.NETWORK_SHORT_NAME,
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testSubnetworkExpansion(self):
    """Tests that if --subnetwork is provided as a short name, it is expanded.
    """
    node_config = api_util.GetMessagesModule().NodeConfig(
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION,
        '--network', self.NETWORK_SHORT_NAME,
        '--subnetwork', self.SUBNETWORK_SHORT_NAME,
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testUrlsReducedToRelativeNames(self):
    """Tests that fully-qualified URLs are provided, they become relative names.
    """
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.CONFIG,
        response=self.running_op)

    endpoint = 'https://www.googleapis.com/compute/v1/'
    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION, '--node-count',
        str(self.NODE_COUNT), '--zone', endpoint + self.LOCATION_RELATIVE_NAME,
        '--machine-type', endpoint + self.MACHINE_TYPE_RELATIVE_NAME,
        '--network', endpoint + self.NETWORK_RELATIVE_NAME, '--subnetwork',
        endpoint + self.SUBNETWORK_RELATIVE_NAME, '--async',
        self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testCustomDiskSize(self):
    """Tests that a non-default --disk-size can be used."""
    disk_size_gb = 123
    disk_size_kb = disk_size_gb << 20
    node_config = api_util.GetMessagesModule().NodeConfig(
        diskSizeGb=disk_size_gb)
    config = api_util.GetMessagesModule().EnvironmentConfig(
        nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project',
        self.TEST_PROJECT, '--location', self.TEST_LOCATION,
        '--disk-size', '{}KB'.format(disk_size_kb),
        '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testCustomDiskSizeTooSmall(self):
    """Tests error if --disk-size is < 10GB."""
    with self.AssertRaisesArgumentErrorRegexp(
        'must be greater than or equal to'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '9GB',
          '--async', self.TEST_ENVIRONMENT_ID)

  def testCustomDiskSizeTooLarge(self):
    """Tests error if --disk-size is > 64TB."""
    with self.AssertRaisesArgumentErrorRegexp(
        'must be less than or equal to'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '{}GB'.format((64 << 10) + 1),
          '--async', self.TEST_ENVIRONMENT_ID)

  def testCustomDiskSizeNotGigabyteMultiple(self):
    """Tests error if --disk-size is not an integer multiple of gigabytes."""
    disk_size_kb = (123 << 20) + 10  # 123 GB + 10 KB
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        'Must be an integer quantity of GB'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '{}KB'.format(disk_size_kb),
          '--async', self.TEST_ENVIRONMENT_ID)


if __name__ == '__main__':
  test_case.main()
