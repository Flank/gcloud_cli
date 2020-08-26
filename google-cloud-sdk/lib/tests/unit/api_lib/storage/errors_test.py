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
"""Tests for googlecloudsdk.api_lib.storage.storage_api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.storage import errors as cloud_errors
from tests.lib import sdk_test_base
from tests.lib import test_case


class CatchHttpErrorRaiseGcsApiErrorTest(sdk_test_base.SdkBase):

  def test_decorator(self):
    @cloud_errors.catch_http_error_raise_gcs_api_error()
    def _error_func():
      raise apitools_exceptions.HttpError(None, None, None)

    with self.assertRaisesRegex(cloud_errors.GcsApiError, 'HTTPError 0'):
      _error_func()

  def test_custom_format(self):
    @cloud_errors.catch_http_error_raise_gcs_api_error('custom {message}')
    def _error_func():
      raise apitools_exceptions.HttpError(None, None, None)

    with self.assertRaisesRegex(cloud_errors.GcsApiError, 'custom HTTPError 0'):
      _error_func()

if __name__ == '__main__':
  test_case.main()
