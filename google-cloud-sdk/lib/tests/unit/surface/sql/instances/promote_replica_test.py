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
"""Tests that exercise operations listing and executing."""

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class InstancesPromoteReplicaTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectPromoteReplica(self):
    self.mocked_client.instances.PromoteReplica.Expect(
        self.messages.SqlInstancesPromoteReplicaRequest(
            instance='replica-1',
            project=self.Project(),),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                26,
                785000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'replica-1',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/patch-instance3'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'56dec13c-fe47-449d-9942-921ad3bb8092',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56dec13c-fe47-449d-9942-921ad3bb8092'.
            format(self.Project()),
            operationType=u'PROMOTE_REPLICA',
            status=u'PENDING',
            user=u'170350250316@developer.gserviceaccount.com',))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation=u'56dec13c-fe47-449d-9942-921ad3bb8092',
            project=self.Project(),),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                26,
                785000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                27,
                48000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                26,
                22,
                6,
                27,
                48000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'replica-1',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/patch-instance3'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'56dec13c-fe47-449d-9942-921ad3bb8092',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56dec13c-fe47-449d-9942-921ad3bb8092'.
            format(self.Project()),
            operationType=u'PROMOTE_REPLICA',
            status=u'DONE',
            user=u'170350250316@developer.gserviceaccount.com',))

  def testSimplePromote(self):
    self._ExpectPromoteReplica()
    self.WriteInput('y')

    self.Run('sql instances promote-replica replica-1')
    self.AssertErrContains(
        'Promoted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/replica-1].'.format(self.Project()))

  def testPromoteAsync(self):
    self._ExpectPromoteReplica()
    self.WriteInput('y')

    self.Run('sql instances promote-replica replica-1 --async')
    self.AssertErrNotContains(
        'Promoted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/replica-1].'.format(self.Project()))

  def testPromoteNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances promote-replica replica-1')


if __name__ == '__main__':
  test_case.main()
