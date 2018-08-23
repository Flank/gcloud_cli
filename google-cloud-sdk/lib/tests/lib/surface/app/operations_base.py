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

"""Tests for gcloud app services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types

from tests.lib.surface.app import api_test_util


class OperationsTestBase(api_test_util.ApiTestBase):
  """Provides helper test methods specific to operations."""

  def SetUp(self):
    self.default_start_time = extra_types.JsonValue(
        string_value='2016-12-08T23:59:10.646Z')

  def MakeOperation(self, app, op_id, done, error=None,
                    props=None, no_metadata=False):
    """Creates a messages.Operations object to be used in mocks.

    Args:
      app: String representing project id.
      op_id: String representing operation id.
      done: Boolean representing if operation is finished.
      error: Error result in case of failure or cancellation.
      props: Dictionary of metadata.
      no_metadata: Do not set the metadata message at all.

    Returns:
      A messages.Operation response object.
    """
    props = props or dict()
    if 'insertTime' not in props:
      props['insertTime'] = self.default_start_time

    additional_props = []
    # Sorted for consistent testing.
    for key in sorted(props):
      additional_props.append(
          self.messages.Operation.MetadataValue.AdditionalProperty(
              key=key, value=props[key]))
    metadata = self.messages.Operation.MetadataValue(
        additionalProperties=additional_props)
    op_response = self.messages.Operation(
        name='apps/{0}/operations/{1}'.format(app, op_id),
        done=done,
        error=error,
        metadata=None if no_metadata else metadata)
    return op_response

  def MakeListOperationsResponse(self, operations):
    """Creates a messages.ListOperationsResponse object to be used in mocks.

    Args:
      operations: A list of messages.Operation objects.
    Returns:
      A messages.ListOperationsResponse object.
    """
    return self.messages.ListOperationsResponse(operations=operations)

  def ExpectGetOperationsRequest(self, app, op_id, response):
    """Adds expected get-operation call and response to mock client.

    Args:
      app: String representing project id.
      op_id: String representing operation id.
      response: Expected messages.Operation response object.
    """
    request = self.messages.AppengineAppsOperationsGetRequest(
        name='apps/{0}/operations/{1}'.format(app, op_id))
    self.mock_client.apps_operations.Get.Expect(request, response=response)

  def ExpectListOperationsRequest(self, app, response, filter_=None):
    """Adds expected list call and response to mock client.

    Args:
      app: String representing project id.
      response: Expected messages.ListOperationsResponse object.
      filter_: Expected filter string.
    """
    request = self.messages.AppengineAppsOperationsListRequest(
        name='apps/{0}'.format(app),
        filter=filter_, pageSize=100)
    self.mock_client.apps_operations.List.Expect(request, response=response)
