# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for endpoints operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from apitools.base.py import extra_types
from dateutil import tz

from tests.lib import test_case
from tests.lib.surface.endpoints import unit_test_base


class EndpointsOperationsListTest(unit_test_base.EV1UnitTestBase):
  """Unit tests for endpoints operations list command."""

  def SetUp(self):
    self.StartPatch('googlecloudsdk.core.util.times.LOCAL', tz.tzutc())

  def _MakeStartTimeMetadata(self, timestamp):
    return self.services_messages.Operation.MetadataValue(
        additionalProperties=[
            self.services_messages.Operation.MetadataValue.AdditionalProperty(
                key='startTime',
                value=extra_types.JsonValue(string_value=timestamp),
            )
        ]
    )

  def _MakeOperationList(self):
    ops = [
        self.services_messages.Operation(
            name='operation-12345', done=False,
            metadata=self._MakeStartTimeMetadata('2017-01-01T12:23:43Z')),
        self.services_messages.Operation(
            name='operation-67890', done=True,
            metadata=self._MakeStartTimeMetadata('2017-02-02T12:23:43Z')),
        self.services_messages.Operation(
            name='operation-abcde', done=True,
            metadata=self._MakeStartTimeMetadata('2017-03-03T12:23:43Z')),
    ]
    return ops

  def _ListOperations(self, filter_=None, ops=None, format_enabled=False):
    if filter_ is not None:
      self.assertIsNotNone(ops)
    if ops is None:
      ops = self._MakeOperationList()
    msg_filter = 'serviceName="{0}"'.format(self.DEFAULT_SERVICE_NAME)
    if filter_:
      msg_filter += ' AND ({0})'.format(filter_)

    list_request = (self.services_messages.
                    ServicemanagementOperationsListRequest)

    self.mocked_client.operations.List.Expect(
        request=list_request(filter=msg_filter),
        response=(self.services_messages.
                  ListOperationsResponse(operations=ops))
    )

    cmdline = ('endpoints operations list '
               '--service {0}'.format(self.DEFAULT_SERVICE_NAME))
    if filter_:
      cmdline += ' --filter "{0}"'.format(filter_)

    if not format_enabled:
      cmdline += ' --format=disable'
    return self.Run(cmdline)

  def testServicesOperationsList(self):
    response = list(self._ListOperations())
    self.assertEqual(response, self._MakeOperationList())

  def testServicesOperationsListFiltered(self):
    ops = [op for op in self._MakeOperationList() if op.done]
    response = list(self._ListOperations(filter_='done=True', ops=ops))
    self.assertEqual(response, ops)

  def testServicesOperationsListCheckOutput(self):
    self._ListOperations(format_enabled=True)

    # Verify the output
    expected_output = ('NAME             DONE   START_TIME\n'
                       'operation-12345  False  2017-01-01T12:23:43\n'
                       'operation-67890  True   2017-02-02T12:23:43\n'
                       'operation-abcde  True   2017-03-03T12:23:43\n')
    self.AssertOutputEquals(expected_output)

if __name__ == '__main__':
  test_case.main()
