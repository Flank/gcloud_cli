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
"""Unit tests for environments create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
import six


class _EnvironmentsCreateTestBase(base.EnvironmentsUnitTest):

  # Must be called after self.SetTrack() for self.messages to be present
  def _SetTestMessages(self):
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
    self.NODE_CONFIG = self.messages.NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    self.CONFIG = self.messages.EnvironmentConfig(
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
    self.PYTHON_VERSION = '2'
    self.IMAGE_VERSION = 'composer-latest-airflow-7.8.9'
    self.AIRFLOW_VERSION = '7.8.9'
    self.KMS_KEY = 'testkey'
    self.KMS_KEYRING = 'testring'
    self.KMS_LOCATION = 'us-east1'
    self.KMS_PROJECT = 'testproject'
    self.KMS_FULLY_QUALIFIED = ('projects/testproject/locations/us-east1/' +
                                'keyRings/testring/cryptoKeys/testkey')

    self.running_op = self.MakeOperation(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_OPERATION_UUID,
        done=False)


class EnvironmentsCreateGATest(_EnvironmentsCreateTestBase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def testSuccessfulCreate_synchronous(self):
    """Tests a successful synchronous creation.

    The progress tracker should be activated and terminated.
    """
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
        r'^{{"ux": "PROGRESS_TRACKER", "message": "Waiting for \[{}] to '
        r'be created with \[{}]"'.format(self.TEST_ENVIRONMENT_NAME,
                                         self.TEST_OPERATION_NAME))

  def testFailedCreate_synchronous(self):
    """Tests a failed synchronous creation.

    A command_util.Error or a subclass thereof hould be raised.
    """
    self._SetTestMessages()
    # pylint: disable=invalid-name
    ERROR_DESCRIPTION = 'ERROR DESCRIPTION'
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    # pylint: disable=invalid-name
    SoftwareConfig = self.messages.SoftwareConfig

    software_config = SoftwareConfig(
        envVariables=SoftwareConfig.EnvVariablesValue(additionalProperties=[
            SoftwareConfig.EnvVariablesValue.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems(self.ENV_VARS_DICT)
        ]))
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
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
    self._SetTestMessages()
    # pylint: disable=invalid-name
    SoftwareConfig = self.messages.SoftwareConfig
    AirflowConfigOverrides = SoftwareConfig.AirflowConfigOverridesValue

    software_config = SoftwareConfig(
        airflowConfigOverrides=AirflowConfigOverrides(additionalProperties=[
            AirflowConfigOverrides.AdditionalProperty(key=k, value=v)
            for k, v in six.iteritems(self.AIRFLOW_CONFIG_OVERRIDES_DICT)
        ]))
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
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
    self._SetTestMessages()
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Invalid environment name'):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, 'foo_bar')

  def testMultipleAirflowConfigsMerged(self):
    """Test merging when --airflow-configs is provided many times."""
    self._SetTestMessages()
    # pylint: disable=invalid-name
    SoftwareConfig = self.messages.SoftwareConfig
    AirflowConfigOverrides = SoftwareConfig.AirflowConfigOverridesValue

    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = SoftwareConfig(
        airflowConfigOverrides=AirflowConfigOverrides(additionalProperties=[
            AirflowConfigOverrides.AdditionalProperty(key=k, value=v)  # pylint:disable=g-complex-comprehension
            for k, v in six.iteritems(collections.OrderedDict([
                ('a', '1'),
                ('b', '2'),
                ('c', '3'),
                ('d', '4'),
            ]))
        ]))
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
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
    self._SetTestMessages()
    # pylint: disable=invalid-name
    SoftwareConfig = self.messages.SoftwareConfig

    software_config = SoftwareConfig(
        envVariables=SoftwareConfig.EnvVariablesValue(additionalProperties=[
            SoftwareConfig.EnvVariablesValue.AdditionalProperty(key=k, value=v)   # pylint:disable=g-complex-comprehension
            for k, v in six.iteritems(collections.OrderedDict([
                ('a', '1'),
                ('b', '2'),
                ('c', '3'),
                ('d', '4'),
            ]))
        ]))
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        serviceAccount=self.SERVICE_ACCOUNT,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        oauthScopes=self.OAUTH_SCOPES, diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        tags=self.TAGS, diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        location=self.LOCATION_RELATIVE_NAME,
        machineType=self.MACHINE_TYPE_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        network=self.NETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--network', self.NETWORK_SHORT_NAME,
                                     '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testSubnetworkExpansion(self):
    """Tests that if --subnetwork is provided as a short name, it is expanded.
    """
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(
        network=self.NETWORK_RELATIVE_NAME,
        subnetwork=self.SUBNETWORK_RELATIVE_NAME,
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--network', self.NETWORK_SHORT_NAME,
                                     '--subnetwork', self.SUBNETWORK_SHORT_NAME,
                                     '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testUrlsReducedToRelativeNames(self):
    """Tests that fully-qualified URLs are provided, they become relative names.
    """
    self._SetTestMessages()
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.CONFIG,
        response=self.running_op)

    endpoint = 'https://compute.googleapis.com/compute/v1/'
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
    self._SetTestMessages()
    disk_size_gb = 123
    disk_size_kb = disk_size_gb << 20
    node_config = self.messages.NodeConfig(diskSizeGb=disk_size_gb)
    config = self.messages.EnvironmentConfig(nodeConfig=node_config)
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
    """Tests error if --disk-size is < 20GB."""
    self._SetTestMessages()
    with self.AssertRaisesArgumentErrorRegexp(
        'must be greater than or equal to'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '19GB',
          '--async', self.TEST_ENVIRONMENT_ID)

  def testCustomDiskSizeTooLarge(self):
    """Tests error if --disk-size is > 64TB."""
    self._SetTestMessages()
    with self.AssertRaisesArgumentErrorRegexp(
        'must be less than or equal to'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '{}GB'.format((64 << 10) + 1),
          '--async', self.TEST_ENVIRONMENT_ID)

  def testCustomDiskSizeNotGigabyteMultiple(self):
    """Tests error if --disk-size is not an integer multiple of gigabytes."""
    self._SetTestMessages()
    disk_size_kb = (123 << 20) + 10  # 123 GB + 10 KB
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        'Must be an integer quantity of GB'):
      self.RunEnvironments(
          'create', '--project',
          self.TEST_PROJECT, '--location', self.TEST_LOCATION,
          '--disk-size', '{}KB'.format(disk_size_kb),
          '--async', self.TEST_ENVIRONMENT_ID)

  def testPythonVersionInput(self):
    """Tests operation with a supplied --python-version."""
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        pythonVersion=self.PYTHON_VERSION)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--python-version', self.PYTHON_VERSION,
                                     '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)

  def testPythonVersionInvalidInput(self):
    """Tests error if supplied a --python-version that is not supported."""
    self._SetTestMessages()
    unsupported_version = '1'
    with self.AssertRaisesExceptionRegexp(
        cli_test_base.MockArgumentError,
        'Invalid choice: \'{}\''.format(unsupported_version)):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION,
                           '--python-version', unsupported_version,
                           '--async', self.TEST_ENVIRONMENT_ID)

  def testAirflowVersion_SuccessfulAsyncCreate(self):
    """Test that creating an environment with an airflow version works."""
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        imageVersion=self.IMAGE_VERSION, pythonVersion=self.PYTHON_VERSION)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create',
                                     '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--airflow-version', self.AIRFLOW_VERSION,
                                     '--python-version', self.PYTHON_VERSION,
                                     '--async', self.TEST_ENVIRONMENT_ID)
    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Create in progress for environment \[{}] with operation \[{}]'
        .format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testImageVersionValidInput(self):
    """Tests error if supplied am --airflow-version that is not supported."""
    self._SetTestMessages()
    valid_image_version_inputs = [
        'composer-1.2.3-airflow-1.2',
        'composer-1.2.3-airflow-1.2.3',
        'composer-11.22.33-airflow-11.22',
        'composer-11.22.33-airflow-11.22.33',
        'composer-latest-airflow-1.2.3'
    ]
    for test_input in valid_image_version_inputs:
      node_config = self.messages.NodeConfig(
          diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
      software_config = self.messages.SoftwareConfig(
          imageVersion=test_input)
      config = self.messages.EnvironmentConfig(
          nodeConfig=node_config,
          softwareConfig=software_config)
      self.ExpectEnvironmentCreate(
          self.TEST_PROJECT,
          self.TEST_LOCATION,
          self.TEST_ENVIRONMENT_ID,
          config=config,
          response=self.running_op)

      actual_op = self.RunEnvironments('create',
                                       '--project', self.TEST_PROJECT,
                                       '--location', self.TEST_LOCATION,
                                       '--image-version', test_input,
                                       '--async', self.TEST_ENVIRONMENT_ID)
      self.assertEqual(self.running_op, actual_op)

  def testImageVersionInvalidInput(self):
    """Tests error if supplied am --image-version that is not supported."""
    self._SetTestMessages()
    bad_image_version_inputs = [
        'composer-latest-airflow-latest',
        'composer-1.2.3-airflow-latest',
        'composer-1-airflow-1',
        'composer-1.2-airflow-1.2.3',
        'composer-1.2.3.4-airflow-latest',
        'a.b.c',
        'latest'
    ]

    for test_input in bad_image_version_inputs:
      with self.AssertRaisesExceptionRegexp(
          cli_test_base.MockArgumentError,
          r'Bad value \[{}\]'.format(test_input)):
        self.RunEnvironments(
            'create',
            '--project', self.TEST_PROJECT,
            '--location', self.TEST_LOCATION,
            '--image-version', test_input,
            '--async', self.TEST_ENVIRONMENT_ID)

  def testAirflowVersionValidInput(self):
    """Tests error if supplied am --airflow-version that is not supported."""
    self._SetTestMessages()
    valid_airflow_version_inputs = [
        '1.2.3',
        '1.2',
        '11.22.33'
    ]
    for test_input in valid_airflow_version_inputs:
      node_config = self.messages.NodeConfig(
          diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
      software_config = self.messages.SoftwareConfig(
          imageVersion='composer-latest-airflow-{}'.format(test_input))
      config = self.messages.EnvironmentConfig(
          nodeConfig=node_config,
          softwareConfig=software_config)
      self.ExpectEnvironmentCreate(
          self.TEST_PROJECT,
          self.TEST_LOCATION,
          self.TEST_ENVIRONMENT_ID,
          config=config,
          response=self.running_op)

      actual_op = self.RunEnvironments('create',
                                       '--project', self.TEST_PROJECT,
                                       '--location', self.TEST_LOCATION,
                                       '--airflow-version', test_input,
                                       '--async', self.TEST_ENVIRONMENT_ID)
      self.assertEqual(self.running_op, actual_op)

  def testAirflowVersionInvalidInput(self):
    """Tests error if supplied am --airflow-version that is not supported."""
    self._SetTestMessages()
    invalid_airflow_version_inputs = [
        'a.b.c',
        'composer-latest-airflow-latest',
        '1',
        '1.2.',  # with trailing dot
        '1.2.3.4',
        'latest'
    ]
    for test_input in invalid_airflow_version_inputs:
      with self.AssertRaisesExceptionRegexp(
          cli_test_base.MockArgumentError,
          r'Bad value \[{}\]'.format(test_input)):
        self.RunEnvironments(
            'create',
            '--project', self.TEST_PROJECT,
            '--location', self.TEST_LOCATION,
            '--airflow-version', test_input,
            '--async', self.TEST_ENVIRONMENT_ID)

  def testSuccessfulIpAliasEnvironmentCreation(self):
    self._SetTestMessages()

    ip_allocation_policy = self.messages.IPAllocationPolicy(
        useIpAliases=True,
        clusterSecondaryRangeName=self.TEST_CLUSTER_SECONDARY_RANGE_NAME,
        servicesSecondaryRangeName=self.TEST_SERVICES_SECONDARY_RANGE_NAME,
        clusterIpv4CidrBlock=self.TEST_CLUSTER_IPV4_CIDR_BLOCK,
        servicesIpv4CidrBlock=self.TEST_SERVICES_IPV4_CIDR_BLOCK,
    )

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(nodeConfig=node_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias',
        '--cluster-secondary-range-name',
        self.TEST_CLUSTER_SECONDARY_RANGE_NAME,
        '--services-secondary-range-name',
        self.TEST_SERVICES_SECONDARY_RANGE_NAME, '--cluster-ipv4-cidr',
        self.TEST_CLUSTER_IPV4_CIDR_BLOCK, '--services-ipv4-cidr',
        self.TEST_SERVICES_IPV4_CIDR_BLOCK, '--async', self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)

  def successfulPrivateIpEnvironmentCreationGa(self):
    self._SetTestMessages()

    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True)

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    args = [
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--async', self.TEST_ENVIRONMENT_ID
    ]
    actual_op = self.RunEnvironments(*args)

    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulPrivateIpEnvironmentCreation(self):
    self.successfulPrivateIpEnvironmentCreationGa()

  def privateIpEnvironmentCreationWithOptionsGa(self):
    self._SetTestMessages()
    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True,
        privateClusterConfig=self.messages.PrivateClusterConfig(
            enablePrivateEndpoint=True,
            masterIpv4CidrBlock=self.TEST_MASTER_IPV4_CIDR_BLOCK))

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    args = [
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--enable-private-endpoint', '--master-ipv4-cidr',
        self.TEST_MASTER_IPV4_CIDR_BLOCK, '--async', self.TEST_ENVIRONMENT_ID
    ]
    actual_op = self.RunEnvironments(*args)

    self.assertEqual(self.running_op, actual_op)

  def testPrivateIpEnvironmentCreationWithOptions(self):
    self.privateIpEnvironmentCreationWithOptionsGa()

  def testPrivateIpEnvironmentCreationWithWebServerAndCloudSqlRanges(self):
    self._SetTestMessages()
    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True,
        privateClusterConfig=self.messages.PrivateClusterConfig(
            enablePrivateEndpoint=True,
            masterIpv4CidrBlock=self.TEST_MASTER_IPV4_CIDR_BLOCK),
        webServerIpv4CidrBlock=self.TEST_WEB_SERVER_IPV4_CIDR_BLOCK,
        cloudSqlIpv4CidrBlock=self.TEST_CLOUD_SQL_IPV4_CIDR_BLOCK)

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--enable-private-endpoint', '--master-ipv4-cidr',
        self.TEST_MASTER_IPV4_CIDR_BLOCK, '--web-server-ipv4-cidr',
        self.TEST_WEB_SERVER_IPV4_CIDR_BLOCK, '--cloud-sql-ipv4-cidr',
        self.TEST_CLOUD_SQL_IPV4_CIDR_BLOCK, '--async',
        self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)

  def testIpAliasEnvironmentFlagPrerequisites(self):
    self._SetTestMessages()
    required_dep = '--enable-ip-alias'

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--cluster-ipv4-cidr',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--cluster-ipv4-cidr',
                           self.TEST_CLUSTER_IPV4_CIDR_BLOCK,
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error, r'Cannot specify {} without {}.'.format(
            '--cluster-secondary-range-name', required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--cluster-secondary-range-name',
                           self.TEST_CLUSTER_SECONDARY_RANGE_NAME,
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--services-ipv4-cidr',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--services-ipv4-cidr',
                           self.TEST_SERVICES_IPV4_CIDR_BLOCK,
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error, r'Cannot specify {} without {}.'.format(
            '--services-secondary-range-name', required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--services-secondary-range-name',
                           self.TEST_SERVICES_SECONDARY_RANGE_NAME,
                           self.TEST_ENVIRONMENT_ID)

  def ipAliasEnvironmentFlagPrerequisiteForPrivateIpGa(self):
    self._SetTestMessages()
    required_dep = '--enable-ip-alias'

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--enable-private-environment',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--enable-private-environment',
                           self.TEST_ENVIRONMENT_ID)

  def testIpAliasEnvironmentFlagPrerequisiteForPrivateIp(self):
    self.ipAliasEnvironmentFlagPrerequisiteForPrivateIpGa()

  def testIpv4CidrBlockFormatValidation(self):
    """Test that IPV4 CIDR block format validation fails fast."""
    self._SetTestMessages()
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'argument --services-ipv4-cidr: invalid Parse value: \'badIpv4Cidr\''):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--services-ipv4-cidr', 'badIpv4Cidr',
                           self.TEST_ENVIRONMENT_ID)

  def testPrivateIPEnvironmentFlagPrerequisites(self):
    self._SetTestMessages()
    required_dep = '--enable-private-environment'

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--enable-private-endpoint',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--enable-private-endpoint',
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--master-ipv4-cidr',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--master-ipv4-cidr',
                           self.TEST_MASTER_IPV4_CIDR_BLOCK,
                           self.TEST_ENVIRONMENT_ID)

  def testPrivateIPEnvironmentFlagPrerequisitesWebServerCloudSqlRanges(self):
    self._SetTestMessages()
    required_dep = '--enable-private-environment'

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--web-server-ipv4-cidr',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--web-server-ipv4-cidr',
                           self.TEST_WEB_SERVER_IPV4_CIDR_BLOCK,
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--cloud-sql-ipv4-cidr',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--cloud-sql-ipv4-cidr',
                           self.TEST_CLOUD_SQL_IPV4_CIDR_BLOCK,
                           self.TEST_ENVIRONMENT_ID)


class EnvironmentsCreateBetaTest(EnvironmentsCreateGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)

  # Even if empty, maintain structure for upcoming beta tests.
  # def _SetTestMessages(self):
  #   # pylint: disable=invalid-name
  #   super(EnvironmentsCreateBetaTest, self)._SetTestMessages()

  def successfulPrivateIpEnvironmentCreationBeta(self):
    self._SetTestMessages()

    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True)

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    args = [
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--web-server-allow-all', '--async', self.TEST_ENVIRONMENT_ID
    ]
    actual_op = self.RunEnvironments(*args)

    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulPrivateIpEnvironmentCreation(self):
    self.successfulPrivateIpEnvironmentCreationBeta()

  def privateIpEnvironmentCreationWithOptionsBeta(self):
    self._SetTestMessages()
    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True,
        privateClusterConfig=self.messages.PrivateClusterConfig(
            enablePrivateEndpoint=True,
            masterIpv4CidrBlock=self.TEST_MASTER_IPV4_CIDR_BLOCK))

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    args = [
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--enable-private-endpoint', '--master-ipv4-cidr',
        self.TEST_MASTER_IPV4_CIDR_BLOCK, '--web-server-allow-all', '--async',
        self.TEST_ENVIRONMENT_ID
    ]
    actual_op = self.RunEnvironments(*args)

    self.assertEqual(self.running_op, actual_op)

  def testPrivateIpEnvironmentCreationWithOptions(self):
    self.privateIpEnvironmentCreationWithOptionsBeta()

  def testPrivateIpEnvironmentCreationWithWebServerAndCloudSqlRanges(self):
    self._SetTestMessages()
    private_environment_config = self.messages.PrivateEnvironmentConfig(
        enablePrivateEnvironment=True,
        privateClusterConfig=self.messages.PrivateClusterConfig(
            enablePrivateEndpoint=True,
            masterIpv4CidrBlock=self.TEST_MASTER_IPV4_CIDR_BLOCK),
        webServerIpv4CidrBlock=self.TEST_WEB_SERVER_IPV4_CIDR_BLOCK,
        cloudSqlIpv4CidrBlock=self.TEST_CLOUD_SQL_IPV4_CIDR_BLOCK)

    ip_allocation_policy = self.messages.IPAllocationPolicy(useIpAliases=True)

    node_config = self.messages.NodeConfig(
        diskSizeGb=self.DEFAULT_DISK_SIZE_GB,
        ipAllocationPolicy=ip_allocation_policy)

    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        privateEnvironmentConfig=private_environment_config)

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--enable-ip-alias', '--enable-private-environment',
        '--enable-private-endpoint', '--master-ipv4-cidr',
        self.TEST_MASTER_IPV4_CIDR_BLOCK, '--web-server-ipv4-cidr',
        self.TEST_WEB_SERVER_IPV4_CIDR_BLOCK, '--cloud-sql-ipv4-cidr',
        self.TEST_CLOUD_SQL_IPV4_CIDR_BLOCK, '--web-server-allow-all',
        '--async', self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)

  def testPrivateIPEnvironmentWebServerAccessControlRequirement(self):
    self._SetTestMessages()

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        'Cannot specify --enable-private-environment without one of: ' +
        '--web-server-allow-ip, --web-server-allow-all ' +
        'or --web-server-deny-all'):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--enable-private-environment', '--enable-ip-alias',
                           self.TEST_ENVIRONMENT_ID)

  def ipAliasEnvironmentFlagPrerequisiteForPrivateIpBeta(self):
    self._SetTestMessages()
    required_dep = '--enable-ip-alias'

    with self.AssertRaisesExceptionRegexp(
        command_util.Error,
        r'Cannot specify {} without {}.'.format('--enable-private-environment',
                                                required_dep)):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--enable-private-environment',
                           '--web-server-allow-all', self.TEST_ENVIRONMENT_ID)

  def testIpAliasEnvironmentFlagPrerequisiteForPrivateIp(self):
    self.ipAliasEnvironmentFlagPrerequisiteForPrivateIpBeta()

  def testWebServerAccessControl(self):
    self._SetTestMessages()

    config = self.messages.EnvironmentConfig(
        nodeConfig=self.messages.NodeConfig(
            diskSizeGb=self.DEFAULT_DISK_SIZE_GB),
        webServerNetworkAccessControl=self.messages
        .WebServerNetworkAccessControl(allowedIpRanges=[
            self.messages.AllowedIpRange(
                value='192.168.35.0/28', description='description1'),
            self.messages.AllowedIpRange(
                value='2001:db8::/32', description='description2')
        ]))

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--async', '--web-server-allow-ip',
        'ip_range=192.168.35.0/28,description=description1',
        '--web-server-allow-ip',
        'ip_range=2001:db8::/32,description=description2',
        self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)

  def testWebServerAccessControlFormatValidation(self):
    self._SetTestMessages()
    with self.AssertRaisesExceptionMatches(command_util.Error,
                                           'Invalid IP range'):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--web-server-allow-ip', 'ip_range=badIpRange',
                           self.TEST_ENVIRONMENT_ID)

  def testWebServerAccessControlExclusiveFlags(self):
    """Test that only one of the --web-server* flags can be provided."""
    self._SetTestMessages()
    with self.AssertRaisesArgumentErrorMatches(
        'argument --web-server-allow-all: At most one of ' +
        '--web-server-allow-all | --web-server-allow-ip | ' +
        '--web-server-deny-all may be specified'):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--web-server-allow-all', '--web-server-deny-all',
                           self.TEST_ENVIRONMENT_ID)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --web-server-allow-all: At most one of ' +
        '--web-server-allow-all | --web-server-allow-ip | ' +
        '--web-server-deny-all may be specified'):

      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           '--web-server-allow-all', '--web-server-allow-ip',
                           'ip_range=192.168.35.0/28', self.TEST_ENVIRONMENT_ID)

  def testCloudSqlMachineType(self):
    """Test specifying Cloud SQL machine type."""
    self._SetTestMessages()

    config = self.messages.EnvironmentConfig(
        nodeConfig=self.messages.NodeConfig(
            diskSizeGb=self.DEFAULT_DISK_SIZE_GB),
        databaseConfig=self.messages
        .DatabaseConfig(machineType='db-n1-standard-2'))

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--async', '--cloud-sql-machine-type',
                                     'db-n1-standard-2',
                                     self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)

  def testWebServerMachineType(self):
    """Test specifying web server machine type."""
    self._SetTestMessages()

    config = self.messages.EnvironmentConfig(
        nodeConfig=self.messages.NodeConfig(
            diskSizeGb=self.DEFAULT_DISK_SIZE_GB),
        webServerConfig=self.messages
        .WebServerConfig(machineType='n1-standard-2'))

    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--async', '--web-server-machine-type',
                                     'n1-standard-2',
                                     self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)


class EnvironmentsCreateAlphaTest(EnvironmentsCreateBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)

  def _SetTestMessages(self):
    # pylint: disable=invalid-name
    super(EnvironmentsCreateAlphaTest, self)._SetTestMessages()
    self.AIRFLOW_EXECUTOR_TYPE = 'KUBERNETES'

  def testSuccessfulAsyncCreateWithAlphaFeatures(self):
    """Test that creating an environment with alpha features works."""
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        airflowExecutorType=self.messages.SoftwareConfig
        .AirflowExecutorTypeValueValuesEnum.KUBERNETES)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config, softwareConfig=software_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)

    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--airflow-executor-type',
                                     self.AIRFLOW_EXECUTOR_TYPE,
                                     '--async', self.TEST_ENVIRONMENT_ID)

    self.assertEqual(self.running_op, actual_op)
    self.AssertErrMatches(
        r'^Create in progress for environment \[{}] with operation \[{}]'
        .format(self.TEST_ENVIRONMENT_NAME, self.TEST_OPERATION_NAME))

  def testSuccessfulPrivateIpEnvironmentCreation(self):
    # Call GA version, since Web Server ACL is only available in beta.
    self.successfulPrivateIpEnvironmentCreationGa()

  def testPrivateIpEnvironmentCreationWithOptions(self):
    # Call GA version, since Web Server ACL is only available in beta.
    self.privateIpEnvironmentCreationWithOptionsGa()

  def testPrivateIpEnvironmentCreationWithWebServerAndCloudSqlRanges(self):
    # Feature available only in beta.
    pass

  def testPrivateIPEnvironmentFlagPrerequisitesWebServerCloudSqlRanges(self):
    # Feature available only in beta.
    pass

  def testWebServerAccessControl(self):
    # Feature available only in beta.
    pass

  def testWebServerAccessControlFormatValidation(self):
    # Feature available only in beta.
    pass

  def testPrivateIPEnvironmentWebServerAccessControlRequirement(self):
    # Feature available only in beta.
    pass

  def testIpAliasEnvironmentFlagPrerequisiteForPrivateIp(self):
    # Call GA version, since Web Server ACL is only available in beta.
    self.ipAliasEnvironmentFlagPrerequisiteForPrivateIpGa()

  def testWebServerAccessControlExclusiveFlags(self):
    # Feature available only in beta.
    pass

  def testSuccessfulCreationWithSyntacticallyCorrectKmsKey(self):
    """Tests that creation succeedes with a properly formatted KMS key."""
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        pythonVersion=self.PYTHON_VERSION)
    encryption_config = self.messages.EncryptionConfig(
        kmsKeyName=self.KMS_FULLY_QUALIFIED)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config,
        encryptionConfig=encryption_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                                     '--location', self.TEST_LOCATION,
                                     '--python-version', self.PYTHON_VERSION,
                                     '--async', self.TEST_ENVIRONMENT_ID,
                                     '--kms-key', self.KMS_FULLY_QUALIFIED)
    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulCreationWithKmsKeyAndKeyRing(self):
    """Tests that creation succeedes with a properly formatted KMS key."""
    expected_kms_full_key_name = (
        'projects/{}/locations/{}/keyRings/testkeyring/cryptoKeys/testkeyname'
        .format(self.TEST_PROJECT, self.TEST_LOCATION))
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        pythonVersion=self.PYTHON_VERSION)
    encryption_config = self.messages.EncryptionConfig(
        kmsKeyName=expected_kms_full_key_name)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config,
        encryptionConfig=encryption_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--python-version', self.PYTHON_VERSION, '--async',
        self.TEST_ENVIRONMENT_ID, '--kms-key', 'testkeyname', '--kms-keyring',
        'testkeyring', '--kms-project', self.TEST_PROJECT, '--kms-location',
        self.TEST_LOCATION)
    self.assertEqual(self.running_op, actual_op)

  def testSuccessfulCreationWithFullKmsGroupSpecified(self):
    """Tests that creation succeedes with a properly formatted KMS key."""
    expected_kms_full_key_name = (
        'projects/other-project/locations/us-central1/' +
        'keyRings/testkeyring/cryptoKeys/testkeyname')
    self._SetTestMessages()
    node_config = self.messages.NodeConfig(diskSizeGb=self.DEFAULT_DISK_SIZE_GB)
    software_config = self.messages.SoftwareConfig(
        pythonVersion=self.PYTHON_VERSION)
    encryption_config = self.messages.EncryptionConfig(
        kmsKeyName=expected_kms_full_key_name)
    config = self.messages.EnvironmentConfig(
        nodeConfig=node_config,
        softwareConfig=software_config,
        encryptionConfig=encryption_config)
    self.ExpectEnvironmentCreate(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=config,
        response=self.running_op)
    actual_op = self.RunEnvironments(
        'create', '--project', self.TEST_PROJECT, '--location',
        self.TEST_LOCATION, '--python-version', self.PYTHON_VERSION, '--async',
        self.TEST_ENVIRONMENT_ID, '--kms-key', 'testkeyname', '--kms-keyring',
        'testkeyring', '--kms-location', 'us-central1', '--kms-project',
        'other-project')
    self.assertEqual(self.running_op, actual_op)

  def testFailedCreationWithSyntacticallyIncorrectKmsKey(self):
    """Tests that creation fails with an improperly formatted KMS key."""
    self._SetTestMessages()
    invalid_kms_key = 'test-project/test-key'
    with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                          'Encryption key not fully specified'):
      self.RunEnvironments('create', '--project', self.TEST_PROJECT,
                           '--location', self.TEST_LOCATION, '--async',
                           self.TEST_ENVIRONMENT_ID, '--kms-key',
                           invalid_kms_key)


if __name__ == '__main__':
  test_case.main()
