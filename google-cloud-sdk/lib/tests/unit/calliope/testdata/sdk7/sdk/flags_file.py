# -*- coding: utf-8 -*- #
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

"""Command for testing --flags-file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base


class FlagsFile(calliope_base.ListCommand):
  """Test --flags-file by displaying the parsed args."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--boolean', action='store_true', help='Auxilio aliis I.')
    parser.add_argument(
        '--string', default='DEFAULT-FLAG', help='Auxilio aliis II.')
    parser.add_argument(
        '--integer', type=int, default=0, help='Auxilio aliis III.')
    parser.add_argument(
        '--floating', type=float, default=-0.9, help='Auxilio aliis IV.')
    parser.add_argument(
        '--list', type=arg_parsers.ArgList(),
        metavar='ITEMS', help='Auxilio aliis V.')
    parser.add_argument(
        '--dict', type=arg_parsers.ArgDict(),
        metavar='ATTRIBUTES', help='Auxilio aliis VI.')

    group = parser.add_group(
        mutex=True, required=True, help='Auxilio aliis VII.')
    group.add_argument(
        '--this', help='Auxilio aliis VIII.')
    group.add_argument(
        '--or-that', help='Auxilio aliis IX.')

  def Run(self, args):
    return args
