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

"""Tests that exercise the 'gcloud dns record-sets changes list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.dns import base
from tests.lib.surface.dns import util


class ChangesListTest(base.DnsMockTest):

  def testZeroChangesList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.changes.List.Expect(
        self.messages.DnsChangesListRequest(
            managedZone=test_zone.name,
            project=self.Project(),
            maxResults=100),
        self.messages.ChangesListResponse(changes=[]))

    self.Run('dns record-sets changes list -z {0}'.format(test_zone.name))
    self.AssertErrContains('Listed 0 items.')

  def testOneChangeList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.changes.List.Expect(
        self.messages.DnsChangesListRequest(
            managedZone=test_zone.name,
            project=self.Project(),
            maxResults=100),
        self.messages.ChangesListResponse(changes=util.GetChanges()[:1]))

    self.Run('dns record-sets changes list -z {0}'.format(test_zone.name))
    self.AssertOutputContains("""\
ID  START_TIME                STATUS
2   2014-10-21T15:16:29.252Z  pending
""", normalize_space=True)

  def testMultipleChangesList(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.changes.List.Expect(
        self.messages.DnsChangesListRequest(
            managedZone=test_zone.name,
            project=self.Project(),
            maxResults=100),
        self.messages.ChangesListResponse(changes=util.GetChanges()))

    self.Run('dns record-sets changes list -z {0}'.format(test_zone.name))
    self.AssertOutputContains("""\
ID  START_TIME                STATUS
2   2014-10-21T15:16:29.252Z  pending
1   2014-10-20T21:34:21.073Z  done
0   2014-10-20T20:06:50.078Z  done
""", normalize_space=True)

  def testChangesListSortOrder(self):
    test_zone = util.GetManagedZones()[0]
    sort_order = 'ascending'
    reversed_changes = [change for change in reversed(util.GetChanges())]
    self.mocked_dns_v1.changes.List.Expect(
        self.messages.DnsChangesListRequest(
            managedZone=test_zone.name,
            project=self.Project(),
            sortOrder=sort_order,
            maxResults=100),
        self.messages.ChangesListResponse(changes=reversed_changes))

    self.Run('dns record-sets changes list -z {0} --sort-order={1}'.format(
        test_zone.name, sort_order))
    self.AssertOutputContains("""\
ID  START_TIME                STATUS
0   2014-10-20T20:06:50.078Z  done
1   2014-10-20T21:34:21.073Z  done
2   2014-10-21T15:16:29.252Z  pending
""", normalize_space=True)

  def testChangesListWithLimit(self):
    test_zone = util.GetManagedZones()[0]
    self.mocked_dns_v1.changes.List.Expect(
        self.messages.DnsChangesListRequest(
            managedZone=test_zone.name,
            project=self.Project(),
            maxResults=2),
        self.messages.ChangesListResponse(changes=util.GetChanges()))

    self.Run('dns record-sets changes list -z {0} --limit=2'.format(
        test_zone.name))
    self.AssertOutputContains("""\
ID  START_TIME                STATUS
2   2014-10-21T15:16:29.252Z  pending
1   2014-10-20T21:34:21.073Z  done
""", normalize_space=True)

if __name__ == '__main__':
  test_case.main()
