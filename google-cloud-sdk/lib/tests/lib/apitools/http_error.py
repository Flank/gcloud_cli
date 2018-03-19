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

"""apitools_exceptions.HttpError test support."""

import json

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper


_HTTP_CODE_INFO = {
    400: (
        'Invalid request.',
        'INVALID_ARGUMENT',
        'Invalid request API reason.',
    ),
    403: (
        'Permission denied.',
        'PERMISSION_DENIED',
        'Permission denied API reason.',
    ),
    404: (
        'Resource not found.',
        'NOT_FOUND',
        'Resource not found API reason.',
    ),
    409: (
        'Resource already exists.',
        'ALREADY_EXISTS',
        'Resource already exists API reason.',
    ),
    500: (
        'Internal server error.',
        'INTERNAL_SERVER_ERROR',
        'Internal server error API reason.',
    ),
    504: (
        'Deadline exceeded.',
        'DEADLINE_EXCEEDED',
        'Deadline exceeded API reason.',
    ),
}


def MakeHttpError(code=400, message=None, reason=None, content=None, url=None):
  """Makes and returns an apitools HttpError exception.

  Args:
    code: The HTTP error code number. Must be in _HTTP_CODE_INFO.
    message: Context specific status message.
    reason: Status reason.
    content: A dict added to to the JSON body dict.
    url: The URL this error occurred at.

  Returns:
    An apitools HttpError exception.
  """
  (code_message, status, code_reason) = _HTTP_CODE_INFO.get(code, ('', '', ''))
  if not message:
    message = code_message
  if not reason:
    reason = code_reason
  response = {
      'content-type': 'application/json; charset=UTF-8',
      'reason': reason,
      'status': code,
  }
  body = {
      'error': {
          'code': str(code),
          'errors': [{
              'domain': 'global',
              'reason': reason,
              'message': message,
          }],
          'message': message,
      },
      'debugInfo': 'mock-debug-info',
      'location': 'mock-location',
      'status': status,
  }
  if content:
    body.update(content)
  http_response = http_wrapper.Response(
      info=response, content=json.dumps(body), request_url=url)
  return apitools_exceptions.HttpError.FromResponse(http_response)


def ExampleErrorDetails():
  """Gives an example of variation in error details types."""
  error_details = [
      {'@type': 'type.googleapis.com/google.rpc.BadRequest',
       'fieldViolations': [
           {
               'field': 'version.deployment.container.image',
               'description': 'Description of the violation.'
           }
       ]
      },
      {
          '@type': 'type.googleapis.com/google.rpc.DebugInfo',
          'detail': (
              '[ORIGINAL ERROR] error_type::error: Error details.'
              '\\nAnd then more details.')
      }
  ]
  return error_details


def MakeDetailedHttpError(code=400, message=None, reason=None, content=None,
                          url=None, details=None):
  """Creates an apitools HttpError with additional details ('v2' style).

  Args:
    code: The HTTP error code number. Must be in _HTTP_CODE_INFO.
    message: Context specific status message.
    reason: Status reason.
    content: A dict added to to the JSON body dict.
    url: The URL this error occurred at.
    details: A list of json objects representing any type of protocol buffers.
       Each object should be of the format {'type@': type, 'field1': data,
       ['field2': data, ...]} where
       the type is the protocol buffer type and the remaining fields are
       the unpacked fields from the message of that type.

  Returns:
    An apitools HttpError exception.
  """
  (code_message, status, code_reason) = _HTTP_CODE_INFO.get(
      code, ('', '', ''))
  if not message:
    message = code_message
  if not reason:
    reason = code_reason
  response = {
      'content-type': 'application/json; charset=UTF-8',
      'reason': reason,
      'status': code,
  }
  body = {
      'error': {
          'code': str(code),
          'details': details,
          'message': message,
          'status': status,
      },
      'debugInfo': 'mock-debug-info',
      'location': 'mock-location',
      'status': status,
  }
  if content:
    body.update(content)
  http_response = http_wrapper.Response(
      info=response, content=json.dumps(body), request_url=url)
  return apitools_exceptions.HttpError.FromResponse(http_response)
