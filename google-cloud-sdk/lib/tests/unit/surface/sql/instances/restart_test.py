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
"""Tests that exercise operations listing and executing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesRestartTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectRestart(self):
    self.mocked_client.instances.Restart.Expect(
        self.messages.SqlInstancesRestartRequest(
            instance='reset-test',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='reset-test',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/reset-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='3c4bb339-858a-4225-aa21-43caa613cc62',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/3c4bb339-858a-4225-aa21-43caa613cc62'.
            format(self.Project()),
            operationType='RESTART',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='3c4bb339-858a-4225-aa21-43caa613cc62',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='reset-test',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/reset-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='3c4bb339-858a-4225-aa21-43caa613cc62',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/3c4bb339-858a-4225-aa21-43caa613cc62'.
            format(self.Project()),
            operationType='RESTART',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

  def testRestart(self):
    self._ExpectRestart()
    self.WriteInput('y')

    self.Run('sql instances restart reset-test')
    self.AssertErrContains(
        'Restarted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/reset-test].'.format(self.Project()))

  def testRestartAsync(self):
    self._ExpectRestart()
    self.WriteInput('y')

    self.Run('sql instances restart reset-test --async')
    self.AssertErrNotContains(
        'Restarted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/reset-test].'.format(self.Project()))

  def testRestartNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql instances restart reset-test')


class InstancesRestartGATest(_BaseInstancesRestartTest, base.SqlMockTestGA):
  pass


class InstancesRestartBetaTest(_BaseInstancesRestartTest, base.SqlMockTestBeta):
  pass


class InstancesRestartAlphaTest(_BaseInstancesRestartTest,
                                base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
