# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for Cloud Filestore instances update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.filestore import base

import six


class CloudFilestoreInstancesUpdateTest(base.CloudFilestoreUnitTestBase,
                                        parameterized.TestCase):

  _TRACK = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SetUpTrack(self._TRACK)
    self.name = (
        'projects/{}/locations/us-central1-c/instances/instance_name'.format(
            self.Project()))
    self.op_name = 'projects/{}/locations/us-central1-c/operations/op'.format(
        self.Project())

  def RunUpdate(self, *args):
    return self.Run(['filestore', 'instances', 'update'] + list(args))

  def DefaultFileShare(self):
    return [
        self.messages.FileShareConfig(
            name='my_vol',
            capacityGb=1024)
    ]

  def MakeLabels(self, labels_dict):
    return self.messages.Instance.LabelsValue(
        additionalProperties=[
            self.messages.Instance.LabelsValue.AdditionalProperty(
                key=key, value=value)
            for key, value in six.iteritems(labels_dict)])

  def MakeConfig(self, name, file_share, labels=None):
    return self.messages.Instance(
        name=name,
        fileShares=file_share,
        tier=self.messages.Instance.TierValueValuesEnum.STANDARD,
        networks=[
            self.messages.NetworkConfig(
                network='test_network', reservedIpRange='10.0.0.0/29')
        ],
        description='test_description',
        labels=labels)

  def ExpectInstanceGetRequest(self, existing_config):
    self.mock_client.projects_locations_instances.Get.Expect(
        self.messages.FileProjectsLocationsInstancesGetRequest(name=self.name),
        existing_config)

  def ExpectInstancePatchRequest(self, config, update_mask):
    self.mock_client.projects_locations_instances.Patch.Expect(
        self.messages.FileProjectsLocationsInstancesPatchRequest(
            name=self.name, instance=config, updateMask=update_mask),
        self.messages.Operation(
            name=self.op_name))

  def testUpdateFileShare(self):
    existing_config = self.MakeConfig(self.name, self.DefaultFileShare())
    self.ExpectInstanceGetRequest(existing_config)

    new_file_shares = [self.messages.FileShareConfig(name='my_vol',
                                                     capacityGb=2048)]
    update_mask = 'fileShares'
    config = self.MakeConfig(self.name, new_file_shares)
    self.ExpectInstancePatchRequest(config, update_mask)

    self.RunUpdate(
        'instance_name', '--zone=us-central1-c',
        '--file-share=name=my_vol,capacity=2TB', '--async')

  @parameterized.named_parameters(
      ('NotUpsized', 'Must resize the file share to a larger capacity',
       ['--file-share=name=my_vol,capacity=1TB']),
      ('NameMismatch', 'Must resize an existing file share',
       ['--file-share=name=my_vol_2,capacity=3TB']))
  def testUpdateInvalidFileShare(self, expected_regex, args):
    existing_config = self.MakeConfig(self.name,
                                      [self.messages.FileShareConfig(
                                          name='my_vol',
                                          capacityGb=2048)])
    self.ExpectInstanceGetRequest(existing_config)
    final_args = ['instance_name', '--zone=us-central1-c'] + args
    with self.assertRaisesRegex(exceptions.InvalidArgumentException,
                                expected_regex):
      self.RunUpdate(*final_args)

  def testUpdateLabelsAndDescription(self):
    existing_config = self.MakeConfig(
        self.name, self.DefaultFileShare(),
        labels=self.MakeLabels({'key1': 'value1'}))
    self.ExpectInstanceGetRequest(existing_config)

    config = self.MakeConfig(
        self.name, self.DefaultFileShare(),
        labels=self.MakeLabels({'key2': 'value2'}))
    config.description = 'New description'
    update_mask = 'description,labels'
    self.ExpectInstancePatchRequest(config, update_mask)

    self.RunUpdate(
        'instance_name', '--zone=us-central1-c',
        '--remove-labels', 'key1', '--update-labels', 'key2=value2',
        '--description', 'New description', '--async')

  def testClearLabels(self):
    existing_config = self.MakeConfig(
        self.name, self.DefaultFileShare(),
        labels=self.MakeLabels({'key1': 'value1'}))
    self.ExpectInstanceGetRequest(existing_config)

    config = self.MakeConfig(self.name, self.DefaultFileShare(),
                             labels=self.messages.Instance.LabelsValue())
    update_mask = 'labels'
    self.ExpectInstancePatchRequest(config, update_mask)

    self.RunUpdate(
        'instance_name', '--zone=us-central1-c',
        '--clear-labels', '--async')

  def testClearLabelsWithDeprecatedLocation(self):
    existing_config = self.MakeConfig(
        self.name, self.DefaultFileShare(),
        labels=self.MakeLabels({'key1': 'value1'}))
    self.ExpectInstanceGetRequest(existing_config)

    config = self.MakeConfig(self.name, self.DefaultFileShare(),
                             labels=self.messages.Instance.LabelsValue())
    update_mask = 'labels'
    self.ExpectInstancePatchRequest(config, update_mask)

    self.RunUpdate(
        'instance_name', '--location=us-central1-c',
        '--clear-labels', '--async')

  def testWaitForUpdate(self):
    existing_config = self.MakeConfig(self.name, self.DefaultFileShare())
    self.ExpectInstanceGetRequest(existing_config)

    new_file_shares = [self.messages.FileShareConfig(name='my_vol',
                                                     capacityGb=2048)]
    update_mask = 'fileShares'
    config = self.MakeConfig(self.name, new_file_shares)
    op_name = 'projects/{}/locations/us-central1-c/operations/op'.format(
        self.Project())
    self.ExpectInstancePatchRequest(config, update_mask)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.FileProjectsLocationsOperationsGetRequest(name=op_name),
        self.messages.Operation(name=op_name, done=True))

    self.RunUpdate(
        'instance_name', '--zone=us-central1-c',
        '--file-share=name=my_vol,capacity=2TB')

  def testUsingInvalidCapacity(self):
    # Argparse throws error if the value is below the minimum.
    with self.assertRaisesRegexp(cli_test_base.MockArgumentError, '1TB'):
      self.RunUpdate(
          'instance_name', '--zone=us-central1-c',
          '--file-share=name=my_vol,capacity=100GB')


class CloudFilestoreInstancesUpdateBetaTest(CloudFilestoreInstancesUpdateTest):

  _TRACK = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
