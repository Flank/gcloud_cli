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

"""Tests for rolling-updates describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties

from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import rolling_updates_base as base

messages = core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


class UpdatesDescribeTest(base.UpdaterMockTest):

  def testDescribe(self):
    self.mocked_client_v1beta1.rollingUpdates.Get.Expect(
        messages.ReplicapoolupdaterRollingUpdatesGetRequest(
            project=self.Project(), zone=base.ZONE,
            rollingUpdate='some-update'),
        messages.RollingUpdate(
            kind='replicapoolupdater#rollingUpdate',
            selfLink='http://apis/updates/some-update',
            instanceGroupManager='http://apis/instanceGroupManagers/some-group',
            instanceTemplate='http://apis/instanceTemplates/some-template',
            policy=messages.RollingUpdate.PolicyValue(
                maxNumConcurrentInstances=3,
                autoPauseAfterInstances=5,
                maxNumFailedInstances=1,
                minInstanceUpdateTimeSec=60,
                instanceStartupTimeoutSec=120),
            id='some-update',
            status='ROLLING_FORWARD',
            statusMessage='some details'
        )
    )

    self.Run('alpha compute rolling-updates '
             '--zone=some-zone describe some-update')
    self.AssertOutputContains("""\
id: some-update
instanceGroupManager: http://apis/instanceGroupManagers/some-group
instanceTemplate: http://apis/instanceTemplates/some-template
kind: replicapoolupdater#rollingUpdate
policy:
  autoPauseAfterInstances: 5
  instanceStartupTimeoutSec: 120
  maxNumConcurrentInstances: 3
  maxNumFailedInstances: 1
  minInstanceUpdateTimeSec: 60
selfLink: http://apis/updates/some-update
status: ROLLING_FORWARD
statusMessage: some details
""")

  def testDescribe404(self):
    self.mocked_client_v1beta1.rollingUpdates.Get.Expect(
        messages.ReplicapoolupdaterRollingUpdatesGetRequest(
            project=self.Project(), zone=base.ZONE,
            rollingUpdate='some-update'),
        exception=http_error.MakeHttpError(404),
    )

    with self.AssertRaisesHttpExceptionMatches('Resource not found.'):
      self.Run('alpha compute rolling-updates '
               '--zone=some-zone describe some-update')

  def testDescribeFailureMissingArgumentZone(self):
    try:
      self.Run('alpha compute rolling-updates describe some-update')
      self.fail('Expected exception has not been raised')
    except properties.RequiredPropertyError:
      self.AssertErrContains('required property [zone] is not currently set')

if __name__ == '__main__':
  test_case.main()
