# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Integration tests for the 'gcloud dns' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.dns import base
import six


class ProjectInfoTest(base.DnsTest):

  def testDescribe(self):
    self.Run(
        'dns project-info describe {0}'.format(self.Project()))
    self.AssertOutputContains("""\
id: {0}
kind: dns#project
""".format(self.Project()))


class ManagedZonesTest(base.DnsTest):

  def SetUp(self):
    messages = core_apis.GetMessagesModule('dns', 'v1')
    self.test_zone = messages.ManagedZone(
        description='Zone!',
        dnsName=six.text_type(
            next(
                e2e_utils.GetResourceNameGenerator(
                    suffix='.com.',
                    hash_len=13,
                    delimiter='',
                    timestamp_format=None))),
        kind='dns#managedZone',
        name=six.text_type(
            next(e2e_utils.GetResourceNameGenerator(prefix='zone'))),
        nameServers=[])

    self.Run(
        'dns managed-zones create {0} --dns-name {1} --description {2}'.format(
            self.test_zone.name, self.test_zone.dnsName,
            self.test_zone.description))
    self.AssertErrContains("""\
Created [https://dns.googleapis.com/dns/v1/projects/{0}/managedZones/{1}].
""".format(self.Project(), self.test_zone.name))

  def TearDown(self):
    self.Run('dns managed-zones delete {0}'.format(self.test_zone.name))
    self.AssertErrContains("""\
Deleted [https://dns.googleapis.com/dns/v1/projects/{0}/managedZones/{1}].
""".format(self.Project(), self.test_zone.name))

  def testList(self):
    self.Run('dns managed-zones list')
    self.AssertOutputContains("""\
{0}   {1}  Zone! public
""".format(self.test_zone.name, self.test_zone.dnsName), normalize_space=True)

  def testDescribe(self):
    self.Run('dns managed-zones describe {0}'.format(self.test_zone.name))
    self.AssertOutputContains("""\
description: Zone!
dnsName: {0}
""".format(self.test_zone.dnsName))
    self.AssertOutputContains("""\
kind: dns#managedZone
name: {0}
nameServers:
""".format(self.test_zone.name))


class RecordSetsTest(ManagedZonesTest):

  def testList(self):
    self.Run('dns record-sets list -z {0}'.format(self.test_zone.name))
    self.AssertOutputContains("""\
NAME        TYPE  TTL    DATA
{0}  NS""".format(self.test_zone.dnsName), normalize_space=True)
    self.AssertOutputContains("""\
{0}  SOA""".format(self.test_zone.dnsName))

  def _WaitForChange(self, change_id):
    cmd = 'dns record-sets changes describe -z {0} {1}'.format(
        self.test_zone.name, change_id).split()
    self.ReRunUntilOutputContains(
        cmd, 'status: done', max_retrials=4, sleep_ms=10000, max_wait_ms=400000,
        exponential_sleep_multiplier=3.0)

  def testImportExport(self):
    # Prepare zone file for import
    import_file_path = self.Touch(directory=self.temp_path)
    with open(import_file_path, 'w') as import_file:
      import_file.write("""\
@          IN  MX    20 mail2.{0}
@          IN  MX    50 mail3
{0}  IN  A     192.0.2.1
""".format(self.test_zone.dnsName))

    # Perform import and make assertions
    self.Run('dns record-sets import -z {0} --zone-file-format {1}'.format(
        self.test_zone.name, import_file_path))
    self.AssertErrContains("""\
Imported record-sets from [{1}] into managed-zone [{2}].
Created [https://dns.googleapis.com/dns/v1/projects/{0}/managedZones/{2}/changes/1].
""".format(self.Project(), import_file_path, self.test_zone.name))

    # Wait for import change to be completed
    self._WaitForChange(1)

    # Perform export and make assertions
    export_file_path = import_file_path
    self.Run('dns record-sets export -z {0} --zone-file-format {1}'.format(
        self.test_zone.name, export_file_path))
    self.AssertErrContains("""\
Exported record-sets to [{0}].
""".format(export_file_path))
    with open(export_file_path, 'r') as export_file:
      export_result = export_file.read()
    self.assertTrue('{0} 0 IN A 192.0.2.1\n'.format(self.test_zone.dnsName)
                    in export_result)
    self.assertTrue('{0} 0 IN MX 20 mail2.{0}\n'.format(self.test_zone.dnsName)
                    in export_result)
    self.assertTrue('{0} 0 IN MX 50 mail3.{0}\n'.format(self.test_zone.dnsName)
                    in export_result)

    # Clean up i.e. import with an empty file using --delete-all-existing
    with open(import_file_path, 'w') as import_file:
      import_file.write('')
    self.Run('dns record-sets import -z {0} {1} --delete-all-existing'.format(
        self.test_zone.name, import_file_path))

    # Wait for clean up change to be completed
    self._WaitForChange(2)

  def testTransaction(self):
    # Start transaction and assert
    self.Run('dns record-sets transaction start -z {0}'.format(
        self.test_zone.name))
    self.AssertErrContains("""\
Transaction started [transaction.yaml].
""")

    # Transaction add and assert
    self.Run('dns record-sets transaction add -z {0} --name="ftp.{1}" '
             '--ttl=2160 --type=CNAME "{2}"'.format(
                 self.test_zone.name,
                 # Test ommision of trailing dot in the DNS name parameter
                 self.test_zone.dnsName[:-1],
                 self.test_zone.dnsName))
    self.AssertErrContains("""\
Record addition appended to transaction at [transaction.yaml].
""")

    # Transaction execute and assert
    self.Run('dns record-sets transaction execute -z {0}'.format(
        self.test_zone.name))
    self.AssertErrContains("""\
Executed transaction [transaction.yaml] for managed-zone [{1}].
Created [https://dns.googleapis.com/dns/v1/projects/{0}/managedZones/{1}/changes/1].
""".format(self.Project(), self.test_zone.name))

    # Wait for transaction change to be completed
    self._WaitForChange(1)

    # Start transaction and assert
    self.Run('dns record-sets transaction start -z {0}'.format(
        self.test_zone.name))
    self.AssertErrContains("""\
Transaction started [transaction.yaml].
""")

    # Transaction remove and assert
    self.Run('dns record-sets transaction remove -z {0} --name="ftp.{1}" '
             '--ttl=2160 --type=CNAME "{1}"'.format(
                 self.test_zone.name, self.test_zone.dnsName))
    self.AssertErrContains("""\
Record removal appended to transaction at [transaction.yaml].
""")

    # Transaction execute and assert
    self.Run('dns record-sets transaction execute -z {0}'.format(
        self.test_zone.name))
    self.AssertErrContains("""\
Executed transaction [transaction.yaml] for managed-zone [{1}].
Created [https://dns.googleapis.com/dns/v1/projects/{0}/managedZones/{1}/changes/2].
""".format(self.Project(), self.test_zone.name))

    # Wait for transaction change to be completed
    self._WaitForChange(2)

if __name__ == '__main__':
  test_case.main()
