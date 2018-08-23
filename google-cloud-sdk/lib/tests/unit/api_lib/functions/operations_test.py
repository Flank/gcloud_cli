# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Unit tests for the operations module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions import operations
from tests.lib import test_case


_ASCII_MESSAGE = "We're gettin' no place fast."
_UNICODE_MESSAGE = ".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"


class _MockHttpResponse(object):

  def __init__(self, status='STATUS', reason=404):
    self.status = status
    self.reason = reason


class _MockHttpException(object):

  def __init__(self, status='STATUS', code=404, message='MESSAGE',
               content='CONTENT'):
    self.status = status
    self.code = code
    self.content = content
    self.message = message
    self.response = _MockHttpResponse(status=status, reason=code)


class FunctionsOperationsTest(test_case.TestCase):

  def testGetOperationErrorAscii(self):
    message = _ASCII_MESSAGE
    error = _MockHttpException(400, message=message)
    actual = operations.OperationErrorToString(error)
    self.assertTrue(message in actual)

  def testGetOperationErrorUnicode(self):
    message = _UNICODE_MESSAGE
    error = _MockHttpException(400, message=message)
    actual = operations.OperationErrorToString(error)
    self.assertTrue(message in actual)

  def testGetOperationErrorUtf8(self):
    message = _UNICODE_MESSAGE
    error = _MockHttpException(400, message=message.encode('utf8'))
    actual = operations.OperationErrorToString(error)
    self.assertTrue(message in actual)


if __name__ == '__main__':
  test_case.main()
