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

"""Tests for rolling-updates start command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.surface.compute import rolling_updates_base as base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


class StartTest(base.UpdaterMockTest):

  def testStart_Ok_Recreate(self):
    self.mocked_client_v1beta1.rollingUpdates.Insert.Expect(
        messages.ReplicapoolupdaterRollingUpdatesInsertRequest(
            project=self.Project(),
            zone=base.ZONE,
            rollingUpdate=messages.RollingUpdate(
                instanceGroupManager=(
                    'https://www.googleapis.com/compute/v1/'
                    'projects/{0}/zones/some-zone/instanceGroupManagers'
                    '/some-group').format(self.Project()),
                actionType='RECREATE',
                instanceTemplate=(
                    'https://www.googleapis.com/compute/v1/'
                    'projects/{0}/global/instanceTemplates'
                    '/some-template').format(self.Project()),
                policy=messages.RollingUpdate.PolicyValue(
                    autoPauseAfterInstances=1,
                    maxNumConcurrentInstances=7,
                    minInstanceUpdateTimeSec=8,
                    instanceStartupTimeoutSec=15,
                    maxNumFailedInstances=23))),
        messages.Operation(
            name='some-operation',
            targetLink=(
                'https://www.googleapis.com/replicapoolupdater/v1beta1/'
                'projects/{0}/zones/some-zone/rollingUpdates'
                '/some-update').format(self.Project()))
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

    self.Run('alpha compute rolling-updates --zone=some-zone start '
             '--group=some-group '
             '--template=some-template '
             '--auto-pause-after-instances=1 '
             '--max-num-concurrent-instances=7 '
             '--min-instance-update-time=8 '
             '--instance-startup-timeout=15 '
             '--max-num-failed-instances=23')
    self.AssertErrContains(
        'Started [https://www.googleapis.com/replicapoolupdater/v1beta1'
        '/projects/{0}/zones/some-zone/rollingUpdates/some-update].'.format(
            self.Project()))

  def testStart_Failure_Errors(self):
    self.mocked_client_v1beta1.rollingUpdates.Insert.Expect(
        messages.ReplicapoolupdaterRollingUpdatesInsertRequest(
            project=self.Project(),
            zone=base.ZONE,
            rollingUpdate=messages.RollingUpdate(
                instanceGroupManager=(
                    'https://www.googleapis.com/compute/v1/'
                    'projects/{0}/zones/some-zone/instanceGroupManagers'
                    '/some-group').format(self.Project()),
                actionType='RECREATE',
                instanceTemplate=(
                    'https://www.googleapis.com/compute/v1/'
                    'projects/{0}/global/instanceTemplates'
                    '/some-template').format(self.Project()),
                policy=messages.RollingUpdate.PolicyValue(
                    autoPauseAfterInstances=1,
                    maxNumConcurrentInstances=7,
                    instanceStartupTimeoutSec=3600))),
        messages.Operation(
            name='some-operation',
            targetLink=(
                'https://www.googleapis.com/replicapoolupdater/v1beta1/'
                'projects/{0}/zones/some-zone/rollingUpdates'
                '/some-update').format(self.Project()))
    )
    self.mocked_client_v1beta1.zoneOperations.Get.Expect(
        messages.ReplicapoolupdaterZoneOperationsGetRequest(
            project=self.Project(), zone=base.ZONE, operation='some-operation'),
        base.OPERATION_DONE_WITH_ERRORS
    )

    with self.AssertRaisesToolExceptionRegexp(
        r'could not start \[https://www.googleapis.com/replicapoolupdater/'
        r'v1beta1/projects/{0}/zones/some-zone/'
        r'rollingUpdates/some-update\]'.format(self.Project())):
      self.Run('alpha compute rolling-updates --zone=some-zone start '
               '--group=some-group '
               '--template=some-template '
               '--auto-pause-after-instances=1 '
               '--max-num-concurrent-instances=7 '
               '--instance-startup-timeout=1h')

  def testStart_Failure_MissingArgument_Group(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --group: Must be specified.'):
      self.Run('alpha compute rolling-updates --zone=some-zone start '
               '--template=some-template')

  def testStart_Failure_MissingArgument_Template(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template: Must be specified.'):
      self.Run('alpha compute rolling-updates --zone=some-zone start '
               '--group=some-group')

  def testStart_Failure_MissingArgument_Zone(self):
    try:
      self.Run('alpha compute rolling-updates start '
               '--group=some-group --template=some-template')
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')

  def testStart_Failure_IncorrectActionType(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --action: Invalid choice: \'WRONG_ACTION\''):
      self.Run('alpha compute rolling-updates --zone=some-zone start '
               '--template=some-template --group=some-group '
               '--action=WRONG_ACTION')
      self.fail('Expected exception has not been raised')


if __name__ == '__main__':
  test_case.main()
