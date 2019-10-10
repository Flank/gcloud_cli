# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for api_lib.app.operations_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error

import mock


class CollectOpErrorsTest(test_case.TestCase):
  """Tests for CallAndCollectOpErrors(method, *args, **kwargs)."""

  def testMethodSucceeds(self):
    """Method succeeds, make sure it is called with the right args."""
    method = mock.Mock(return_value='return_val')
    operations_util.CallAndCollectOpErrors(method, 'positional', param=123)
    method.assert_called_once_with('positional', param=123)

  def testMethodFailsWithHttpError(self):
    """Method fails with HttpError, check for misc error with friendly str."""
    http_err = http_error.MakeHttpError()
    http_exception = api_exceptions.HttpException(http_err)
    # Raised error must serialize to the same as the original http exception
    err_str = re.escape(str(http_exception))
    method = mock.Mock(side_effect=http_err)
    with self.assertRaisesRegex(operations_util.MiscOperationError, err_str):
      operations_util.CallAndCollectOpErrors(method, 'positional', param=123)

  def testMethodFailsWithOperationError(self):
    """Method fails with OperationError, check for our misc error."""
    operation_err = operations_util.OperationError('custom msg')
    # Raised error must serialize to the same as the original op error
    err_str = re.escape(str(operation_err))
    method = mock.Mock(side_effect=operation_err)
    with self.assertRaisesRegex(operations_util.MiscOperationError, err_str):
      operations_util.CallAndCollectOpErrors(method, 'positional', param=123)

  def testMethodFailsWithUnrelatedError(self):
    """Method fails with different err, check that it falls through."""
    method = mock.Mock(side_effect=ValueError(14))
    with self.assertRaises(ValueError):
      operations_util.CallAndCollectOpErrors(method, 'positional', param=123)

if __name__ == '__main__':
  test_case.main()
