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
"""Internal tests command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base


class XyzZY(calliope_base.Command):
  """Internal tests command."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--input_param', type=int, default=10, help='first input')
    parser.add_argument(
        '--input-param', type=int, default=10, help='output input')
    parser.add_argument(
        '-H', '--hyper', type=int, default=1, help='short capitalized flag')
    parser.add_argument(
        '--bad-list', nargs='*', help='Auxilio aliis.')
    parser.add_argument(
        '--mediocre-list', type=arg_parsers.ArgList(), help='Auxilio aliis.')
    parser.add_argument(
        '--mediocre-dict', type=arg_parsers.ArgDict(), help='arg dict')
