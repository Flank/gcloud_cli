# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests that exercise operations on remote completion."""

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util


class RemoteCompletionTest(base.DnsMockTest, cli_test_base.CliTestBase):

  def SetUp(self):
    self.mocked_dns_v1.managedZones.List.Expect(
        self.messages.DnsManagedZonesListRequest(
            project=self.Project(),
            maxResults=100),
        self.messages.ManagedZonesListResponse(
            managedZones=util.GetManagedZones()[:1]))

  def testDescribeCompletion(self):
    self.RunCompletion('dns managed-zones describe m',
                       ['mz'])

  def testDeleteCompletion(self):
    self.RunCompletion('dns managed-zones delete m',
                       ['mz'])

  def testRecordSetsCompletion(self):
    self.RunCompletion('dns record-sets list --zone m',
                       ['mz'])

  def testRecordSetsExportCompletion(self):
    self.RunCompletion('dns record-sets export --zone m',
                       ['mz'])

if __name__ == '__main__':
  test_case.main()
