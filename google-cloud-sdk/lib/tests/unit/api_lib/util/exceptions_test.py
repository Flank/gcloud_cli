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

import logging

from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error

import six


class HttpExceptionFormatTest(cli_test_base.CliTestBase):

  _ERROR_FORMAT_ALL = """\
api_name: <{api_name}>
api_version: <{api_version}>
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
    self.original_verbosity = log.GetVerbosity()

  def TearDown(self):
    log.SetVerbosity(self.original_verbosity)

  def testHttpException400FormatAll(self):
    err = http_error.MakeHttpError(400)
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)
    expected = """\
api_name: <>
api_version: <>
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
    self.assertEqual(expected, actual)

  def testHttpException400FormatAllUtf8(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                'Ṳᾔḯ¢◎ⅾℯ',
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: Ṳᾔḯ¢◎ⅾℯ call-1',
                    'file-2:line-2: Ṳᾔḯ¢◎ⅾℯ call-2',
                ],
                'message': [
                    'Memory fault: Ṳᾔḯ¢◎ⅾℯ dumped',
                ],
            },
        },
        message='A Ṳᾔḯ¢◎ⅾℯ error somewhere. Try and find it.',
        reason='A Ṳᾔḯ¢◎ⅾℯ error somewhere. Find and try it.',
    )
    exc = exceptions.HttpException(err, self._ERROR_FORMAT_ALL)

    # The expected value contains escaped unicode values for the JSON field
    # values because whoever generated the JSON data represented unicode
    # characters as C-style escapes. Other field values are unicode strings
    # containing valid unicode characters, so escape representation is not
    # needed. The raw JSON values are checked in this test because the they are
    # always preserved in the payload. That way the caller can debug
    # dump/decode/parse bugs using the original raw encoding.
    expected = """api_name: <mock>
api_version: <v1>
content: <debugInfo:
  message:
  - "Memory fault: \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F dumped"
  stackTrace:
  - "file-1:line-1: \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F call-1"
  - "file-2:line-2: \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F call-2"
error:
  code: '400'
  errors:
  - domain: global
    message: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Try and\\
      \\ find it."
    reason: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Find and\\
      \\ try it."
  message: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Try and find\\
    \\ it."
location: mock-location
status: INVALID_ARGUMENT
stuff:
- "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F">
error_info: <code: '400'
errors:
- domain: global
  message: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Try and find\\
    \\ it."
  reason: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Find and try\\
    \\ it."
message: "A \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F error somewhere. Try and find\\
  \\ it.">
instance_name: <>
message: <A \u1e72\u1f94\u1e2f\xa2\u25ce\u217e\u212f error somewhere. Find and try it: A \u1e72\u1f94\u1e2f\xa2\u25ce\u217e\u212f error somewhere. Try and find it.>
resource_name: <>
status_code: <400>
status_description: <A \u1e72\u1f94\u1e2f\xa2\u25ce\u217e\u212f error somewhere. Find and try it.>
status_message: <A \u1e72\u1f94\u1e2f\xa2\u25ce\u217e\u212f error somewhere. Try and find it.>
url: <https://mock.googleapis.com/v1/projects/your-stuff/junk/mine>
"""
    actual = six.text_type(exc)
    self.maxDiff = None
    self.assertEqual(expected, actual)

  def testHttpException400Content(self):
    err = http_error.MakeHttpError(400)
    exc = exceptions.HttpException(err, '{content}')
    self.assertEqual(
        '{"debugInfo": "mock-debug-info", "error": {"code": "400", "errors": '
        '[{"domain": "global", "message": "Invalid request.", "reason": '
        '"Invalid request API reason."}], "message": "Invalid request."}, '
        '"location": "mock-location", "status": "INVALID_ARGUMENT"}',
        str(exc.payload.content))

  def testHttpException400Message(self):
    err = http_error.MakeHttpError(400)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Invalid request API reason: Invalid request.',
        exc.payload.message)

  def testHttpException403Message(self):
    err = http_error.MakeHttpError(403)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Permission denied API reason: Permission denied.',
        exc.payload.message)

  def testHttpException404Message(self):
    err = http_error.MakeHttpError(404)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Resource not found API reason: Resource not found.',
        exc.payload.message)

  def testHttpException500Message(self):
    err = http_error.MakeHttpError(500)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Internal server error API reason: Internal server error.',
        exc.payload.message)

  def testHttpException504Message(self):
    err = http_error.MakeHttpError(504)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Deadline exceeded API reason: Deadline exceeded.',
        exc.payload.message)

  def testHttpException666Message(self):
    err = http_error.MakeHttpError(666)
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'HTTPError 666',
        exc.payload.message)

  def testHttpException400AttributesWithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        400,
        url='https://www.googleapis.com/mock/v1/projects/your-stuff',
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Invalid request API reason: Your bad.',
        exc.payload.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException403WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        403,
        url=('https://www-googleapis-staging.sandbox.google.com/mock/v1'
             '/projects/your-stuff'),
        message='Your bad.')
    properties.VALUES.core.account.Set('user@gmail.com')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'User [user@gmail.com] does not have permission to access project '
        '[your-stuff] (or it may not exist): Your bad.',
        exc.payload.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException404WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        404,
        url='https://mock.googleapis.com/v1/projects/your-stuff',
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Project [your-stuff] not found: Your bad.',
        str(exc))
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException409WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        409,
        url='https://some.other.domain/mock/v1/projects/your-stuff',
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        ('Resource in project [your-stuff] is the subject of a conflict: '
         'Your bad.'),
        exc.payload.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException500WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        500,
        url='https://www.googleapis.com/mock/v1/projects/your-stuff',
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Internal server error API reason: Your bad.',
        str(exc))
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException504WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        504,
        url=('https://www-googleapis-staging.sandbox.google.com/mock/v1'
             '/projects/your-stuff'),
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Deadline exceeded API reason: Your bad.',
        exc.payload.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException666WithMessageAndUrl(self):
    err = http_error.MakeHttpError(
        666,
        url='https://mock.googleapis.com/v1/projects/your-stuff',
        message='Your bad.')
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'HTTPError 666: Your bad.',
        exc.payload.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)

  def testHttpException400UrlNoHttp(self):
    err = http_error.MakeHttpError(
        400,
        url='url')
    exc = exceptions.HttpException(err)
    self.assertEqual('', exc.payload.api_name)
    self.assertEqual('', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlNoVersion(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com')
    exc = exceptions.HttpException(err)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlNoResource(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1')
    exc = exceptions.HttpException(err)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlNoInstance(self):
    err = http_error.MakeHttpError(
        400,
        url='https://www.googleapis.com/compute/v1/projects/')
    exc = exceptions.HttpException(err)
    self.assertEqual('compute', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlParseOK(self):
    err = http_error.MakeHttpError(
        400,
        url=('https://www.googleapis.com/compute/alpha/projects/mock-project/'
             'zones/us-east1-b/instances/mock-instance'))
    exc = exceptions.HttpException(err)
    self.assertEqual('compute', exc.payload.api_name)
    self.assertEqual('alpha', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlInstanceWithSlashRegistryParseOK(self):
    err = http_error.MakeHttpError(
        400,
        url=('https://www.googleapis.com/compute/alpha/projects/mock-project/'
             'zones/us-east1-b/instances/mock-instance/with-a-slash'))
    exc = exceptions.HttpException(err)
    self.assertEqual('compute', exc.payload.api_name)
    self.assertEqual('alpha', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException400UrlRegistryParseFails(self):
    err = http_error.MakeHttpError(
        400,
        url=('https://mock.googleapis.com/v1/projects/your-stuff'
             '/regions/global/clusters/my-stuff'))
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Invalid request API reason: Invalid request.', exc.message)
    self.assertEqual('mock', exc.payload.api_name)
    self.assertEqual('v1', exc.payload.api_version)
    self.assertEqual('', exc.payload.resource_name)
    self.assertEqual('', exc.payload.resource_item)
    self.assertEqual('', exc.payload.instance_name)

  def testHttpException404UrlRegistryParseFails(self):
    err = http_error.MakeHttpError(
        404,
        url=('https://cloudresourcemanager.googleapis.com/v1beta1/projects/'
             'error-reporting-gcloud-e2e-does-not-exist?alt=json'))
    exc = exceptions.HttpException(err)
    self.assertEqual(
        ('Project [error-reporting-gcloud-e2e-does-not-exist] not found: '
         'Resource not found.'),
        exc.message)
    self.assertEqual('cloudresourcemanager', exc.payload.api_name)
    self.assertEqual('v1beta1', exc.payload.api_version)
    self.assertEqual('projects', exc.payload.resource_name)
    self.assertEqual('project', exc.payload.resource_item)
    self.assertEqual(
        'error-reporting-gcloud-e2e-does-not-exist', exc.payload.instance_name)

  def testHttpException404UrlRegistryParseWithParms(self):
    err = http_error.MakeHttpError(
        404,
        url=('http://cloudresourcemanager.googleapis.com/v1beta1/organizations/'
             'ID?someParam=true&other=false'))
    exc = exceptions.HttpException(err)
    self.assertEqual(
        'Organization [ID] not found: Resource not found.', exc.message)
    self.assertEqual('cloudresourcemanager', exc.payload.api_name)
    self.assertEqual('v1beta1', exc.payload.api_version)
    self.assertEqual('organizations', exc.payload.resource_name)
    self.assertEqual('organization', exc.payload.resource_item)
    self.assertEqual('ID', exc.payload.instance_name)

  def testHttpExceptionErrorFormatAttributes(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                "We're in a tight spot.",
                "You're gonna need a bigger boat.",
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: call-1',
                    'file-2:line-2: call-2',
                ],
                'message': [
                    'Memory fault: core dumped',
                ],
            },
        },
    )
    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}{url?\n{?}}{.stuff?\n{?}}')
    self.assertEqual("""\
Error [400] Invalid request.
https://mock.googleapis.com/v1/projects/your-stuff/junk/mine
- We're in a tight spot.
- You're gonna need a bigger boat.""", exc.message)

  def testHttpExceptionErrorFormatAttributesWithExplicitLabel(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                "We're in a tight spot.",
                "You're gonna need a bigger boat.",
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: call-1',
                    'file-2:line-2: call-2',
                ],
                'message': [
                    'Memory fault: core dumped',
                ],
            },
        },
    )
    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] '
        '{status_message}{url?\n{?}}{.stuff?\n\nstuff:\n{?}}')
    self.assertEqual("""\
Error [400] Invalid request.
https://mock.googleapis.com/v1/projects/your-stuff/junk/mine

stuff:
- We're in a tight spot.
- You're gonna need a bigger boat.""", exc.message)

  def testHttpExceptionErrorFormatAttributesValueUnicode(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                'Ṳᾔḯ¢◎ⅾℯ',
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: call-1',
                    'file-2:line-2: call-2',
                ],
                'message': [
                    'Memory fault: core dumped',
                ],
            },
        },
    )
    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}{url?\n{?}}{.stuff?\n{?}}')
    self.assertEqual('''\
Error [400] Invalid request.
https://mock.googleapis.com/v1/projects/your-stuff/junk/mine
- "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F"''', exc.message)

  def testHttpExceptionErrorFormatAttributesDebugVerbosityDefaultLine(self):
    log.SetVerbosity(logging.DEBUG)
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                "We're in a tight spot.",
                "You're gonna need a bigger boat.",
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: call-1',
                    'file-2:line-2: call-2',
                ],
                'message': [
                    'Memory fault: core dumped',
                ],
            },
        },
    )
    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}{url?\n{?}}{.stuff?\n{?}}')
    self.assertEqual("""\
Error [400] Invalid request.
https://mock.googleapis.com/v1/projects/your-stuff/junk/mine
- We're in a tight spot.
- You're gonna need a bigger boat.""", exc.message)

  def testHttpExceptionDefaultErrorFormatDebugVerbosity(self):
    log.SetVerbosity(logging.DEBUG)
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'stuff': [
                "We're in a tight spot.",
                "You're gonna need a bigger boat.",
            ],
            'debugInfo': {
                'stackTrace': [
                    'file-1:line-1: call-1',
                    'file-2:line-2: call-2',
                ],
                'message': [
                    'Memory fault: core dumped',
                ],
            },
        },
    )
    exc = exceptions.HttpException(err)
    self.assertEqual("""\
Invalid request API reason: Invalid request.
message:
- 'Memory fault: core dumped'
stackTrace:
- 'file-1:line-1: call-1'
- 'file-2:line-2: call-2'""", exc.message)

  def testHttpExceptionErrorFormatAttributesNoStuff(self):
    err = http_error.MakeHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'shmeetails': [
                "We're in a tight spot.",
                "You're gonna need a bigger boat.",
            ],
        },
    )
    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}{url?\nurl={?}}{stuff?\n{?}}')
    self.assertEqual("""\
Error [400] Invalid request.
url=https://mock.googleapis.com/v1/projects/your-stuff/junk/mine""",
                     exc.message)

  def testHttpExceptionErrorFormatV2Details(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        details=http_error.ExampleErrorDetails(),
    )

    exc = exceptions.HttpException(err)
    self.assertEqual("""\
Invalid request API reason: Invalid request.
- '@type': type.googleapis.com/google.rpc.BadRequest
  fieldViolations:
  - description: Description of the violation.
    field: version.deployment.container.image
- '@type': type.googleapis.com/google.rpc.DebugInfo
  detail: '[ORIGINAL ERROR] error_type::error: Error details.\\n\
And then more details.'""",
                     exc.message)

  def testHttpExceptionErrorFormatV2ContentVsPayload(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'details': [
                {
                    '@type': 'type.googleapis.com/google.rpc.Quote',
                    'detail': "We're in a tight spot.",
                },
                {
                    '@type': 'type.googleapis.com/google.rpc.Quip',
                    'detail': "You're gonna need a bigger boat.",
                },
            ],
        },
        details=http_error.ExampleErrorDetails(),
    )

    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}'
        '{error.details.detail?\nerror.details.detail:\n{?}}'
        '{.details.detail?\n.details.detail:\n{?}}'
        '{details.detail?\ndetails.detail:\n{?}}'
    )
    self.assertEqual("""\
Error [400] Invalid request.
error.details.detail:
- '[ORIGINAL ERROR] error_type::error: Error details.\\n\
And then more details.'
.details.detail:
- We're in a tight spot.
- You're gonna need a bigger boat.
details.detail:
- '[ORIGINAL ERROR] error_type::error: Error details.\\n\
And then more details.'""",
                     exc.message)

  def testHttpExceptionErrorFormatV2ContentPrinterFormat(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'details': [
                {
                    '@type': 'type.googleapis.com/google.rpc.Quote',
                    'detail': "We're in a tight spot.",
                },
                {
                    '@type': 'type.googleapis.com/google.rpc.Quip',
                    'detail': "You're gonna need a bigger boat.",
                },
            ],
        },
        details=http_error.ExampleErrorDetails(),)

    exc = exceptions.HttpException(
        err, 'Error [{status_code}] {status_message}\n'
        '{.:value(details.detail.list(separator="\n"))}')
    self.assertEqual("""\
Error [400] Invalid request.
We're in a tight spot.
You're gonna need a bigger boat.""", exc.message)

  def testHttpExceptionErrorFormatV2FirstVsAggregate(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'Precondition check failed.',
                'status': 'FAILED_PRECONDITION',
                'details': [
                    {
                        '@type': 'type.googleapis.com/google.rpc.violations',
                        'violations': [
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                                'description': 'Remove the lien [1.1].',
                            },
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                                'description': 'Remove the lien [1.2].',
                            },
                        ],
                    },
                    {
                        '@type': 'type.googleapis.com/google.rpc.violations',
                        'violations': [
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-xyz',
                                'description': 'Remove the lien [2.1].',
                            },
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                                'description': 'Remove the lien [2.2].',
                            },
                        ],
                    },
                ],
            },
        },
        details=http_error.ExampleErrorDetails(),
    )

    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}'
        '{details.violations.description?\n'
        'details.violations.description:\n{?}}'
        '{details[0].violations[0].description?\n'
        'details[0].violations[0].description:\n{?}}'
    )
    self.assertEqual("""\
Error [400] Precondition check failed.
details.violations.description:
- - Remove the lien [1.1].
  - Remove the lien [1.2].
- - Remove the lien [2.1].
  - Remove the lien [2.2].
details[0].violations[0].description:
Remove the lien [1.1].""",
                     exc.message)

    exc = exceptions.HttpException(err)
    self.assertEqual("""\
Invalid request API reason: Precondition check failed.
- '@type': type.googleapis.com/google.rpc.violations
  violations:
  - description: Remove the lien [1.1].
    subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien
  - description: Remove the lien [1.2].
    subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien
- '@type': type.googleapis.com/google.rpc.violations
  violations:
  - description: Remove the lien [2.1].
    subject: liens/123-456-xyz
    type: type.googleapis.com/google.rpc.lien
  - description: Remove the lien [2.2].
    subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien""",
                     exc.message)

  def testHttpExceptionErrorFormatV2AggregateWithMissingDescription(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'Precondition check failed.',
                'status': 'FAILED_PRECONDITION',
                'details': [
                    {
                        '@type': 'type.googleapis.com/google.rpc.violations',
                        'violations': [
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                            },
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                                'description': 'Remove the lien [1.2].',
                            },
                        ],
                    },
                    {
                        '@type': 'type.googleapis.com/google.rpc.violations',
                        'violations': [
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-xyz',
                                'description': 'Remove the lien [2.1].',
                            },
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                            },
                        ],
                    },
                ],
            },
        },
        details=http_error.ExampleErrorDetails(),
    )

    exc = exceptions.HttpException(
        err,
        'Error [{status_code}] {status_message}'
        '{details.violations.description?\n{?}}'
    )
    self.assertEqual("""\
Error [400] Precondition check failed.
- - Remove the lien [1.2].
- - Remove the lien [2.1].""",
                     exc.message)

    exc = exceptions.HttpException(err)
    self.assertEqual("""\
Invalid request API reason: Precondition check failed.
- '@type': type.googleapis.com/google.rpc.violations
  violations:
  - subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien
  - description: Remove the lien [1.2].
    subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien
- '@type': type.googleapis.com/google.rpc.violations
  violations:
  - description: Remove the lien [2.1].
    subject: liens/123-456-xyz
    type: type.googleapis.com/google.rpc.lien
  - subject: liens/123-456-abc
    type: type.googleapis.com/google.rpc.lien""",
                     exc.message)

  def testCatchHTTPErrorRaiseHTTPException(self):
    @exceptions.CatchHTTPErrorRaiseHTTPException('Error [{status_code}]')
    def mock_run_with_exception():
      err = http_error.MakeHttpError(400)
      raise err

    # Check that the error message returned from the decorator is correct.
    with self.AssertRaisesExceptionMatches(exceptions.HttpException,
                                           'Error [400]'):
      mock_run_with_exception()

  def _GetFieldViolations(self, err):
    payload = exceptions.HttpErrorPayload(err)
    return payload.field_violations

  def testGetOneFieldViolation(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'The request has errors.',
                'status': 'INVALID_ARGUMENT',
                'details': [{
                    '@type': 'type.googleapis.com/google.rpc.BadRequest',
                    'fieldViolations': [{
                        'field': 'spec.revisionTemplate.spec.container.image',
                        'description':
                            'Invalid image provided in the revision'
                            ' template. Expected [region.]gcr.io/repo-path[:tag'
                            ' or @digest], obtained really/bad/image',
                    }]}]}},
        details=http_error.ExampleErrorDetails())
    self.assertEquals(
        self._GetFieldViolations(err),
        {'spec.revisionTemplate.spec.container.image':
             'Invalid image provided in the revision'
             ' template. Expected [region.]gcr.io/repo-path[:tag'
             ' or @digest], obtained really/bad/image'})

  def testGetSeveralFieldViolations(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'The request has errors.',
                'status': 'INVALID_ARGUMENT',
                'details': [{
                    '@type': 'type.googleapis.com/google.rpc.BadRequest',
                    'fieldViolations': [
                        {'field': 'blog.blug', 'description': 'hahaha'},
                        {'field': 'doop.doop', 'description': 'lol'},
                    ]}]}},
        details=http_error.ExampleErrorDetails())
    self.assertEquals(
        self._GetFieldViolations(err),
        {'blog.blug': 'hahaha', 'doop.doop': 'lol'})

  def testGetSeveralFieldViolationsOtherDetails(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'The request has errors.',
                'status': 'INVALID_ARGUMENT',
                'details': [
                    {
                        '@type': 'type.googleapis.com/google.rpc.violations',
                        'violations': [
                            {
                                'type': 'type.googleapis.com/google.rpc.lien',
                                'subject': 'liens/123-456-abc',
                            }]},
                    {
                        '@type': 'type.googleapis.com/google.rpc.BadRequest',
                        'fieldViolations': [
                            {'field': 'blog.blug', 'description': 'hahaha'},
                            {'field': 'doop.doop', 'description': 'lol'},
                        ]
                    }
                ]}},
        details=http_error.ExampleErrorDetails())
    self.assertEquals(
        self._GetFieldViolations(err),
        {'blog.blug': 'hahaha', 'doop.doop': 'lol'})

  def testGetNoFieldViolations(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={
            'error': {
                'code': 400,
                'message': 'The request has errors.',
                'status': 'INVALID_ARGUMENT',
                'details': []}},
        details=http_error.ExampleErrorDetails())
    self.assertEquals(self._GetFieldViolations(err), {})

  def testGetFieldViolationsBadJson(self):
    err = http_error.MakeDetailedHttpError(
        400,
        url='https://mock.googleapis.com/v1/projects/your-stuff/junk/mine',
        content={},
        details=http_error.ExampleErrorDetails())
    # Override content, since the factory doesn't let us make it invalid.
    err.content = 'this is bad json yo . it is . like. so bad'
    self.assertEquals(self._GetFieldViolations(err), {})


if __name__ == '__main__':
  test_case.main()
