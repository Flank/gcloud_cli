# -*- coding: utf-8 -*- #
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
"""This is a command for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from tests.lib.apitools import http_error


class ExceptionCommand(base.Command):

  @staticmethod
  def Args(parser):
    parser.add_argument('--unknown-error', action='store_true', required=False,
                        help='Auxilio aliis.')
    parser.add_argument('--http-error', action='store_true', required=False,
                        help='Auxilio aliis.')

  def Run(self, args):
    if args.http_error:
      raise exceptions.HttpException(
          http_error.MakeHttpError(404, 'some error'))
    if args.unknown_error:
      raise ValueError('Unknown Error')
    raise exceptions.ToolException('no reason', exit_code=2)
