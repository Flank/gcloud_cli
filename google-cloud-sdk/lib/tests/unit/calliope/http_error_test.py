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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.calliope import util


class HttpExceptionFormatTest(test_case.Base):

  _ERROR_FORMAT_ALL = """\
content: <{content}>
error_info: <{error_info}>
instance_name: <{instance_name}>
message: <{message}>
resource_name: <{resource_name}>
status_code: <{status_code}>
status_description: <{status_description}>
status_message: <{status_message}>
url: <{url}>
"""

  def SetUp(self):
    self.maxDiff = None
    properties.VALUES.core.account.Set('user@gmail.com')

  def testHttpException400(self):
    err = http_error.MakeHttpError(400)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '400'
  errors:
  - domain: global
    message: Invalid request.
    reason: Invalid request API reason.
  message: Invalid request.
location: mock-location
status: INVALID_ARGUMENT>
error_info: <code: '400'
errors:
- domain: global
  message: Invalid request.
  reason: Invalid request API reason.
message: Invalid request.>
instance_name: <>
message: <Invalid request API reason: Invalid request.>
resource_name: <>
status_code: <400>
status_description: <Invalid request API reason.>
status_message: <Invalid request.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException403(self):
    err = http_error.MakeHttpError(403)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '403'
  errors:
  - domain: global
    message: Permission denied.
    reason: Permission denied API reason.
  message: Permission denied.
location: mock-location
status: PERMISSION_DENIED>
error_info: <code: '403'
errors:
- domain: global
  message: Permission denied.
  reason: Permission denied API reason.
message: Permission denied.>
instance_name: <>
message: <Permission denied API reason: Permission denied.>
resource_name: <>
status_code: <403>
status_description: <Permission denied API reason.>
status_message: <Permission denied.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException404(self):
    err = http_error.MakeHttpError(404)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '404'
  errors:
  - domain: global
    message: Resource not found.
    reason: Resource not found API reason.
  message: Resource not found.
location: mock-location
status: NOT_FOUND>
error_info: <code: '404'
errors:
- domain: global
  message: Resource not found.
  reason: Resource not found API reason.
message: Resource not found.>
instance_name: <>
message: <Resource not found API reason: Resource not found.>
resource_name: <>
status_code: <404>
status_description: <Resource not found API reason.>
status_message: <Resource not found.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException409(self):
    err = http_error.MakeHttpError(409)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '409'
  errors:
  - domain: global
    message: Resource already exists.
    reason: Resource already exists API reason.
  message: Resource already exists.
location: mock-location
status: ALREADY_EXISTS>
error_info: <code: '409'
errors:
- domain: global
  message: Resource already exists.
  reason: Resource already exists API reason.
message: Resource already exists.>
instance_name: <>
message: <Resource already exists API reason: Resource already exists.>
resource_name: <>
status_code: <409>
status_description: <Resource already exists API reason.>
status_message: <Resource already exists.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException500(self):
    err = http_error.MakeHttpError(500)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '500'
  errors:
  - domain: global
    message: Internal server error.
    reason: Internal server error API reason.
  message: Internal server error.
location: mock-location
status: INTERNAL_SERVER_ERROR>
error_info: <code: '500'
errors:
- domain: global
  message: Internal server error.
  reason: Internal server error API reason.
message: Internal server error.>
instance_name: <>
message: <Internal server error API reason: Internal server error.>
resource_name: <>
status_code: <500>
status_description: <Internal server error API reason.>
status_message: <Internal server error.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException504(self):
    err = http_error.MakeHttpError(504)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '504'
  errors:
  - domain: global
    message: Deadline exceeded.
    reason: Deadline exceeded API reason.
  message: Deadline exceeded.
location: mock-location
status: DEADLINE_EXCEEDED>
error_info: <code: '504'
errors:
- domain: global
  message: Deadline exceeded.
  reason: Deadline exceeded API reason.
message: Deadline exceeded.>
instance_name: <>
message: <Deadline exceeded API reason: Deadline exceeded.>
resource_name: <>
status_code: <504>
status_description: <Deadline exceeded API reason.>
status_message: <Deadline exceeded.>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException666(self):
    err = http_error.MakeHttpError(666)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '666'
  errors:
  - domain: global
    message: ''
    reason: ''
  message: ''
location: mock-location
status: ''>
error_info: <code: '666'
errors:
- domain: global
  message: ''
  reason: ''
message: ''>
instance_name: <>
message: <HTTPError 666>
resource_name: <>
status_code: <666>
status_description: <>
status_message: <>
url: <>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException400WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        400, 'Your bad.',
        url='https://www.mock.googleapis.com/mock/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '400'
  errors:
  - domain: global
    message: Your bad.
    reason: Invalid request API reason.
  message: Your bad.
location: mock-location
status: INVALID_ARGUMENT>
error_info: <code: '400'
errors:
- domain: global
  message: Your bad.
  reason: Invalid request API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <Invalid request API reason: Your bad.>
resource_name: <projects>
status_code: <400>
status_description: <Invalid request API reason.>
status_message: <Your bad.>
url: <https://www.mock.googleapis.com/mock/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException403WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        403, 'Your bad.',
        url='https://www-mock.googleapis.com/mock/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '403'
  errors:
  - domain: global
    message: Your bad.
    reason: Permission denied API reason.
  message: Your bad.
location: mock-location
status: PERMISSION_DENIED>
error_info: <code: '403'
errors:
- domain: global
  message: Your bad.
  reason: Permission denied API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <User [user@gmail.com] does not have permission to access project [your-stuff] (or it may not exist): Your bad.>
resource_name: <projects>
status_code: <403>
status_description: <Permission denied API reason.>
status_message: <Your bad.>
url: <https://www-mock.googleapis.com/mock/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException404WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        404, 'Your bad.',
        url='https://www+mock.googleapis.com/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '404'
  errors:
  - domain: global
    message: Your bad.
    reason: Resource not found API reason.
  message: Your bad.
location: mock-location
status: NOT_FOUND>
error_info: <code: '404'
errors:
- domain: global
  message: Your bad.
  reason: Resource not found API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <Project [your-stuff] not found: Your bad.>
resource_name: <projects>
status_code: <404>
status_description: <Resource not found API reason.>
status_message: <Your bad.>
url: <https://www+mock.googleapis.com/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException409WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        409, 'Your bad.',
        url='https://mock.googleapis.com/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '409'
  errors:
  - domain: global
    message: Your bad.
    reason: Resource already exists API reason.
  message: Your bad.
location: mock-location
status: ALREADY_EXISTS>
error_info: <code: '409'
errors:
- domain: global
  message: Your bad.
  reason: Resource already exists API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <Resource in project [your-stuff] is the subject of a conflict: Your bad.>
resource_name: <projects>
status_code: <409>
status_description: <Resource already exists API reason.>
status_message: <Your bad.>
url: <https://mock.googleapis.com/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException500WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        500, 'Your bad.',
        url='https://mock.com/mocks/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '500'
  errors:
  - domain: global
    message: Your bad.
    reason: Internal server error API reason.
  message: Your bad.
location: mock-location
status: INTERNAL_SERVER_ERROR>
error_info: <code: '500'
errors:
- domain: global
  message: Your bad.
  reason: Internal server error API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <Internal server error API reason: Your bad.>
resource_name: <projects>
status_code: <500>
status_description: <Internal server error API reason.>
status_message: <Your bad.>
url: <https://mock.com/mocks/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException504WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        504, 'Your bad.',
        url='https://mock.com/mocks/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '504'
  errors:
  - domain: global
    message: Your bad.
    reason: Deadline exceeded API reason.
  message: Your bad.
location: mock-location
status: DEADLINE_EXCEEDED>
error_info: <code: '504'
errors:
- domain: global
  message: Your bad.
  reason: Deadline exceeded API reason.
message: Your bad.>
instance_name: <your-stuff>
message: <Deadline exceeded API reason: Your bad.>
resource_name: <projects>
status_code: <504>
status_description: <Deadline exceeded API reason.>
status_message: <Your bad.>
url: <https://mock.com/mocks/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)

  def testHttpException666WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        666, 'Your bad.',
        url='https://mock.com/mocks/v1/projects/your-stuff')
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
content: <debugInfo: mock-debug-info
error:
  code: '666'
  errors:
  - domain: global
    message: Your bad.
    reason: ''
  message: Your bad.
location: mock-location
status: ''>
error_info: <code: '666'
errors:
- domain: global
  message: Your bad.
  reason: ''
message: Your bad.>
instance_name: <your-stuff>
message: <HTTPError 666: Your bad.>
resource_name: <projects>
status_code: <666>
status_description: <>
status_message: <Your bad.>
url: <https://mock.com/mocks/v1/projects/your-stuff>
"""
    actual = str(exc)
    self.assertMultiLineEqual(expected, actual)


class CombinationsCommandTest(util.WithTestTool, cli_test_base.CliTestBase):

  def testCombinationsStatic(self):
    self.cli.Execute([
        'sdk2',
        'combinations',
        '--resource-list-type=static',
    ])
    self.AssertOutputEquals("""\
1
2
3
4
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
""")

  def testCombinationsStaticRaiseHttpError(self):
    with self.AssertRaisesHttpExceptionMatches(
        'User [None] does not have permission to access project [your-stuff] '
        '(or it may not exist): '
        'Permission denied.'):
      self.cli.Execute([
          'sdk2',
          'combinations',
          '--resource-list-type=static',
          '--raise-exception=http-error',
      ])
    self.AssertOutputEquals("""\
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
ERROR: (test.sdk2.combinations) User [None] does not have permission to access project [your-stuff] (or it may not exist): Permission denied.
""")

  def testCombinationsStaticRaiseHttpException(self):
    with self.AssertRaisesHttpExceptionMatches(
        'HTTP error code=403 resource=projects name=your-stuff'):
      self.cli.Execute([
          'sdk2',
          'combinations',
          '--resource-list-type=static',
          '--raise-exception=http-exception',
      ])
    self.AssertOutputEquals("""\
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
ERROR: (test.sdk2.combinations) HTTP error code=403 resource=projects name=your-stuff
""")

  def testCombinationsGenerator(self):
    self.cli.Execute([
        'sdk2',
        'combinations',
        '--resource-list-type=generator',
    ])
    self.AssertOutputEquals("""\
1
2
3
4
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
""")

  def testCombinationsGeneratorRaiseHttpError(self):
    with self.AssertRaisesHttpExceptionMatches(
        'User [None] does not have permission to access project [your-stuff] '
        '(or it may not exist): '
        'Permission denied.'):
      self.cli.Execute([
          'sdk2',
          'combinations',
          '--resource-list-type=generator',
          '--raise-exception=http-error',
      ])
    self.AssertOutputEquals("""\
1
2
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
ERROR: (test.sdk2.combinations) User [None] does not have permission to access project [your-stuff] (or it may not exist): Permission denied.
""")

  def testCombinationsGeneratorRaiseHttpException(self):
    with self.AssertRaisesHttpExceptionMatches(
        'HTTP error code=403 resource=projects name=your-stuff'):
      self.cli.Execute([
          'sdk2',
          'combinations',
          '--resource-list-type=generator',
          '--raise-exception=http-exception',
      ])
    self.AssertOutputEquals("""\
1
2
""")
    self.AssertErrEquals("""\
Filter Sdk1
Filter Sdk2
ERROR: (test.sdk2.combinations) HTTP error code=403 resource=projects name=your-stuff
""")


if __name__ == '__main__':
  test_case.main()
