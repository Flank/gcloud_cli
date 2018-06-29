# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for the 'gcloud dns record-sets import' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import io
import textwrap

from dns import rdatatype
from googlecloudsdk.api_lib.dns import import_util
from googlecloudsdk.calliope.exceptions import ToolException
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util
from tests.lib.surface.dns import util_beta


class RecordSetsImportTest(base.DnsMockTest):

  def SetUp(self):
    self.zone_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-to-import.zone')
    self.crnl_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-to-import.crnl')
    self.yaml_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-to-import.yaml')
    self.zone_file_path_no_conflicts = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-to-import-no-conflicts.zone')
    self.yaml_file_path_no_conflicts = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data',
        'zone.com-to-import-no-conflicts.yaml')

  def testRecordSetsFromZoneFile(self):
    zone_file = io.open(self.zone_file_path, mode='rt')
    rsets = import_util.RecordSetsFromZoneFile(zone_file, 'zone.com.')
    self.assertEqual(util.GetImportedRecordSets(), rsets)
    zone_file.close()

  def testRecordSetsFromZoneFileCRNL(self):
    zone_file = io.open(self.crnl_file_path, mode='rt')
    rsets = import_util.RecordSetsFromZoneFile(zone_file, 'zone.com.')
    self.assertEqual(util.GetImportedRecordSets(), rsets)
    zone_file.close()

  def testRecordSetsFromYamlFile(self):
    yaml_file = io.open(self.yaml_file_path, mode='rt')
    rsets = import_util.RecordSetsFromYamlFile(yaml_file)
    self.assertEqual(util.GetImportedRecordSets(), rsets)
    yaml_file.close()

  def testComputeChangeConflicts(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util.GetRecordSets())
    with self.assertRaises(ToolException) as context:
      import_util.ComputeChange(
          current_record_sets,
          util.GetImportedRecordSets(),
          False, 'zone.com.', True)
      self.assertEqual(
          context.exception.message,
          'Conflicting records for the following (name type): '
          '[\'mail.zone.com. A\', \'zone.com. A\', \'zone.com. SOA\']')

  def testComputeChangeNoConflicts(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util.GetRecordSets())
    change = import_util.ComputeChange(
        current_record_sets, util.GetImportedRecordSetsWithoutConflicts(),
        False, 'zone.com.', True)
    self.assertEqual(util.GetImportChange(), change)

  def testComputeChangeReplaceAll(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util.GetRecordSets())
    change = import_util.ComputeChange(
        current_record_sets,
        util.GetImportedRecordSets(),
        True, 'zone.com.', True)
    self.assertEqual(util.GetImportReplaceChange(), change)
    change = import_util.ComputeChange(
        current_record_sets,
        util.GetImportedRecordSets(),
        True,
        'zone.com.',
        False)

    self.assertEqual(util.GetImportReplaceChangeNoReplaceOrigin(), change)

  def testComputeChangeIdenticalRecordsReplaceAll(self):
    change = import_util.ComputeChange(
        util.GetImportedRecordSets(),
        util.GetImportedRecordSets(),
        replace_all=True)
    self.assertEqual(None, change)

  def testComputeChangeSOASerialIncrementing(self):
    change = import_util.ComputeChange(util.GetSOASequence()[0],
                                       util.GetImportableRecord())
    self.assertEqual(list(util.GetSOASequence()[0].values()), change.deletions)
    self.assertEqual(list(util.GetImportableRecord().values()) +
                     list(util.GetSOASequence()[1].values()),
                     change.additions)
    change = import_util.ComputeChange(util.GetSOASequence()[1],
                                       util.GetImportableRecord())
    self.assertEqual(list(util.GetSOASequence()[1].values()), change.deletions)
    self.assertEqual(list(util.GetImportableRecord().values()) +
                     list(util.GetSOASequence()[2].values()),
                     change.additions)

  def _ImportFromFileHelper(self, file_path, flags=None):
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
            rrsets=util.GetRecordSets()))

    self.mocked_dns_v1.changes.Create.Expect(
        self.messages.DnsChangesCreateRequest(
            change=util.GetImportChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util.GetImportChangeAfterCreation())

    self.Run(['dns', 'record-sets', 'import', '-z', test_zone.name, file_path] +
             (flags or []))
    self.AssertOutputContains(textwrap.dedent("""\
    ID  START_TIME  STATUS
    1   today now   pending
    """))
    self.AssertErrContains((
        'Created [https://www.googleapis.com/dns/v1/projects/{0}/'
        'managedZones/mz/changes/1]').format(self.Project()))

  def testImportFromYamlFile(self):
    self._ImportFromFileHelper(self.yaml_file_path_no_conflicts,
                               ['--replace-origin-ns'])

  def testImportFromZoneFile(self):
    self._ImportFromFileHelper(self.zone_file_path_no_conflicts,
                               ['--zone-file-format', '--replace-origin-ns'])

  def _ImportReplaceFromFileHelper(self, file_path, flags=None):
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
            rrsets=util.GetRecordSets()))

    self.mocked_dns_v1.changes.Create.Expect(
        self.messages.DnsChangesCreateRequest(
            change=util.GetImportReplaceChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util.GetImportReplaceChangeAfterCreation())

    self.Run(['dns', 'record-sets', 'import', '-z', test_zone.name, file_path,
              '--delete-all-existing', '--replace-origin-ns'] + (flags or []))
    self.AssertOutputContains(textwrap.dedent("""\
    ID  START_TIME        STATUS
    2   today 5 mins ago  done
    """))
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz/changes/2].
""".format(self.api_version, self.Project()))

  def testImportReplaceFromYamlFile(self):
    self._ImportReplaceFromFileHelper(self.yaml_file_path)

  def testImportReplaceFromZoneFile(self):
    self._ImportReplaceFromFileHelper(self.zone_file_path,
                                      ['--zone-file-format'])

  def testFilterNSRecordsTest(self):

    # Test that records that are not of NS return true
    self.assertFalse(import_util._FilterOutRecord('www.zone.com',
                                                  rdatatype.A,
                                                  'zone.com'))

    # Test that we return false when the name matchin the
    # origin and override is false
    self.assertTrue(import_util._FilterOutRecord('zone.com',
                                                 rdatatype.NS,
                                                 'zone.com'))

    # Test that we return true when the name matchin the
    # origin and override is true
    self.assertFalse(import_util._FilterOutRecord('zone.com',
                                                  rdatatype.NS,
                                                  'zone.com',
                                                  True))

    # Test that we allow NS records for a sub zone
    self.assertFalse(import_util._FilterOutRecord('sub.zone.com',
                                                  rdatatype.NS,
                                                  'zone.com'))


class RecordSetsImportBetaTest(base.DnsMockBetaTest):

  def SetUp(self):
    self.zone_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-to-import.zone')
    self.yaml_file_path = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-to-import.yaml')
    self.zone_file_path_no_conflicts = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-to-import-no-conflicts.zone')
    self.yaml_file_path_no_conflicts = sdk_test_base.SdkBase.Resource(
        'tests', 'unit', 'surface', 'dns', 'test_data', 'v2beta1',
        'zone.com-to-import-no-conflicts.yaml')

  def testRecordSetsFromZoneFile(self):
    zone_file = io.open(self.zone_file_path, mode='rt')
    rsets = import_util.RecordSetsFromZoneFile(
        zone_file, 'zone.com.', api_version=self.api_version)
    self.assertEqual(util_beta.GetImportedRecordSets(), rsets)
    zone_file.close()

  def testRecordSetsFromYamlFile(self):
    yaml_file = io.open(self.yaml_file_path, mode='rt')
    rsets = import_util.RecordSetsFromYamlFile(
        yaml_file, api_version=self.api_version)
    self.assertEqual(util_beta.GetImportedRecordSets(), rsets)
    yaml_file.close()

  def testComputeChangeConflicts(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util_beta.GetRecordSets())
    with self.assertRaises(ToolException) as context:
      import_util.ComputeChange(
          current_record_sets,
          util_beta.GetImportedRecordSets(),
          False, 'zone.com.', True,
          api_version=self.api_version)
      self.assertEqual(
          context.exception.message,
          'Conflicting records for the following (name type): '
          '[\'mail.zone.com. A\', \'zone.com. A\', \'zone.com. SOA\']')

  def testComputeChangeNoConflicts(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util_beta.GetRecordSets())
    change = import_util.ComputeChange(
        current_record_sets, util_beta.GetImportedRecordSetsWithoutConflicts(),
        False, 'zone.com.', True,
        api_version=self.api_version)
    self.assertEqual(util_beta.GetImportChange(), change)

  def testComputeChangeReplaceAll(self):
    current_record_sets = dict(
        ((record_set.name, record_set.type), record_set)
        for record_set in util_beta.GetRecordSets())
    change = import_util.ComputeChange(
        current_record_sets,
        util_beta.GetImportedRecordSets(),
        True, 'zone.com.', True,
        api_version=self.api_version)
    self.assertEqual(util_beta.GetImportReplaceChange(), change)
    change = import_util.ComputeChange(
        current_record_sets,
        util_beta.GetImportedRecordSets(),
        True,
        'zone.com.',
        False,
        api_version=self.api_version)

    self.assertEqual(util_beta.GetImportReplaceChangeNoReplaceOrigin(), change)

  def testComputeChangeIdenticalRecordsReplaceAll(self):
    change = import_util.ComputeChange(
        util_beta.GetImportedRecordSets(),
        util_beta.GetImportedRecordSets(),
        replace_all=True,
        api_version=self.api_version)
    self.assertEqual(None, change)

  def testComputeChangeSOASerialIncrementing(self):
    change = import_util.ComputeChange(
        util_beta.GetSOASequence()[0],
        util_beta.GetImportableRecord(),
        api_version=self.api_version)
    self.assertEqual(
        list(util_beta.GetSOASequence()[0].values()), change.deletions)
    self.assertEqual(
        list(util_beta.GetImportableRecord().values()) + list(
            util_beta.GetSOASequence()[1].values()), change.additions)
    change = import_util.ComputeChange(util_beta.GetSOASequence()[1],
                                       util_beta.GetImportableRecord(),
                                       api_version=self.api_version)
    self.assertEqual(
        list(util_beta.GetSOASequence()[1].values()), change.deletions)
    self.assertEqual(
        list(util_beta.GetImportableRecord().values()) + list(
            util_beta.GetSOASequence()[2].values()), change.additions)

  def _ImportFromFileHelper(self, file_path, flags=None):
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
            rrsets=util_beta.GetRecordSets()))

    self.mocked_dns_client.changes.Create.Expect(
        self.messages_beta.DnsChangesCreateRequest(
            change=util_beta.GetImportChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util_beta.GetImportChangeAfterCreation())

    self.Run(['dns', 'record-sets', 'import', '-z', test_zone.name, file_path] +
             (flags or []))
    self.AssertOutputContains("""\
ID  START_TIME  STATUS
1   today now   pending
""", normalize_space=True)
    self.AssertErrContains((
        'Created [https://www.googleapis.com/dns/{0}/projects/{1}/'
        'managedZones/mz/changes/1]').format(self.api_version, self.Project()))

  def testImportFromYamlFile(self):
    self._ImportFromFileHelper(self.yaml_file_path_no_conflicts,
                               ['--replace-origin-ns'])

  def testImportFromZoneFile(self):
    self._ImportFromFileHelper(self.zone_file_path_no_conflicts,
                               ['--zone-file-format', '--replace-origin-ns'])

  def _ImportReplaceFromFileHelper(self, file_path, flags=None):
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
            rrsets=util_beta.GetRecordSets()))

    self.mocked_dns_client.changes.Create.Expect(
        self.messages_beta.DnsChangesCreateRequest(
            change=util_beta.GetImportReplaceChange(),
            managedZone=test_zone.name,
            project=self.Project()),
        util_beta.GetImportReplaceChangeAfterCreation())

    self.Run(['dns', 'record-sets', 'import', '-z', test_zone.name, file_path,
              '--delete-all-existing', '--replace-origin-ns'] + (flags or []))
    self.AssertOutputContains("""\
ID  START_TIME        STATUS
2   today 5 mins ago  done
""", normalize_space=True)
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{0}/projects/{1}/managedZones/mz/changes/2].
""".format(self.api_version, self.Project()))

  def testImportReplaceFromYamlFile(self):
    self._ImportReplaceFromFileHelper(self.yaml_file_path)

  def testImportReplaceFromZoneFile(self):
    self._ImportReplaceFromFileHelper(self.zone_file_path,
                                      ['--zone-file-format'])

  def testFilterNSRecordsTest(self):

    # Test that records that are not of NS return true
    self.assertFalse(import_util._FilterOutRecord('www.zone.com',
                                                  rdatatype.A,
                                                  'zone.com'))

    # Test that we return false when the name matchin the
    # origin and override is false
    self.assertTrue(import_util._FilterOutRecord('zone.com',
                                                 rdatatype.NS,
                                                 'zone.com'))

    # Test that we return true when the name matchin the
    # origin and override is true
    self.assertFalse(import_util._FilterOutRecord('zone.com',
                                                  rdatatype.NS,
                                                  'zone.com',
                                                  True))

    # Test that we allow NS records for a sub zone
    self.assertFalse(import_util._FilterOutRecord('sub.zone.com',
                                                  rdatatype.NS,
                                                  'zone.com'))


if __name__ == '__main__':
  test_case.main()
