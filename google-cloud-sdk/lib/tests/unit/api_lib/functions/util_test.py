# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the util module."""

from googlecloudsdk.api_lib.functions import util
from tests.lib import test_case


_ASCII_MESSAGE = "We're gettin' no place fast."
_UNICODE_MESSAGE = u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"


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


class FunctionsUtilTest(test_case.TestCase):

  def testFormatTimestamp_expectedInput(self):
    formatted = util.FormatTimestamp('2015-12-01T12:34:56.789012345Z')
    self.assertEqual('2015-12-01 12:34:56.789', formatted)

  def testFormatTimestamp_unexpectedInput(self):
    formatted = util.FormatTimestamp('2015-12-01 12:34:56')
    self.assertEqual('2015-12-01 12:34:56', formatted)

  def testGetHttpErrorMessageAscii(self):
    message = _ASCII_MESSAGE
    error = _MockHttpException(400, content=message)
    actual = util.GetHttpErrorMessage(error)
    self.assertTrue(message in actual)

  def testGetHttpErrorMessageUnicode(self):
    message = _UNICODE_MESSAGE
    error = _MockHttpException(400, content=message)
    actual = util.GetHttpErrorMessage(error)
    self.assertTrue(message in actual)

  def testGetHttpErrorMessageUtf8(self):
    message = _UNICODE_MESSAGE
    error = _MockHttpException(400, content=message.encode('utf8'))
    actual = util.GetHttpErrorMessage(error)
    self.assertTrue(message in actual)


if __name__ == '__main__':
  test_case.main()
