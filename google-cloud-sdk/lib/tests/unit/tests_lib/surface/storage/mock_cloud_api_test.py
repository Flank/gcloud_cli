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
"""Tests for tests.lib.surface.storage.mock_cloud_api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.core import exceptions as core_errors
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import mock_cloud_api

import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class MockCloudApiTest(sdk_test_base.SdkBase):
  """Tests logic of IntraCloudCopyTask."""

  def SetUp(self):
    self.client = mock_cloud_api.MockCloudApi()

  def test_mocks_all_cloud_api_functions(self):
    expected_mocked_methods = [name for name in dir(cloud_api.CloudApi)
                               if name[0] != '_']
    self.assertEqual(self.client._mocked_methods, expected_mocked_methods)

  def test_closing_client_closes_mocked_functions(self):
    for method in self.client._mocked_methods:
      setattr(self.client, method, mock.Mock(
          spec=mock_cloud_api.MockCloudApiFunction))

    self.client.close()

    for method in self.client._mocked_methods:
      getattr(self.client, method).close.assert_called_once()

  def test_closing_client_raises_error_when_expecting_call(self):
    self.client.GetBucket.expect()

    with self.assertRaises(core_errors.Error):
      self.client.close()

  def test_unexpected_call(self):
    with self.assertRaisesRegex(
        core_errors.Error, 'Received unexpected call to GetBucket'):
      self.client.GetBucket()

  def test_received_more_args_than_allowed(self):
    with self.assertRaisesRegex(core_errors.Error,
                                'Method GetBucket received 3 args but only'
                                ' accepts 2 args.'):
      self.client.GetBucket.expect(['potato', 'apricot', 'salad'])

  def test_missing_expected_args(self):
    self.client.GetBucket.expect(['potato'])

    with self.assertRaises(core_errors.Error):
      self.client.GetBucket()

  def test_received_unexpected_args(self):
    self.client.GetBucket.expect()

    with self.assertRaises(core_errors.Error):
      self.client.GetBucket('potato')

  def test_expect_disallowed_kwargs(self):
    with self.assertRaises(core_errors.Error):
      self.client.GetBucket.expect(kwargs={'pineapple': 'pizza'})

  def test_missing_expected_kwargs(self):
    self.client.GetBucket.expect(kwargs={'bucket_name': 'pizza'})

    with self.assertRaises(core_errors.Error):
      self.client.GetBucket()

  def test_received_unexpected_kwargs(self):
    self.client.GetBucket.expect()

    with self.assertRaises(core_errors.Error):
      self.client.GetBucket(bucket_name='pizza')

  def test_expected_args_and_kwargs(self):
    self.client.GetBucket.expect(['potato'], {'fields_scope': 'hyrule_field'})
    self.client.GetBucket('potato', fields_scope='hyrule_field')
    self.client.close()

  def test_conflicting_args_and_kwargs(self):
    with self.assertRaisesRegex(
        core_errors.Error,
        'Method GetBucket received a kwargs dict that attempts to set the same'
        ' values as the args list it received.'):
      self.client.GetBucket.expect(['potato'], {'bucket_name': 'hi'})

  def test_provided_error_raised(self):
    self.client.GetBucket.expect(error=Exception('hey'))

    with self.assertRaisesRegex(Exception, 'hey'):
      self.client.GetBucket()

  def test_provided_response_returned(self):
    self.client.GetBucket.expect(response='hi')

    self.assertEqual(self.client.GetBucket(), 'hi')

  def test_error_and_response_provided(self):
    self.client.GetBucket.expect(response='hi', error=Exception('hey'))

    with self.assertRaisesRegex(Exception, 'hey'):
      self.client.GetBucket()


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class PatchCloudApiTest(sdk_test_base.SdkBase):
  """Tests for the patch_cloud_api decorator."""

  def test_api_factory_patched(self):
    @mock_cloud_api.patch_cloud_api
    def helper(*_):
      self.assertIsInstance(api_factory.get_api(None),
                            mock_cloud_api.MockCloudApi)

    helper()

  def test_mock_client_argument_added_to_target(self):
    @mock_cloud_api.patch_cloud_api
    def helper(*args):
      self.assertIsInstance(args[0], mock_cloud_api.MockCloudApi)

    helper()

  def test_mock_client_close_called(self):
    # We can only assign to a mutable object from an inner function scope.
    # Python 3 has the nonlocal keyword, but that still triggers an invalid
    # syntax error even though we use "DoNotRunOnPy2".
    mock_client_holder = []

    @mock_cloud_api.patch_cloud_api
    def helper(*args):
      args[0].close = mock.Mock()
      mock_client_holder.append(args[0])

    helper()
    mock_client_holder[0].close.assert_called_once()


if __name__ == '__main__':
  test_case.main()
