# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesDeleteTest(object):
  # pylint:disable=g-tzinfo-datetime

  def testDeleteNoConfirm(self):
    self.WriteInput('n')
    self.Run('sql instances delete mock-instance')

  def _ExpectDelete(self):
    self.mocked_client.instances.Delete.Expect(
        self.messages.SqlInstancesDeleteRequest(
            instance='mock-instance',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=None,
            targetId='mock-instance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56282116-8e0d-43d4-85d1-692b1f0cf044',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56282116-8e0d-43d4-85d1-692b1f0cf044'.
            format(self.Project()),
            operationType='DELETE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='56282116-8e0d-43d4-85d1-692b1f0cf044',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                415000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                38,
                39,
                525000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                12,
                19,
                39,
                26,
                601000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='mock-instance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='56282116-8e0d-43d4-85d1-692b1f0cf044',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/56282116-8e0d-43d4-85d1-692b1f0cf044'.
            format(self.Project()),
            operationType='DELETE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

  def testDelete(self):
    self._ExpectDelete()
    self.WriteInput('y')

    self.Run('sql instances delete mock-instance')
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains(
        'Deleted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/mock-instance].'.format(self.Project()))

  def testDeleteAsync(self):
    self._ExpectDelete()
    self.WriteInput('y')

    self.Run('sql instances delete mock-instance --async')
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrNotContains(
        'Deleted [https://www.googleapis.com/sql/v1beta4/'
        'projects/{0}/instances/mock-instance].'.format(self.Project()))


class InstancesDeleteGATest(_BaseInstancesDeleteTest, base.SqlMockTestGA):
  pass


class InstancesDeleteBetaTest(_BaseInstancesDeleteTest, base.SqlMockTestBeta):
  pass


class InstancesDeleteAlphaTest(_BaseInstancesDeleteTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
