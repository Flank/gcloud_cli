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
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.storage import mock_cloud_api

import mock


@test_case.Filters.DoNotRunOnPy2('Storage does not support Python 2.')
class PatchCloudApiTest(sdk_test_base.SdkBase):
  """Tests for the patch_cloud_api decorator."""

  def test_api_factory_patched(self):
    @mock_cloud_api.patch
    def helper(*_):
      self.assertIsInstance(api_factory.get_api(None), mock.Mock)

    helper()

  def test_mock_client_argument_added_to_target(self):
    @mock_cloud_api.patch
    def helper(*args):
      mock_client = args[0]
      self.assertIsInstance(mock_client, mock.Mock)

    helper()


if __name__ == '__main__':
  test_case.main()
