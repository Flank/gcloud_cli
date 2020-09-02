# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""For mocking calls to a provider-neutral cloud API client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api

import mock


def patch(unit_test_function):
  """Patches CloudApi for a unit test.

  Example:

  @mock_cloud_api.patch
  def my_api_test(self, mock_client):
    # Set return values for successive calls to API client function.
    mock_client.GetBucket.side_effect = ['bucket1_data,', 'bucket2_data', ...]

    # Test logic.
    ...

    # Make sure successive calls to API client function had correct arguments.
    # The mock.call objects can be used to represent args and kwargs together.
    mock_client.GetBucket.assert_has_calls([mock.call('bucket1', extra=True),
                                            mock.call('bucket2'), ...])

  Args:
    unit_test_function (function): Unit test to decorate.

  Returns:
    Decorator function.
  """
  # "wraps" makes the decorator reflect some metadata of the wrapped function.
  # Allows compatibility with parameterized decorator.
  @functools.wraps(unit_test_function)
  def wrapper(*args, **kwargs):
    mock_cloud_api_client = mock.create_autospec(cloud_api.CloudApi)
    # Add mocked CloudApi to unit test arguments like the patch decorator.
    args += (mock_cloud_api_client,)
    # Have api_factory return the mocked client instead of a specific
    # cloud provider client.
    with mock.patch.object(api_factory, 'get_api',
                           new=lambda _: mock_cloud_api_client):
      unit_test_function(*args, **kwargs)

  return wrapper
