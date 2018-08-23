# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for googlecloudsdk.api_lib.logging.common library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import common
from tests.lib import test_case
from tests.lib.surface.logging import base


class ApiLibCommonTest(base.LoggingTestBase):

  def _setExpect(self, filter_spec, order_by='timestamp desc', page_size=1000):
    self.mock_client_v2.entries.List.Expect(
        self.msgs.ListLogEntriesRequest(resourceNames=['projects/my-project'],
                                        filter=filter_spec,
                                        orderBy=order_by,
                                        pageSize=page_size),
        self.msgs.ListLogEntriesResponse(entries=[]))

  def testBasicCalls(self):
    # FetchLogs() returns a generator so we use list() to force its execution.
    self._setExpect(filter_spec=None)
    list(common.FetchLogs())

    self._setExpect(filter_spec='myField=hello')
    list(common.FetchLogs(log_filter='myField=hello'))

  def testOrdering(self):
    self._setExpect(filter_spec=None)
    list(common.FetchLogs(order_by='desc'))

    self._setExpect(filter_spec=None, order_by='timestamp asc')
    list(common.FetchLogs(order_by='asc'))

  def testTestLimit(self):
    self._setExpect(filter_spec=None, page_size=5)
    list(common.FetchLogs(limit=5))

    self._setExpect(filter_spec=None, page_size=1000)
    list(common.FetchLogs(limit=1005))


if __name__ == '__main__':
  test_case.main()
