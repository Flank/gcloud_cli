# -*- coding: utf-8 -*- #
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

"""Tests for rolling-updates list-instance-updates command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.compute import rolling_updates_base as base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


class UpdatesListInstanceUpdatesTest(base.UpdaterMockTest):

  def testListInstanceUpdates(self):
    self.mocked_client_v1beta1.rollingUpdates.ListInstanceUpdates.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListInstanceUpdatesRequest(
            project=self.Project(),
            zone=base.ZONE,
            rollingUpdate='some-update',
            maxResults=100,
        ),
        messages.InstanceUpdateList(
            items=[
                messages.InstanceUpdate(
                    instance='http://instances/some-instance-1',
                    status='ROLLED_OUT',
                ),
                messages.InstanceUpdate(
                    instance='http://instances/some-instance-2',
                    status='ROLLING_OUT',
                ),
            ],
            nextPageToken='1396059067464',
        ),
    )
    self.mocked_client_v1beta1.rollingUpdates.ListInstanceUpdates.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListInstanceUpdatesRequest(
            project=self.Project(),
            zone=base.ZONE,
            rollingUpdate='some-update',
            pageToken='1396059067464',
            maxResults=100,
        ),
        messages.InstanceUpdateList(
            items=[
                messages.InstanceUpdate(
                    instance='http://instances/some-instance-3',
                    status='ROLLING_OUT',
                ),
                messages.InstanceUpdate(
                    instance='http://instances/some-instance-4',
                    status='ROLLED_OUT',
                ),
            ],
            nextPageToken=None,
        ),
    )

    self.Run(('alpha compute rolling-updates '
              '--zone=some-zone list-instance-updates some-update'))
    self.AssertOutputContains("""\
INSTANCE_NAME    STATUS
some-instance-1  ROLLED_OUT
some-instance-2  ROLLING_OUT
some-instance-3  ROLLING_OUT
some-instance-4  ROLLED_OUT
""")

  def testListInstanceUpdates_Failure_MissingArgument_Zone(self):
    try:
      self.Run(
          'alpha compute rolling-updates list-instance-updates some-update')
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')


if __name__ == '__main__':
  test_case.main()
