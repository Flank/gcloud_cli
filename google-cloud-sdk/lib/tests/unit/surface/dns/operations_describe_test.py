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
"""Tests that exercise the 'gcloud dns operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dns import base


@parameterized.named_parameters(
    ('Beta', calliope_base.ReleaseTrack.BETA, 'v1beta2'),
    ('GA', calliope_base.ReleaseTrack.GA, 'v1'),
)
class OperationsDescribeTest(base.DnsMockMultiTrackTest):

  def getTestOperation(self):
    return self.messages.Operation(
        id='123',
        startTime='2015-10-22T18:46:48.654Z',
        status=self.messages.Operation.StatusValueValuesEnum('done'),
        type='delete',
        user='user@example.net',)

  def testDescribeByZone(self, track, api_version):
    self.SetUpForTrack(track, api_version)
    test_operation = self.getTestOperation()
    self.client.managedZoneOperations.Get.Expect(
        self.messages.DnsManagedZoneOperationsGetRequest(
            managedZone='my-zone',
            project=self.Project(),
            operation=test_operation.id),
        test_operation)

    self.Run('dns operations describe {0} --zone my-zone'.format(
        test_operation.id))

    expected_output = """\
id: '123'
startTime: '2015-10-22T18:46:48.654Z'
status: done
type: delete
user: user@example.net
"""
    self.AssertOutputContains(expected_output)


if __name__ == '__main__':
  test_case.main()
