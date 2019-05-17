# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for the Run flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import source_ref
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.run import base

import mock


class ServerlessFlagsTest(base.ServerlessSurfaceBase, parameterized.TestCase):

  def testGenerateDefaultServiceName(self):
    self.StartObjectPatch(os.path, 'isdir')
    self.assertEqual('directory-3',
                     resource_args.GenerateServiceName(
                         source_ref.SourceRef.MakeDirRef('-#dir_ecTor$y-3-')))

  def testServiceBeginDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('-s3rvice')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)

  def testServiceEndDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('s3rvice-')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)

  def testServiceContainsDash(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('s3rv-ice')
    self.assertEqual(self._ServiceRef('s3rv-ice'), flags.GetService(args))

  def testServiceOneCharacter(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('a')
    self.assertEqual(self._ServiceRef('a'), flags.GetService(args))

  def testServiceDigits(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef('123abc123')
    self.assertEqual(self._ServiceRef('123abc123'), flags.GetService(args))

  def testServiceTooLong(self):
    args = mock.Mock()
    args.CONCEPTS.service.Parse.return_value = self._ServiceRef(
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    with self.assertRaises(flags.ArgumentError):
      flags.GetService(args)


class GetConfigurationChangesTest(base.ServerlessSurfaceBase,
                                  parameterized.TestCase):

  def SetUp(self):
    self.args = parser_extensions.Namespace(
        update_env_vars=None, set_env_vars=None, remove_env_vars=None,
        clear_env_vars=None, concurrency=None, add_cloudsql_instances=None,
        remove_cloudsql_instances=None, clear_cloudsql_instances=None,
        set_cloudsql_instances=None, cpu=None, clear_labels=None,
        update_labels=None, remove_labels=None)
    self.service = service.Service.New(
        self.mock_serverless_client, self.namespace.namespacesId)
    self.config = self.service.configuration
    self.metadata = self.service.metadata

  def _GetAndApplyChanges(self):
    self.changes = flags.GetConfigurationChanges(self.args)
    for change in self.changes:
      change.AdjustConfiguration(self.config, self.metadata)

  def testCpu(self):
    self.args.cpu = '1m'
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertEquals('1m', self.config.resource_limits['cpu'])

  def testConcurrencyEnum(self):
    self.args.concurrency = 'Single'
    self._GetAndApplyChanges()
    self.AssertErrContains('deprecated')
    self.assertEquals(len(self.changes), 1)
    self.assertEquals('Single', self.config.deprecated_string_concurrency)
    self.assertIsNone(self.config.concurrency)

  def testConcurrencyDefault(self):
    self.args.concurrency = 'default'
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertIsNone(self.config.deprecated_string_concurrency)
    self.assertIsNone(self.config.concurrency)

  def testServiceAccount(self):
    self.args.service_account = 'test@project.iam.gserviceaccount.com'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    self.assertEqual(self.config.service_account, self.args.service_account)

  @parameterized.parameters(['0', '1', '3'])
  def testConcurrencyNumeric(self, concurrency):
    self.args.concurrency = concurrency
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertEquals(self.config.concurrency, int(concurrency))
    self.assertIsNone(self.config.deprecated_string_concurrency)

  def testUpdateLabels(self):
    self.args.update_labels = {'asdf': 'tyte'}
    self.args._specified_args['update_labels'] = 'update_labels'
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    labels = k8s_object.LabelsFromMetadata(self.serverless_messages,
                                           self.metadata)
    self.assertEqual(dict(**labels), {'asdf': 'tyte'})

  def testRemoveLabels(self):
    self.args.remove_labels = ['abc', 'def']
    self.args._specified_args['remove_labels'] = 'remove_labels'
    self.service.labels.update({'abc': 'foo', 'def': 'bar', 'ghi': 'baz'})
    self._GetAndApplyChanges()
    self.assertEqual(len(self.changes), 1)
    labels = k8s_object.LabelsFromMetadata(self.serverless_messages,
                                           self.metadata)
    self.assertEqual(dict(**labels), {'ghi': 'baz'})

  @parameterized.parameters(['4s', '8m16s'])
  def testValidTimeoutDuration(self, timeout):
    self.args.timeout = timeout
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertEquals(self.config.timeout,
                      int(times.ParseDuration(timeout).total_seconds))

  @parameterized.parameters(['2', '5'])
  def testValidTimeoutNumber(self, timeout):
    self.args.timeout = timeout
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertEquals(self.config.timeout, int(timeout))

  @parameterized.parameters(['2.0', '@^$%4', 'abcd'])
  def testInvalidTimeoutDurationSyntaxError(self, timeout):
    self.args.timeout = timeout
    with self.assertRaises(times.DurationSyntaxError):
      self._GetAndApplyChanges()

  @parameterized.parameters(['0', '-1'])
  def testInvalidTimeoutArgError(self, timeout):
    self.args.timeout = timeout
    with self.assertRaises(flags.ArgumentError):
      self._GetAndApplyChanges()

  def testValidateClusterNoLocation(self):
    self.args.cluster = 'mycluster'
    self.args.cluster_location = None
    with self.assertRaises(exceptions.ConfigurationError):
      flags.ValidateClusterArgs(self.args)

  def testValidateClusterAndLocation(self):
    self.args.cluster = 'mycluster'
    self.args.cluster_location = 'mylocation'
    self.assertIsNone(flags.ValidateClusterArgs(self.args))

  def testValidateClusterLocationOnly(self):
    self.args.cluster = None
    self.args.cluster_location = 'mylocation'
    with self.assertRaises(exceptions.ConfigurationError):
      flags.ValidateClusterArgs(self.args)

  def testValidateNoClusterOrLocation(self):
    self.args.cluster = None
    self.args.cluster_location = None
    self.assertIsNone(flags.ValidateClusterArgs(self.args))


class GetRegionTest(base.ServerlessBase,
                    cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Test getting region under different configs and flags."""

  def SetUp(self):
    properties.VALUES.run.region.Set('serverless-config-region')
    properties.VALUES.compute.region.Set('compute-config-region')
    self.args = parser_extensions.Namespace()

  def testGetFromFlag(self):
    self.args.region = 'region1'
    self.assertEqual('region1', flags.GetRegion(self.args, prompt=True))

  def testGetFromServerlessConfig(self):
    self.assertEqual(
        'serverless-config-region', flags.GetRegion(self.args))

  def testGetFromComputeConfig(self):
    properties.VALUES.run.region.Set(None)
    self.assertEqual('compute-config-region',
                     flags.GetRegion(self.args, prompt=True))

  def testGetFromPrompt(self):
    with mock.patch(
        'googlecloudsdk.api_lib.run.global_methods.GetServerlessClientInstance',
        return_value=self.mock_serverless_client):
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListRegions',
          return_value=[base.DEFAULT_REGION]):
        properties.VALUES.run.region.Set(None)
        properties.VALUES.compute.region.Set(None)

        fake_idx = 0
        self.WriteInput('{}\n'.format(fake_idx + 1))

        expected_region = base.DEFAULT_REGION
        actual_region = flags.GetRegion(self.args, prompt=True)
        self.AssertErrContains(
            'To make this the default region, run '
            '`gcloud config set run/region {}`'.format(expected_region))

        self.assertEqual(expected_region, actual_region)


class ValidationsTest(test_case.TestCase):

  def testVerifyGKEFlagsAllowUnauthenticated(self):
    with self.assertRaises(exceptions.ConfigurationError):
      args = mock.Mock()
      args.allow_unauthenticated = True
      flags.VerifyGKEFlags(args)

  def testVerifyGKEFlagsServiceAccount(self):
    with self.assertRaises(exceptions.ConfigurationError):
      args = mock.Mock()
      args.service_account = 'test@iam.gserviceaccount.com'
      flags.VerifyGKEFlags(args)

  def testVerifyOnePlatformFlagsConnectivity(self):
    with self.assertRaises(exceptions.ConfigurationError):
      args = mock.Mock()
      args.connectivity = True
      flags.VerifyOnePlatformFlags(args)

  def testVerifyOnePlatformFlagsCpu(self):
    with self.assertRaises(exceptions.ConfigurationError):
      args = mock.Mock()
      args.cpu = 2
      flags.VerifyOnePlatformFlags(args)


class ValidateIsGKETest(test_case.TestCase):

  def testTrue(self):
    args = mock.Mock()
    args.CONCEPTS.cluster.Parse.return_value = 'Fake Location'
    self.assertTrue(flags.ValidateIsGKE(args))

  def testFalse(self):
    args = mock.Mock()
    args.CONCEPTS.cluster.Parse.return_value = None
    self.assertFalse(flags.ValidateIsGKE(args))

  def testValidationFails(self):
    with self.assertRaises(exceptions.ConfigurationError):
      args = mock.Mock()
      args.cluster = 'cluster'
      args.cluster_location = None
      args.CONCEPTS.cluster.Parse.return_value = None
      flags.ValidateIsGKE(args)
