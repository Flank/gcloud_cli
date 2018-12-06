# -*- coding: utf-8 -*- #
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
"""Test of the 'operations cancel' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.datastore import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.GA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.ALPHA)
class CancelTest(base.DatastoreCommandUnitTest):
  """Tests the datastore operations cancel command."""

  def testCancelRelativeResourcePath(self, track):
    self.track = track
    operation_name_relative = 'doomed'
    operation_name_full = 'projects/my-test-project/operations/doomed'

    request = self._GetMockCancelRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_datastore_v1.projects_operations.Cancel.Expect(
        request, response=response)

    self.RunDatastoreTest(
        'operations cancel {}'.format(operation_name_relative))

  def testCancelAbsoluteResourcePath(self, track):
    self.track = track
    operation_name_full = 'projects/my-test-project/operations/doomed'

    request = self._GetMockCancelRequest(operation_name_full)
    response = operations.GetMessages().Empty()

    self.mock_datastore_v1.projects_operations.Cancel.Expect(
        request, response=response)

    self.RunDatastoreTest('operations cancel {}'.format(operation_name_full))

  def _GetMockCancelRequest(self, name):
    messages = operations.GetMessages()
    request = messages.DatastoreProjectsOperationsCancelRequest()
    request.name = name
    return request


if __name__ == '__main__':
  test_case.main()
