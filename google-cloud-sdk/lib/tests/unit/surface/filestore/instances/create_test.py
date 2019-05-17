# -*- coding: utf-8 -*- #
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
"""Tests for Cloud Filestore instance create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.util import waiter
from tests.lib.surface.filestore import base

import six


def _GetListCommandOuput(track_prefix=None):
  if track_prefix:
    return '$ gcloud {} filestore instances list'.format(track_prefix)
  return '$ gcloud filestore instances list'


class CloudFilestoreInstancesCreateTest(base.CloudFilestoreUnitTestBase,
                                        waiter.Base,
                                        parameterized.TestCase):

  _TRACK = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SetUpTrack(self._TRACK)
    self.standard_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('STANDARD'))
    self.premium_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('PREMIUM'))
    self.parent = 'projects/{}/locations/us-central1-c'.format(self.Project())
    self.name = 'instance_name'
    self.op_name = 'projects/{}/locations/us-central1-c/operations/op'.format(
        self.Project())

  def RunCreate(self, *args):
    return self.Run(['filestore', 'instances', 'create'] + list(args))

  def FileShareMsg(self):
    return self.messages.FileShareConfig

  def AddInstanceFileShare(self, instance, file_shares):
    instance.fileShares = file_shares

  def MakeFileShareConfig(self, name, capacity):
    return [self.FileShareMsg()(capacityGb=capacity, name=name)]

  def MakeNetworkConfig(self, network, range_=None):
    return [
        self.messages.NetworkConfig(
            network=network, reservedIpRange=range_)]

  def MakeLabels(self, labels_dict):
    return self.messages.Instance.LabelsValue(
        additionalProperties=[
            self.messages.Instance.LabelsValue.AdditionalProperty(
                key=key, value=value)
            for (key, value) in six.iteritems(labels_dict)])

  def ExpectCreateInstance(self, config):
    self.mock_client.projects_locations_instances.Create.Expect(
        self.messages.FileProjectsLocationsInstancesCreateRequest(
            parent=self.parent, instanceId=self.name, instance=config),
        self.messages.Operation(name=self.op_name))

  @parameterized.named_parameters(
      ('Single',
       ['instance_name',
        '--zone=us-central1-c',
        '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
        '--tier=STANDARD', '--file-share=name=my_vol,capacity=1TB',
        '--description=test_description',
        '--async'],
       'test_network', '10.0.0.0/29', 'my_vol', 1024),
      ('DeprecatedLocation',
       ['instance_name',
        '--location=us-central1-c',
        '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
        '--tier=STANDARD', '--file-share=name=my_vol,capacity=1TB',
        '--description=test_description',
        '--async'],
       'test_network', '10.0.0.0/29', 'my_vol', 1024),
      ('NoRange',
       ['instance_name',
        '--zone=us-central1-c', '--async',
        '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1TB',
        '--description=test_description'],
       'test_network', None, 'my_vol', 1024))
  def testCreateStandardInstance(self, args, expected_network,
                                 expected_range, expected_vol_name,
                                 expected_capacity):
    config = self.messages.Instance(
        tier=self.standard_tier,
        description='test_description',
        networks=self.MakeNetworkConfig(
            expected_network, expected_range))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig(
            expected_vol_name, expected_capacity))
    self.ExpectCreateInstance(config)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOuput(self._TRACK.prefix))

  def testCreateValidPremiumInstanceWithLabels(self):
    config = self.messages.Instance(
        tier=self.premium_tier,
        description='test_description',
        networks=self.MakeNetworkConfig('test_network', '10.0.0.0/29'),
        labels=self.MakeLabels({'key1': 'value1'}))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig('my_vol', 2560))
    self.ExpectCreateInstance(config)
    self.RunCreate(
        'instance_name', '--zone=us-central1-c',
        '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
        '--tier=PREMIUM', '--file-share=name=my_vol,capacity=2560GB',
        '--description=test_description', '--labels=key1=value1', '--async')
    self.AssertErrContains(_GetListCommandOuput(self._TRACK.prefix))

  def testWaitForCreate(self):
    config = self.messages.Instance(
        tier=self.standard_tier,
        networks=self.MakeNetworkConfig('test_network', None))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig('my_vol', 1024))
    self.ExpectCreateInstance(config)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(
            name=self.op_name),
        self.messages.Operation(name=self.op_name, done=True))
    self.RunCreate(
        'instance_name', '--zone=us-central1-c',
        '--network=name=test_network', '--file-share=name=my_vol,capacity=1TB')

  def testUsingDefaultLocation(self):
    properties.VALUES.filestore.location.Set('us-central1-c')
    config = self.messages.Instance(
        tier=self.standard_tier,
        networks=self.MakeNetworkConfig('test_network', None))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig('my_vol', 1024))
    self.ExpectCreateInstance(config)
    self.RunCreate(
        'instance_name',
        '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1TB', '--async')

  @parameterized.named_parameters(
      ('MissingLocationNoDefault', handlers.ParseError,
       ['instance_name', '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1TB', '--async']),
      ('MissingInstanceName', cli_test_base.MockArgumentError,
       ['--zone=us-central1-c', '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1TB', '--async']),
      ('BadCapacityUnits', cli_test_base.MockArgumentError,
       ['name', '--zone=us-central1-c', '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1C', '--async']),
      ('BadCapacityTooLarge', cli_test_base.MockArgumentError,
       ['name', '--zone=us-central1-c', '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1PB', '--async']),
      ('WithoutFileShareConfig', cli_test_base.MockArgumentError,
       ['instance_name', '--zone=us-central1-c',
        '--async', '--network=name=test_network']),
      ('WithoutNetworkConfig', cli_test_base.MockArgumentError,
       ['instance_name', '--zone=us-central1-c',
        '--async', '--file-share=name=my_vol,capacity=1TB']),
      ('InvalidTier', cli_test_base.MockArgumentError,
       ['instance_name', '--zone=us-central1-c',
        '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
        '--tier=INVAlID_GARBAGE_Tier',
        '--file-share=name=my_vol,capacity=1TB',
        '--description=test_description', '--async']))
  def testErrors(self, expected_error, args):
    with self.assertRaises(expected_error):
      self.RunCreate(*args)

  @parameterized.named_parameters(
      ('Standard', 'standard', '100GB', cli_test_base.MockArgumentError, '1TB'),
      ('Premium', 'premium', '2TB', exceptions.InvalidArgumentException,
       '2.5TB'))
  def testUsingInvalidCapacity(self, tier_arg, capacity_arg, exception,
                               expected):
    with self.assertRaisesRegexp(exception, expected):
      self.RunCreate(
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier={}'.format(tier_arg),
          '--file-share=name=my_vol,capacity={}'.format(capacity_arg),
          '--description=test_description', '--async')


class CloudFilestoreInstancesCreateAlphaTest(
    CloudFilestoreInstancesCreateTest):

  _TRACK = calliope_base.ReleaseTrack.ALPHA

  def FileShareMsg(self):
    return self.messages.FileShareConfig

  def AddInstanceFileShare(self, instance, file_shares):
    instance.fileShares = file_shares

  def MakeFileShareConfig(self, name, capacity, source_snapshot=None):
    return [self.FileShareMsg()(capacityGb=capacity, name=name,
                                sourceSnapshot=source_snapshot)]

  @parameterized.named_parameters(
      ('NoRange',
       ['instance_name',
        '--location=us-central1-c', '--async',
        '--network=name=test_network',
        '--file-share=name=my_vol,capacity=1TB,source-snapshot=snap',
        '--description=test_description'],
       'test_network', None, 'my_vol', 1024,
       'projects/fake-project/locations/us-central1/snapshots/snap'))
  def testCreateInstanceFromSnapshot(self, args, expected_network,
                                     expected_range, expected_vol_name,
                                     expected_capacity,
                                     expected_source_snapshot):
    config = self.messages.Instance(
        tier=self.standard_tier,
        description='test_description',
        networks=self.MakeNetworkConfig(
            expected_network, expected_range))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig(
            expected_vol_name, expected_capacity, expected_source_snapshot))
    self.ExpectCreateInstance(config)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOuput(self._TRACK.prefix))


if __name__ == '__main__':
  test_case.main()
