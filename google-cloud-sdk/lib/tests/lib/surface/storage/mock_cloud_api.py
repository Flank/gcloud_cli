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

import collections
import functools

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.core import exceptions as core_errors

import mock


ExpectedCall = collections.namedtuple('ExpectedCall',
                                      ['args', 'response', 'error'])


class MockCloudApiFunction(object):
  """Mocks a specific method of CloudApi for MockCloudApi.

  Attributes:
    expected (list): Stack of expected client function calls.
    name (str): Name of function being mocked.
  """

  def __init__(self, name):
    self.expected = []
    self.name = name

  def expect(self, args=None, kwargs=None, response=None, error=None):
    """Set mock to expect a call with certain arguments.

    Args:
      args (list): List of arguments to expect. For example, the values for 'x'
          and 'y' in 'def f(x, y, z=4)'.
      kwargs (dict): Named arguments to expect. For example, '{z: 0}' for
          'def f(x, y, z=4)'.
      response (any): Should be set to the return type of the actual function
          For example, GetBucket should return a BucketResource.
      error (Exception): Should be set to the errors the actual function can
          raise. For example, GetBucket might raise a ValueError. Raising this
          error takes precedence over returning a provided response.
    """
    self.expected.append(ExpectedCall(self._merge_args(args, kwargs),
                                      response=response, error=error))

  def close(self):
    """Make sure all expected calls were made."""
    if self.expected:
      raise core_errors.Error('Did not receive expected calls to {}: {}'.format(
          self.name, self._convert_collection_to_string(self.expected)))

  def __call__(self, *args, **kwargs):
    """Make sure call to mocked method was expected and has correct values."""
    if not self.expected:
      raise core_errors.Error('Received unexpected call to {}'.format(
          self.name))

    merged_args = self._merge_args(args, kwargs)
    expected = self.expected.pop(0)
    if expected[0] != merged_args:
      raise core_errors.Error(
          'Method {} expected args:\n{}\n...and received args: {}'.format(
              self.name,
              self._convert_collection_to_string(expected[0]),
              self._convert_collection_to_string(merged_args)))

    if expected.error:
      raise expected.error
    return expected.response

  def _merge_args(self, args, kwargs):
    """Merge args and kwargs into one args list.

    Note: Default arguments are not included in kwargs.

    Args:
      args (list): List of arguments to expect. For example, the values for 'x'
          and 'y' in 'def f(x, y, z=4)'.
      kwargs (dict): Named arguments to expect. For example, '{z: 0}' for
          'def f(x, y, z=4)'.

    Returns:
      List of all possible function arguments with None for values not received.

    Raises:
      Error: Received named arguments the mocked method does not accept.
    """
    # Get tuple of function argument names.
    # For example: "def f(self, x, y)" becomes "('self', 'x', 'y')"".
    allowed_args = getattr(cloud_api.CloudApi, self.name).__code__.co_varnames
    # Convert tuple to list and remove 'self' argument.
    allowed_args = list(allowed_args)[1:]
    if args and len(args) > len(allowed_args):
      raise core_errors.Error('Method {} received {} args but only accepts {}'
                              ' args.'.format(self.name, len(args),
                                              len(allowed_args)))

    result = [None]*len(allowed_args)
    i = 0
    # Add values for all unamed arguments to result.
    if args:
      while i < len(args):
        result[i] = args[i]
        i += 1
    # Add values for all allowed named args to result.
    while i < len(result):
      if kwargs and allowed_args[i] in kwargs:
        result[i] = kwargs.pop(allowed_args[i])
      i += 1

    if kwargs:
      if any([kwarg in allowed_args for kwarg in kwargs]):
        raise core_errors.Error('Method {} received a kwargs dict that attempts'
                                ' to set the same values as the args list it'
                                ' received.'.format(self.name))
      raise core_errors.Error(
          'Method {} allows args:\n{}\n...and received args: {}'.format(
              self.name,
              self._convert_collection_to_string(allowed_args),
              self._convert_collection_to_string(kwargs)))

    return result

  def _convert_collection_to_string(self, collection):
    """Convert collections of various object types to printable string lists.

    Args:
      collection (dict|list): Collection of items that needs to be printable.

    Returns:
      A printable list of strings.
    """
    if isinstance(collection, list):
      return '\n'.join([str(x) for x in collection])
    if isinstance(collection, dict):
      string_list = ['{}={}'.format(str(k), str(v))
                     for k, v in collection.items()]
      return '\n'.join(string_list)


class MockCloudApi(object):
  """Client that mocks cloud_api.CloudApi with some additional features.

  Tasks and other Storage code should work any cloud provider. It doesn't make
  sense to use provider-specific API mocking like Apitools for GCS. Therefore,
  we have this generic mock cloud API client that follows the cloud_api.CloudAPI
  interface.

  TODO(b/163816044): Write decorator that patches, removes need for 'with', and
  closes the mock_api_client.

  Usage:
    def my_unit_test(self):
      mock_api_client = mock_cloud_api.MockCloudApi()
      bucket_reference = ...
      mock_cloud_api.GetBucket.expect(args=['bucket_name'], kwargs=None,
                                      response=bucket_reference, error=None)

      with mock.patch.object(api_factory, 'get_api') as mock_get_api:
        mock_get_api.return_value = mock_api_client
        test_func_that_uses_get_bucket()
        mock_api_client.close()
  """

  def __init__(self):
    self._mocked_methods = []
    for method_name in dir(cloud_api.CloudApi):
      if method_name[0] != '_':
        setattr(self, method_name, MockCloudApiFunction(method_name))
        self._mocked_methods.append(method_name)
    super().__init__()

  def close(self):
    """Make sure all mocked methods aren't expecting more calls."""
    for method_name in self._mocked_methods:
      getattr(self, method_name).close()


def patch_cloud_api(unit_test_function):
  """Patches MockCloudApi over CloudApi for a unit test and handles cleanup.

  Args:
    unit_test_function (function): Unit test to decorate.

  Returns:
    Decorator function.
  """
  # "wraps" makes the decorator reflect some metadata of the wrapped function.
  # Allows compatibility with parameterized decorator.
  @functools.wraps(unit_test_function)
  def wrapper(*args, **kwargs):
    mock_cloud_api_client = MockCloudApi()
    # Add mocked CloudApi to unit test arguments like the patch decorator.
    args += tuple([mock_cloud_api_client])
    # Have api_factory return the mocked client instead of a specific
    # cloud provider client.
    with mock.patch.object(api_factory, 'get_api',
                           new=lambda _: mock_cloud_api_client):
      unit_test_function(*args, **kwargs)

    mock_cloud_api_client.close()
  return wrapper
