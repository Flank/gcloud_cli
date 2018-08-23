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
"""This is a command for testing multiple positional args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class MultiplePositional(base.Command):
  """A command to test argument ordering in usage text."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'zzz',
        help='help for zzz',
        metavar='[USER@]ZZZ',
        nargs='+')
    parser.add_argument(
        'aaa',
        help='help for aaa',
        metavar='[USER@]AAA',
        nargs='+')

  def Run(self, args):
    pass
