# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Tests for the 'gcloud dns record-sets export' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.dns import export_util
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsExportTest(base.DnsMockTest):

  def SetUp(self):
    self.result_file_path = os.path.join(self.temp_path, 'exported')
    self.zone_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-exported.zone')
    self.yaml_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-exported.yaml')

  def testWriteToZoneFile(self):
    with open(self.result_file_path, 'w') as zone_file:
      export_util.WriteToZoneFile(zone_file, util.GetRecordSetsForExport(),
                                  'zone.com.')

    with open(self.result_file_path) as results:
      with open(self.zone_file_path) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def testWriteToYamlFile(self):
    with open(self.result_file_path, 'w') as yaml_file:
      export_util.WriteToYamlFile(yaml_file, util.GetRecordSetsForExport())

    with open(self.result_file_path) as results:
      with open(self.yaml_file_path) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def _ExportToFileHelper(self, expected_file, flags=''):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.managedZones.Get.Expect(
        self.messages.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    self.mocked_dns_v1.resourceRecordSets.List.Expect(
        self.messages.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages.ResourceRecordSetsListResponse(
            rrsets=util.GetRecordSetsForExport()))

    self.Run('dns record-sets export -z {0} {1} {2}'.format(
        test_zone.name, self.result_file_path, flags))
    with open(self.result_file_path) as results:
      with open(expected_file) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def testExportToZoneFile(self):
    self._ExportToFileHelper(self.zone_file_path, '--zone-file-format')

  def testExportToYamlFile(self):
    self._ExportToFileHelper(self.yaml_file_path)

  def testErrorDuringExport(self):
    write_yaml_mock = self.StartObjectPatch(export_util, 'WriteToYamlFile')
    write_yaml_mock.side_effect = Exception()

    with self.assertRaises(export_util.UnableToExportRecordsToFile):
      self._ExportToFileHelper(self.yaml_file_path)


class RecordSetsExportBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.result_file_path = os.path.join(self.temp_path, 'exported')
    self.zone_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v1beta2',
        'zone.com-exported.zone')
    self.yaml_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v1beta2',
        'zone.com-exported.yaml')

  def testWriteToZoneFile(self):
    with open(self.result_file_path, 'w') as zone_file:
      export_util.WriteToZoneFile(zone_file, util_beta.GetRecordSetsForExport(),
                                  'zone.com.')

    with open(self.result_file_path) as results:
      with open(self.zone_file_path) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def testWriteToYamlFile(self):
    with open(self.result_file_path, 'w') as yaml_file:
      export_util.WriteToYamlFile(yaml_file, util_beta.GetRecordSetsForExport())

    with open(self.result_file_path) as results:
      with open(self.yaml_file_path) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def _ExportToFileHelper(self, expected_file, flags=''):
    test_zone = util_beta.GetManagedZones()[0]
    self.mocked_dns_client.managedZones.Get.Expect(
        self.messages_beta.DnsManagedZonesGetRequest(
            managedZone=test_zone.name,
            project=self.Project()),
        test_zone)

    self.mocked_dns_client.resourceRecordSets.List.Expect(
        self.messages_beta.DnsResourceRecordSetsListRequest(
            project=self.Project(),
            managedZone=test_zone.name,
            maxResults=100),
        self.messages_beta.ResourceRecordSetsListResponse(
            rrsets=util_beta.GetRecordSetsForExport()))

    self.Run('dns record-sets export -z {0} {1} {2}'.format(
        test_zone.name, self.result_file_path, flags))
    with open(self.result_file_path) as results:
      with open(expected_file) as expected:
        self.assertEqual(expected.read().splitlines(),
                         results.read().splitlines())

  def testExportToZoneFile(self):
    self._ExportToFileHelper(self.zone_file_path, '--zone-file-format')

  def testExportToYamlFile(self):
    self._ExportToFileHelper(self.yaml_file_path)


if __name__ == '__main__':
  test_case.main()
