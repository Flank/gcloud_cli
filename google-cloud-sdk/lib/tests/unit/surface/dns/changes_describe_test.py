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

"""Tests that exercise the 'gcloud dns record-sets changes describe' command."""

import StringIO

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_printer
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util


class ChangesDescribeTest(base.DnsMockTest):

  messages = core_apis.GetMessagesModule('dns', 'v1')

  def testDescribe(self):
    test_zone = util.GetManagedZones()[0]
    test_change = util.GetChanges()[1]
    self.mocked_dns_v1.changes.Get.Expect(
        self.messages.DnsChangesGetRequest(
            changeId=test_change.id,
            managedZone=test_zone.name,
            project=self.Project()),
        test_change)

    result = self.Run('dns record-sets changes describe -z {0} {1}'.format(
        test_zone.name, test_change.id))
    self.assertEqual(test_change, result)

    expected_output = StringIO.StringIO()
    resource_printer.Print(
        test_change, 'yaml', out=expected_output, single=True)
    self.AssertOutputContains(expected_output.getvalue())
    expected_output.close()

if __name__ == '__main__':
  test_case.main()
