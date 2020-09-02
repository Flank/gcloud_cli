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
"""Tests for Cloud Filestore instance create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.util import waiter
from tests.lib.surface.filestore import base
from tests.lib.surface.filestore.instances import util
import six


def _GetListCommandOutput(track_prefix=None):
  if track_prefix:
    return '$ gcloud {} filestore instances list'.format(track_prefix)
  return '$ gcloud filestore instances list'


class CloudFilestoreInstancesCreateBase(base.CloudFilestoreUnitTestBase,
                                        waiter.Base, parameterized.TestCase):

  def RunCreate(self, *args):
    return self.Run(['filestore', 'instances', 'create'] + list(args))

  def SetUp(self):
    self.SetUpTrack(self.track)
    if self.track == calliope_base.ReleaseTrack.GA:
      self.CommonVarsBasic()
    else:
      self.CommonVarsHighScale()

  def CommonVarsBasic(self):
    self.standard_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('STANDARD'))
    self.premium_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('PREMIUM'))
    self.parent = 'projects/{}/locations/us-central1-c'.format(self.Project())
    self.name = 'instance_name'
    self.op_name = 'projects/{}/locations/us-central1-c/operations/op'.format(
        self.Project())

  def CommonVarsHighScale(self):
    self.standard_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('STANDARD'))
    self.premium_tier = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('PREMIUM'))
    self.basic_hdd = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('BASIC_HDD'))
    self.basic_ssd = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name('BASIC_SSD'))
    self.high_scale_ssd = (
        self.messages.Instance.TierValueValuesEnum.lookup_by_name(
            'HIGH_SCALE_SSD'))
    self.parent = 'projects/{}/locations/us-central1-c'.format(self.Project())
    self.name = 'instance_name'
    self.op_name = 'projects/{}/locations/us-central1-c/operations/op'.format(
        self.Project())


class CloudFilestoreInstancesCreateTest(CloudFilestoreInstancesCreateBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def FileShareMsg(self):
    return self.messages.FileShareConfig

  @staticmethod
  def AddInstanceFileShare(instance, file_shares):
    instance.fileShares = file_shares

  def MakeFileShareConfig(self, name, capacity):
    return [self.FileShareMsg()(capacityGb=capacity, name=name)]

  def MakeNetworkConfig(self, network, range_=None):
    return [
        self.messages.NetworkConfig(network=network, reservedIpRange=range_)
    ]

  def MakeLabels(self, labels_dict):
    return self.messages.Instance.LabelsValue(additionalProperties=[
        self.messages.Instance.LabelsValue.AdditionalProperty(
            key=key, value=value) for (key, value) in six.iteritems(labels_dict)
    ])

  def ExpectCreateInstance(self, config):
    self.mock_client.projects_locations_instances.Create.Expect(
        self.messages.FileProjectsLocationsInstancesCreateRequest(
            parent=self.parent, instanceId=self.name, instance=config),
        self.messages.Operation(name=self.op_name))

  @parameterized.named_parameters(('Single', [
      'instance_name', '--zone=us-central1-c',
      '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
      '--tier=STANDARD', '--file-share=name=my_vol,capacity=1TB',
      '--description=test_description', '--async'
  ], 'test_network', '10.0.0.0/29', 'my_vol', 1024), ('DeprecatedLocation', [
      'instance_name', '--location=us-central1-c',
      '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
      '--tier=STANDARD', '--file-share=name=my_vol,capacity=1TB',
      '--description=test_description', '--async'
  ], 'test_network', '10.0.0.0/29', 'my_vol', 1024), ('NoRange', [
      'instance_name', '--zone=us-central1-c', '--async',
      '--network=name=test_network', '--tier=STANDARD',
      '--file-share=name=my_vol,capacity=2TB', '--description=test_description'
  ], 'test_network', None, 'my_vol', 2048))
  def testCreateStandardInstance(self, args, expected_network, expected_range,
                                 expected_vol_name, expected_capacity):
    config = self.messages.Instance(
        tier=self.standard_tier,
        description='test_description',
        networks=self.MakeNetworkConfig(expected_network, expected_range))
    self.AddInstanceFileShare(
        config, self.MakeFileShareConfig(expected_vol_name, expected_capacity))
    self.ExpectCreateInstance(config)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  def testCreateValidPremiumInstanceWithLabels(self):
    config = self.messages.Instance(
        tier=self.premium_tier,
        description='test_description',
        networks=self.MakeNetworkConfig('test_network', '10.0.0.0/29'),
        labels=self.MakeLabels({'key1': 'value1'}))
    self.AddInstanceFileShare(config, self.MakeFileShareConfig('my_vol', 2560))
    self.ExpectCreateInstance(config)
    self.RunCreate('instance_name', '--zone=us-central1-c',
                   '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
                   '--tier=PREMIUM', '--file-share=name=my_vol,capacity=2560GB',
                   '--description=test_description', '--labels=key1=value1',
                   '--async')
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  def testWaitForCreate(self):
    config = self.messages.Instance(
        tier=self.standard_tier,
        networks=self.MakeNetworkConfig('test_network', None))
    self.AddInstanceFileShare(config, self.MakeFileShareConfig('my_vol', 1024))
    self.ExpectCreateInstance(config)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(
            name=self.op_name),
        self.messages.Operation(name=self.op_name, done=True))
    self.RunCreate('instance_name', '--zone=us-central1-c',
                   '--network=name=test_network',
                   '--file-share=name=my_vol,capacity=1TB')

  def testUsingDefaultLocation(self):
    properties.VALUES.filestore.location.Set('us-central1-c')
    config = self.messages.Instance(
        tier=self.standard_tier,
        networks=self.MakeNetworkConfig('test_network', None))
    self.AddInstanceFileShare(config, self.MakeFileShareConfig('my_vol', 1024))
    self.ExpectCreateInstance(config)
    self.RunCreate('instance_name', '--network=name=test_network',
                   '--file-share=name=my_vol,capacity=1TB', '--async')

  @parameterized.named_parameters(
      ('MissingLocationNoDefault', handlers.ParseError, [
          'instance_name', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('MissingInstanceName', cli_test_base.MockArgumentError, [
          '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('BadCapacityUnits', cli_test_base.MockArgumentError, [
          'name', '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1C', '--async'
      ]), ('WithoutFileShareConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--network=name=test_network'
      ]), ('BadCapacityTooLarge', cli_test_base.MockArgumentError, [
          'name', '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1PB', '--async'
      ]), ('WithoutNetworkConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--file-share=name=my_vol,capacity=1TB'
      ]), ('InvalidTier', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=INVAlID_GARBAGE_Tier',
          '--file-share=name=my_vol,capacity=1TB',
          '--description=test_description', '--async'
      ]))
  def testErrors(self, expected_error, args):
    with self.assertRaises(expected_error):
      self.RunCreate(*args)


class CloudFilestoreInstancesCreateAlphaTest(CloudFilestoreInstancesCreateBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWaitForCreate(self):
    file_share_config = util.CreateFileShareConfig(
        messages=self.messages,
        flags_file=None,
        expected_vol_name='my_vol',
        expected_capacity=1024,
        expected_source_snapshot=None,
        expected_source_backup=None,
        expected_nfs_export_options=None)
    instance = util.CreateFileShareInstance(
        messages=self.messages,
        tier='BASIC_HDD',
        expected_network='test_network',
        expected_labels=None,
        expected_range=None,
        expected_description='test_description')
    util.InstanceAddFileShareConfig(
        messages=self.messages,
        instance=instance,
        file_share_config=file_share_config)
    util.ExpectCreateInstance(
        messages=self.messages,
        mock_client=self.mock_client,
        parent=self.parent,
        name=self.name,
        op_name=self.op_name,
        config=instance)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(
            name=self.op_name),
        self.messages.Operation(name=self.op_name, done=True))
    self.RunCreate('instance_name', '--zone=us-central1-c',
                   '--network=name=test_network',
                   '--description=test_description',
                   '--file-share=name=my_vol,capacity=1TB')

  @parameterized.named_parameters(
      ('BasicWithLabels', [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_SSD', '--file-share=name=my_vol,capacity=8TB',
          '--description=test_description', '--async', '--labels=key1=value1'
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192, None, None, {
          'key1': 'value1'
      }, None),
      ('BasicFromSnapshot', [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_SSD',
          '--file-share=name=my_vol,capacity=8TB,source-snapshot=snap',
          '--description=test_description', '--async', '--labels=key1=value1'
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192,
       'projects/fake-project/locations/us-central1-c/snapshots/snap', None, {
           'key1': 'value1'
       }, None),
      ('BasicFromLegacySnapshot', [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_SSD',
          '--file-share=name=my_vol,capacity=8TB,source-snapshot=snap,source-snapshot-region=us-central1',
          '--description=test_description', '--async', '--labels=key1=value1'
      ],
       'test_network', '10.0.0.0/29', 'my_vol', 8192,
       'projects/fake-project/locations/us-central1/snapshots/snap', None, {
           'key1': 'value1'
       }, None), ('BasicFromBackup', [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=BASIC_SSD',
           '--file-share=name=my_vol,capacity=8TB,source-backup=backup,source-backup-region=us-central1',
           '--description=test_description', '--async', '--labels=key1=value1'
       ],
                  'test_network', '10.0.0.0/29', 'my_vol', 8192, None,
                  'projects/fake-project/locations/us-central1/backups/backup',
                  {
                      'key1': 'value1'
                  }, None),
      ('HighScaleWithLabels',
       [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD', '--file-share=name=my_vol,capacity=100TB',
           '--description=test_description', '--async', '--labels=key1=value1'
       ],
       'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, {
           'key1': 'value1'
       },
       None
      ),
      ('FlagsFilePriority',
       [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--file-share=name=my_vol,capacity=100TB',
           '--description=test_description',
           '--async',
           '--flags-file=file-share-export-dual-options.json',
       ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None,
       None), ('FlagsFilePriorityYaml', [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--file-share=name=my_vol,capacity=100TB',
           '--description=test_description',
           '--async',
           '--flags-file=file-share-export-dual-options.yaml',
       ], 'test_network', '10.0.0.0/23',
               'my_vol', 102400, None, None, None, None),
      ('BasicNoRange',
       [
           'instance_name',
           '--zone=us-central1-c',
           '--async', '--network=name=test_network', '--tier=STANDARD',
           '--file-share=name=my_vol,capacity=2TB',
           '--description=test_description'
       ], 'test_network', None, 'my_vol', 2048, None, None, None, None),
      ('BasicSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--description=test_description',
          '--async',
          '--flags-file=file-share-export-dual-options.json',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192, None, None, None, None),
      ('BasicNfsExportOptions', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--flags-file=file-share-export-rw-squash-ip.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 1024, None, None, None, None),
      ('BasicNfsExportOptionsGIDUID', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--flags-file=file-share-export-uid-gid.json',
          '--description=test_description',
          '--async',
      ], 'test_network',
       '10.0.0.0/29', 'my_vol', 1024, None, None, None, None),
      ('HighScaleSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
          '--tier=HIGH_SCALE_SSD',
          '--description=test_description',
          '--async',
          '--flags-file=high-scale-file-share-minimal.json',
      ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None,
       None), ('HighScaleNfsExportOptions', [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--flags-file=high-scale-file-share-export-rw-squash-ip.json',
           '--description=test_description',
           '--async',
       ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None,
               None),
      ('MultipleNfsExportOptions', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
          '--tier=HIGH_SCALE_SSD',
          '--flags-file=high-scale-file-share-export-dual-options.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None,
       None), ('HighScaleNfsExportOptionsGIDUID', [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--flags-file=high-scale-file-share-export-uid-gid.json',
           '--description=test_description',
           '--async',
       ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None,
               None), ('HighScaleDeprecatedLocation', [
                   'instance_name',
                   '--location=us-central1-c',
                   '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
                   '--tier=HIGH_SCALE_SSD',
                   '--file-share=name=my_vol,capacity=100TB',
                   '--description=test_description',
                   '--async',
               ], 'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None,
                       None, None),
      ('STANDARDSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=STANDARD',
          '--description=test_description',
          '--async',
          '--flags-file=high-scale-file-share-minimal.json',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None,
       None), ('PREMIUMSingle', [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=PREMIUM',
           '--description=test_description',
           '--async',
           '--flags-file=high-scale-file-share-minimal.json',
       ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None,
               None))
  def testCreateInstance(self, args, expected_network, expected_range,
                         expected_vol_name, expected_capacity,
                         expected_source_snapshot, expected_source_backup,
                         expected_labels, expected_nfs_export_options):
    flags_file = util.GetFlagsFileFullPath(self.Resource, args)
    tier = util.ReturnTier(args)
    description = util.ReturnDescription(args)
    file_share_config = util.CreateFileShareConfig(
        messages=self.messages,
        flags_file=flags_file,
        expected_vol_name=expected_vol_name,
        expected_capacity=expected_capacity,
        expected_source_snapshot=expected_source_snapshot,
        expected_source_backup=expected_source_backup,
        expected_nfs_export_options=expected_nfs_export_options)
    instance = util.CreateFileShareInstance(
        messages=self.messages,
        tier=tier,
        expected_network=expected_network,
        expected_labels=expected_labels,
        expected_range=expected_range,
        expected_description=description)

    util.InstanceAddFileShareConfig(
        self.messages, instance, file_share_config=file_share_config)
    util.ExpectCreateInstance(
        messages=self.messages,
        mock_client=self.mock_client,
        parent=self.parent,
        name=self.name,
        op_name=self.op_name,
        config=instance)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('NoRange', [
          'instance_name', '--location=us-central1-c', '--async',
          '--network=name=test_network', '--tier=BASIC_HDD',
          '--file-share=name=my_vol,capacity=1TB,source-snapshot=snap,source-snapshot-region=us-central1',
          '--description=test_description'
      ], 'test_network', None, 'my_vol', 1024,
       'projects/fake-project/locations/us-central1/snapshots/snap'))
  def testCreateInstanceFromLegacySnapshot(self, args, expected_network,
                                           expected_range, expected_vol_name,
                                           expected_capacity,
                                           expected_source_snapshot):
    util.SetupExpectedInstance(
        self,
        expected_network,
        expected_range,
        expected_vol_name,
        expected_capacity,
        expected_source_snapshot=expected_source_snapshot)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('NoRange', [
          'instance_name', '--location=us-central1-c', '--async',
          '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB,source-snapshot=snap',
          '--description=test_description'
      ], 'test_network', None, 'my_vol', 1024,
       'projects/fake-project/locations/us-central1-c/snapshots/snap'))
  def testCreateInstanceFromSnapshot(self, args, expected_network,
                                     expected_range, expected_vol_name,
                                     expected_capacity,
                                     expected_source_snapshot):
    util.SetupExpectedInstance(
        self,
        expected_network,
        expected_range,
        expected_vol_name,
        expected_capacity,
        expected_source_snapshot=expected_source_snapshot)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('NoRange', [
          'instance_name', '--location=us-central1-c', '--async',
          '--network=name=test_network', '--tier=BASIC_HDD',
          '--file-share=name=my_vol,capacity=1TB,source-backup=backup,source-backup-region=us-central1',
          '--description=test_description'
      ], 'test_network', None, 'my_vol', 1024,
       'projects/fake-project/locations/us-central1/backups/backup'))
  def testCreateInstanceFromBackup(self, args, expected_network, expected_range,
                                   expected_vol_name, expected_capacity,
                                   expected_source_backup):
    util.SetupExpectedInstance(
        self,
        expected_network,
        expected_range,
        expected_vol_name,
        expected_capacity,
        expected_source_backup=expected_source_backup)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('MissingLocationNoDefault', handlers.ParseError, [
          'instance_name', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('MissingInstanceName', cli_test_base.MockArgumentError, [
          '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('BadCapacityUnits', cli_test_base.MockArgumentError, [
          'name', '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1C', '--async'
      ]), ('WithoutFileShareConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--network=name=test_network'
      ]), ('WithoutNetworkConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--file-share=name=my_vol,capacity=1TB'
      ]), ('InvalidTier', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=INVAlID_GARBAGE_Tier',
          '--file-share=name=my_vol,capacity=1TB',
          '--description=test_description', '--async'
      ]), ('InvalidFlagsFileAccessMode',
           calliope_exceptions.InvalidArgumentException, [
               'instance_name', '--zone=us-central1-c',
               '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
               '--tier=basic_hdd', '--flags-file=flag-access-mode-err.json',
               '--file-share=name=my_vol,capacity=1TB',
               '--description=test_description', '--async'
           ]),
      ('InvalidFlagsFileAccessModeYaml',
       calliope_exceptions.InvalidArgumentException, [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=basic_hdd', '--flags-file=flag-access-mode-err.yaml',
           '--file-share=name=my_vol,capacity=1TB',
           '--description=test_description', '--async'
       ]), ('InvalidParseErrYaml', cli_test_base.MockArgumentError, [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=basic_hdd', '--flags-file=flag-parse-err.yaml',
           '--file-share=name=my_vol,capacity=1TB',
           '--description=test_description', '--async'
       ]))
  def testErrors(self, expected_error, args):
    with self.assertRaises(expected_error):
      util.GetFlagsFileFullPath(self.Resource, args)
      self.RunCreate(*args)


class CloudFilestoreInstancesCreateBetaTest(CloudFilestoreInstancesCreateBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testWaitForCreate(self):
    file_share_config = util.CreateFileShareConfig(
        messages=self.messages,
        flags_file=None,
        expected_vol_name='my_vol',
        expected_capacity=1024,
        expected_source_snapshot=None,
        expected_source_backup=None,
        expected_nfs_export_options=None)
    instance = util.CreateFileShareInstance(
        messages=self.messages,
        tier='BASIC_HDD',
        expected_network='test_network',
        expected_labels=None,
        expected_range=None,
        expected_description='test_description')
    util.InstanceAddFileShareConfig(
        messages=self.messages,
        instance=instance,
        file_share_config=file_share_config)
    util.ExpectCreateInstance(
        messages=self.messages,
        mock_client=self.mock_client,
        parent=self.parent,
        name=self.name,
        op_name=self.op_name,
        config=instance)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(
            name=self.op_name),
        self.messages.Operation(name=self.op_name, done=True))
    self.RunCreate('instance_name', '--zone=us-central1-c',
                   '--network=name=test_network',
                   '--description=test_description',
                   '--file-share=name=my_vol,capacity=1TB')

  @parameterized.named_parameters(
      ('BasicWithLabels', [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_SSD', '--file-share=name=my_vol,capacity=8TB',
          '--description=test_description', '--async', '--labels=key1=value1'
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192, None, {
          'key1': 'value1'
      }, None), ('BasicFromBackup', [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_SSD',
          '--file-share=name=my_vol,capacity=8TB,source-backup=backup,source-backup-region=us-central1',
          '--description=test_description', '--async', '--labels=key1=value1'
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192,
                 'projects/fake-project/locations/us-central1/backups/backup', {
                     'key1': 'value1'
                 }, None),
      ('HighScaleWithLabels',
       [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD', '--file-share=name=my_vol,capacity=100TB',
           '--description=test_description', '--async', '--labels=key1=value1'
       ],
       'test_network', '10.0.0.0/23', 'my_vol', 102400, None, {
           'key1': 'value1'
       },
       None), (
           'FlagsFilePriority',
           [
               'instance_name',
               '--zone=us-central1-c',
               '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
               '--tier=HIGH_SCALE_SSD',
               '--file-share=name=my_vol,capacity=100TB',
               '--description=test_description',
               '--async',
               '--flags-file=file-share-export-dual-options.json',
           ],
           'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None),
      ('FlagsFilePriorityYaml',
       [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--file-share=name=my_vol,capacity=100TB',
           '--description=test_description',
           '--async',
           '--flags-file=file-share-export-dual-options.yaml',
       ],
       'test_network', '10.0.0.0/23', 'my_vol', 102400, None, None, None), (
           'BasicNoRange',
           [
               'instance_name',
               '--zone=us-central1-c',
               '--async',
               '--network=name=test_network', '--tier=STANDARD',
               '--file-share=name=my_vol,capacity=2TB',
               '--description=test_description'
           ],
           'test_network',
           None, 'my_vol', 2048,
           None, None,
           None),
      ('BasicSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--description=test_description',
          '--async',
          '--flags-file=file-share-export-dual-options.json',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 8192, None, None, None),
      ('BasicNfsExportOptions', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--flags-file=file-share-export-rw-squash-ip.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 1024, None, None, None),
      ('BasicNfsExportOptionsGIDUID', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--flags-file=file-share-export-uid-gid.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 1024, None, None, None),
      ('BasicDeprecatedLocation', [
          'instance_name',
          '--location=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=BASIC_HDD',
          '--file-share=name=my_vol,capacity=1TB',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 1024, None, None,
       None), ('HighScaleSingle', [
           'instance_name',
           '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/23',
           '--tier=HIGH_SCALE_SSD',
           '--description=test_description',
           '--async',
           '--flags-file=high-scale-file-share-minimal.json',
       ], 'test_network',
               '10.0.0.0/23', 'my_vol', 102400, None, None, None),
      ('HighScaleNfsExportOptions', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=HIGH_SCALE_SSD',
          '--flags-file=high-scale-file-share-export-rw-squash-ip.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None),
      ('MultipleNfsExportOptions', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=HIGH_SCALE_SSD',
          '--flags-file=high-scale-file-share-export-dual-options.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None),
      ('HighScaleNfsExportOptionsGIDUID', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=HIGH_SCALE_SSD',
          '--flags-file=high-scale-file-share-export-uid-gid.json',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None),
      ('HighScaleDeprecatedLocation', [
          'instance_name',
          '--location=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=HIGH_SCALE_SSD',
          '--file-share=name=my_vol,capacity=100TB',
          '--description=test_description',
          '--async',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None),
      ('STANDARDSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=STANDARD',
          '--description=test_description',
          '--async',
          '--flags-file=high-scale-file-share-minimal.json',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None),
      ('PREMIUMSingle', [
          'instance_name',
          '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=PREMIUM',
          '--description=test_description',
          '--async',
          '--flags-file=high-scale-file-share-minimal.json',
      ], 'test_network', '10.0.0.0/29', 'my_vol', 102400, None, None, None))
  def testCreateInstance(self, args, expected_network, expected_range,
                         expected_vol_name, expected_capacity,
                         expected_source_backup, expected_labels,
                         expected_nfs_export_options):
    flags_file = util.GetFlagsFileFullPath(self.Resource, args)
    tier = util.ReturnTier(args)
    description = util.ReturnDescription(args)
    file_share_config = util.CreateFileShareConfig(
        messages=self.messages,
        flags_file=flags_file,
        expected_vol_name=expected_vol_name,
        expected_capacity=expected_capacity,
        expected_source_snapshot='',
        expected_source_backup=expected_source_backup,
        expected_nfs_export_options=expected_nfs_export_options)
    instance = util.CreateFileShareInstance(
        messages=self.messages,
        tier=tier,
        expected_network=expected_network,
        expected_labels=expected_labels,
        expected_range=expected_range,
        expected_description=description)

    util.InstanceAddFileShareConfig(
        self.messages, instance, file_share_config=file_share_config)
    util.ExpectCreateInstance(
        messages=self.messages,
        mock_client=self.mock_client,
        parent=self.parent,
        name=self.name,
        op_name=self.op_name,
        config=instance)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('NoRange', [
          'instance_name', '--location=us-central1-c', '--async',
          '--network=name=test_network', '--tier=BASIC_HDD',
          '--file-share=name=my_vol,capacity=1TB,source-backup=backup,source-backup-region=us-central1',
          '--description=test_description'
      ], 'test_network', None, 'my_vol', 1024,
       'projects/fake-project/locations/us-central1/backups/backup'))
  def testCreateInstanceFromBackup(self, args, expected_network, expected_range,
                                   expected_vol_name, expected_capacity,
                                   expected_source_backup):
    util.SetupExpectedInstance(
        self,
        expected_network,
        expected_range,
        expected_vol_name,
        expected_capacity,
        expected_source_backup=expected_source_backup)
    self.RunCreate(*args)
    self.AssertErrContains(_GetListCommandOutput(self.track.prefix))

  @parameterized.named_parameters(
      ('MissingLocationNoDefault', handlers.ParseError, [
          'instance_name', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('MissingInstanceName', cli_test_base.MockArgumentError, [
          '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1TB', '--async'
      ]), ('BadCapacityUnits', cli_test_base.MockArgumentError, [
          'name', '--zone=us-central1-c', '--network=name=test_network',
          '--file-share=name=my_vol,capacity=1C', '--async'
      ]), ('WithoutFileShareConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--network=name=test_network'
      ]), ('WithoutNetworkConfig', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c', '--async',
          '--file-share=name=my_vol,capacity=1TB'
      ]), ('InvalidTier', cli_test_base.MockArgumentError, [
          'instance_name', '--zone=us-central1-c',
          '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
          '--tier=INVAlID_GARBAGE_Tier',
          '--file-share=name=my_vol,capacity=1TB',
          '--description=test_description', '--async'
      ]), ('InvalidFlagsFileAccessMode',
           calliope_exceptions.InvalidArgumentException, [
               'instance_name', '--zone=us-central1-c',
               '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
               '--tier=basic_hdd', '--flags-file=flag-access-mode-err.json',
               '--file-share=name=my_vol,capacity=1TB',
               '--description=test_description', '--async'
           ]),
      ('InvalidFlagsFileAccessModeYaml',
       calliope_exceptions.InvalidArgumentException, [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=basic_hdd', '--flags-file=flag-access-mode-err.yaml',
           '--file-share=name=my_vol,capacity=1TB',
           '--description=test_description', '--async'
       ]), ('InvalidParseErrYaml', cli_test_base.MockArgumentError, [
           'instance_name', '--zone=us-central1-c',
           '--network=name=test_network,reserved-ip-range=10.0.0.0/29',
           '--tier=basic_hdd', '--flags-file=flag-parse-err.yaml',
           '--file-share=name=my_vol,capacity=1TB',
           '--description=test_description', '--async'
       ]))

  def testErrors(self, expected_error, args):
    with self.assertRaises(expected_error):
      util.GetFlagsFileFullPath(self.Resource, args)
      self.RunCreate(*args)

if __name__ == '__main__':
  test_case.main()
