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
"""Helper functions for all 'gcloud firebase test' unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime

from googlecloudsdk.calliope import parser_extensions
from tests.lib.apitools import http_error


def FakeDateTime():
  return datetime.datetime(2015, 3, 14, 9, 26, 53, 589793)


def MakeHttpError(reason, message, code=404):
  """Create an exceptions.HttpError with a specified reason and message.

  The HttpError is of the form that would be thrown by an apitools RPC.

  Args:
    reason: str, the specified reason
    message: str, the specified message
    code: int, the http error code

  Returns:
    the generated HttpError
  """
  individual_error = {
      'reason': reason,
      'message': message,
      'location': '<dummy location>',
      'debugInfo': '<dummy debug info>'
  }
  error_list_dict = {
      'errors': [individual_error],
      'code': code,
      'message': message
  }
  server_error = {'error': error_list_dict}
  return http_error.MakeHttpError(
      code=code, message=message, reason=reason, content=server_error)


def NewNameSpace(all_args, **kwargs):
  """Create a Namespace containing an attribute for each element of all_args.

  All args for the run command in the specified release track, except those
  appearing in **kwargs, are set to None by default so that unit tests won't get
  missing attribute errors.

  Args:
    all_args: a list of all `firebase test run` args.
    **kwargs: a map of any args which should have values other than None.
  Returns:
    The created argparse.Namespace instance.
  """
  arg_dict = {arg: None for arg in all_args}
  arg_dict['argspec'] = None  # Positional args don't have a CLI flag name
  arg_dict.update(kwargs)
  return parser_extensions.Namespace(**arg_dict)
