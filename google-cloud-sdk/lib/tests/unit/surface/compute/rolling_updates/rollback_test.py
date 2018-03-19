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

"""Tests for rolling-updates rollback command."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import rolling_updates_base as base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


class UpdatesRollbackTest(base.UpdaterMockTest):

  def testRollback_Ok(self):
    self.mocked_client_v1beta1.rollingUpdates.Rollback.Expect(
        messages.ReplicapoolupdaterRollingUpdatesRollbackRequest(
            project=self.Project(), zone=base.ZONE,
            rollingUpdate='some-update'),
        messages.Operation(
            name='some-operation',
            targetLink=(
                'https://www.googleapis.com/replicapoolupdater/v1beta1/'
                'projects/{0}/zones/some-zone'
                '/rollingUpdates/some-update').format(self.Project()))
    )
    self.mocked_client_v1beta1.zoneOperations.Get.Expect(
        messages.ReplicapoolupdaterZoneOperationsGetRequest(
            project=self.Project(), zone=base.ZONE, operation='some-operation'),
        messages.Operation(status='RUNNING')
    )
    self.mocked_client_v1beta1.zoneOperations.Get.Expect(
        messages.ReplicapoolupdaterZoneOperationsGetRequest(
            project=self.Project(), zone=base.ZONE, operation='some-operation'),
        messages.Operation(status='DONE')
    )

    self.Run('alpha compute rolling-updates '
             '--zone=some-zone rollback some-update')
    self.AssertErrContains(
        'Initiated rollback of [https://www.googleapis.com/replicapoolupdater'
        '/v1beta1/projects/{0}/zones/some-zone'
        '/rollingUpdates/some-update].'.format(self.Project()))

  def testRollback_Failure_Errors(self):
    self.mocked_client_v1beta1.rollingUpdates.Rollback.Expect(
        messages.ReplicapoolupdaterRollingUpdatesRollbackRequest(
            project=self.Project(), zone=base.ZONE,
            rollingUpdate='some-update'),
        messages.Operation(
            name='some-operation',
            targetLink=(
                'https://www.googleapis.com/replicapoolupdater/v1beta1/'
                'projects/{0}/zones/some-zone'
                '/rollingUpdates/some-update').format(self.Project()))
    )
    self.mocked_client_v1beta1.zoneOperations.Get.Expect(
        messages.ReplicapoolupdaterZoneOperationsGetRequest(
            project=self.Project(), zone=base.ZONE, operation='some-operation'),
        base.OPERATION_DONE_WITH_ERRORS
    )

    with self.AssertRaisesToolExceptionRegexp(
        r'could not initiate rollback of \[https://www.googleapis.com/'
        r'replicapoolupdater/v1beta1/projects/{0}/zones/'
        r'some-zone/rollingUpdates/some-update\]'.format(self.Project())):
      self.Run('alpha compute rolling-updates '
               '--zone=some-zone rollback some-update')

  def testRollback_Failure_MissingArgument_Zone(self):
    try:
      self.Run('alpha compute rolling-updates rollback some-update')
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')


if __name__ == '__main__':
  test_case.main()
