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
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import local_config
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import source_ref
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
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


class GetConfigurationChangesTest(cli_test_base.CliTestBase,
                                  parameterized.TestCase):

  def SetUp(self):
    self.args = parser_extensions.Namespace(
        update_env_vars=None, set_env_vars=None, remove_env_vars=None,
        clear_env_vars=None, concurrency=None)
    self.config = mock.NonCallableMock(concurrency='SENTINEL',
                                       deprecated_string_concurrency='SENTINEL')
    self.metadata = mock.NonCallableMock()

  def _GetAndApplyChanges(self):
    self.changes = flags.GetConfigurationChanges(self.args)
    for change in self.changes:
      change.AdjustConfiguration(self.config, self.metadata)

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

  @parameterized.parameters(['0', '1', '3'])
  def testConcurrencyNumeric(self, concurrency):
    self.args.concurrency = concurrency
    self._GetAndApplyChanges()
    self.assertEquals(len(self.changes), 1)
    self.assertEquals(self.config.concurrency, int(concurrency))
    self.assertIsNone(self.config.deprecated_string_concurrency)

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
    self.assertIsNone(flags.ValidateClusterArgs(self.args))

  def testValidateNoClusterOrLocation(self):
    self.args.cluster = None
    self.args.cluster_location = None
    self.assertIsNone(flags.ValidateClusterArgs(self.args))


class GetRegionTest(base.ServerlessBase,
                    cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Test getting region under different configs and flags."""

  def SetUp(self):
    self.fake_local_config = local_config.LocalConfig(
        'local-config-service', 'local-config-region')
    properties.VALUES.run.region.Set('serverless-config-region')
    properties.VALUES.compute.region.Set('compute-config-region')
    self.args = parser_extensions.Namespace()

  def testGetFromFlag(self):
    self.args.region = 'region1'
    self.assertEqual('region1', flags.GetRegion(self.args, prompt=True))

  def testGetFromLocalConfigFile(self):
    self.StartObjectPatch(
        flags, 'GetLocalConfig', return_value=self.fake_local_config)
    self.args.source = '.'
    self.assertEqual(self.fake_local_config.region, flags.GetRegion(self.args))

  def testGetFromServerlessConfig(self):
    self.StartObjectPatch(flags, 'GetLocalConfig', return_value=None)
    self.assertEqual(
        'serverless-config-region', flags.GetRegion(self.args))

  def testGetFromComputeConfig(self):
    self.StartObjectPatch(flags, 'GetLocalConfig', return_value=None)
    properties.VALUES.run.region.Set(None)
    self.assertEqual('compute-config-region',
                     flags.GetRegion(self.args, prompt=True))

  def testGetFromPrompt(self):
    self.StartObjectPatch(flags, 'GetLocalConfig', return_value=None)
    properties.VALUES.run.region.Set(None)
    properties.VALUES.compute.region.Set(None)

    fake_idx = 0
    expected_region = flags.REGIONS[fake_idx]
    self.WriteInput('{}\n'.format(fake_idx+1))

    actual_region = flags.GetRegion(self.args, prompt=True)
    self.AssertErrContains(
        'To make this the default region, run '
        '`gcloud config set run/region {}`'.format(expected_region))

    self.assertEqual(expected_region, actual_region)

