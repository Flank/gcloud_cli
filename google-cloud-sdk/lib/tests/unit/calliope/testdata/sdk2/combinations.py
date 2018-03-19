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
"""A command to test generator / exception combinations."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from tests.lib.apitools import http_error


class UnknownError(exceptions.Error):
  """Unknown error that won't cause gcloud crash."""


def _MakeUnknownError():
  """Returns an unknown exception."""
  return UnknownError('Unknown error.')


class Combinations(base.Command):
  """A command to test generator / exception combinations."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--resource-list-type',
        choices=['generator', 'static'],
        default='static',
        help='Set the resource list function type.')
    parser.add_argument(
        '--raise-exception',
        choices=['http-error', 'http-exception', 'none', 'unknown'],
        default='none',
        help='Raise an exception in the named class.')
    parser.display_info.AddFormat('value(status)')

  def _RaiseException(self):
    if self.args.raise_exception == 'none':
      return
    if self.args.raise_exception == 'unknown':
      raise _MakeUnknownError()
    error = http_error.MakeHttpError(
        403, url='https://mock.com/mocks/v1/projects/your-stuff')
    if self.args.raise_exception == 'http-error':
      raise error
    raise calliope_exceptions.HttpException(
        error,
        'HTTP error '
        'code={status_code} resource={resource_name} name={instance_name}')

  def _GenerateResources(self):
    yield {'status': 1}
    yield {'status': 2}
    self._RaiseException()
    yield {'status': 3}
    yield {'status': 4}

  def _StaticResources(self):
    self._RaiseException()
    return [
        {'status': 1},
        {'status': 2},
        {'status': 3},
        {'status': 4},
    ]

  def Run(self, args):
    self.args = args
    if self.args.resource_list_type == 'generator':
      return self._GenerateResources()
    else:
      return self._StaticResources()
