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

"""Tests for rolling-updates list command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.compute import rolling_updates_base as base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


UPDATE_1 = messages.RollingUpdate(
    instanceGroupManager='http://instanceGroups/some-group',
    instanceTemplate='http://instanceTemplates/some-template-1',
    id='some-update-1',
    status='ROLLED_OUT',
    statusMessage='some details 1'
)
UPDATE_2 = messages.RollingUpdate(
    instanceGroupManager='http://instanceGroups/other-group',
    instanceTemplate='http://instanceTemplates/some-template-2',
    policy=messages.RollingUpdate.PolicyValue(
        autoPauseAfterInstances=5,
        maxNumConcurrentInstances=3,
        instanceStartupTimeoutSec=60),
    id='some-update-2',
    status='ROLLED_BACK',
    statusMessage='some details 2'
)
UPDATE_3 = messages.RollingUpdate(
    instanceGroupManager='http://instanceGroups/some-group',
    instanceTemplate='http://instanceTemplates/some-template-3',
    id='some-update-3',
    status='CANCELLED',
    statusMessage='some details 3'
)
UPDATE_4 = messages.RollingUpdate(
    instanceGroupManager='http://instanceGroups/other-group',
    instanceTemplate='http://instanceTemplates/some-template-4',
    policy=messages.RollingUpdate.PolicyValue(
        autoPauseAfterInstances=1,
        maxNumConcurrentInstances=4,
        instanceStartupTimeoutSec=120),
    id='some-update-4',
    status='ROLLING_FORWARD',
    statusMessage='some details 4'
)
UPDATE_5 = messages.RollingUpdate(
    instanceGroup='http://instanceGroups/non-managed',
    id='some-update-5',
    status='ROLLED_OUT',
    statusMessage='some details 5'
)


class UpdatesListTest(base.UpdaterMockTest):

  def testList_Ok(self):
    self.mocked_client_v1beta1.rollingUpdates.List.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListRequest(
            project=self.Project(),
            zone=base.ZONE,
            maxResults=100,
        ),
        messages.RollingUpdateList(
            items=[UPDATE_1, UPDATE_2],
            nextPageToken='1396059067464',
        ),
    )
    self.mocked_client_v1beta1.rollingUpdates.List.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListRequest(
            project=self.Project(),
            zone=base.ZONE,
            pageToken='1396059067464',
            maxResults=100,
        ),
        messages.RollingUpdateList(
            items=[UPDATE_3, UPDATE_4, UPDATE_5],
            nextPageToken=None,
        ),
    )

    self.Run('alpha compute rolling-updates --zone=some-zone list')
    self.AssertOutputContains("""\
ID             GROUP_NAME   TEMPLATE_NAME    STATUS           STATUS_MESSAGE
some-update-1  some-group   some-template-1  ROLLED_OUT       some details 1
some-update-2  other-group  some-template-2  ROLLED_BACK      some details 2
some-update-3  some-group   some-template-3  CANCELLED        some details 3
some-update-4  other-group  some-template-4  ROLLING_FORWARD  some details 4
some-update-5  non-managed                   ROLLED_OUT       some details 5
""", normalize_space=True)

  def testList_Ok_FilterByGroup(self):
    self.mocked_client_v1beta1.rollingUpdates.List.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListRequest(
            project=self.Project(),
            zone=base.ZONE,
            filter='instanceGroup eq some-group',
            maxResults=100,
        ),
        messages.RollingUpdateList(
            items=[UPDATE_1, UPDATE_3],
            nextPageToken=None,
        ),
    )

    self.Run('alpha compute rolling-updates '
             '--zone=some-zone list --group=some-group')
    self.AssertOutputContains("""\
ID             GROUP_NAME  TEMPLATE_NAME    STATUS      STATUS_MESSAGE
some-update-1  some-group  some-template-1  ROLLED_OUT  some details 1
some-update-3  some-group  some-template-3  CANCELLED   some details 3
""", normalize_space=True)

  def testList_Ok_FilterByGroup_EmptyResult(self):
    self.mocked_client_v1beta1.rollingUpdates.List.Expect(
        messages.ReplicapoolupdaterRollingUpdatesListRequest(
            project=self.Project(),
            zone=base.ZONE,
            filter='instanceGroup eq non-existing-group',
            maxResults=100,
        ),
        messages.RollingUpdateList(
            items=[],
            nextPageToken=None,
        ),
    )

    self.Run('alpha compute rolling-updates '
             '--zone=some-zone list --group=non-existing-group')
    self.AssertErrContains('Listed 0 items.')

  def testList_Failure_MissingArgument_Zone(self):
    try:
      self.Run('alpha compute rolling-updates list')
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')


if __name__ == '__main__':
  test_case.main()

