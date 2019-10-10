# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""This is a command for testing grabbing the remainder args."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import argparse

from googlecloudsdk.calliope import base as calliope_base


class Remainder(calliope_base.Command):
  """A command to test remainder args."""

  @staticmethod
  def Args(parser):
    parser.add_argument('single_positional', help='Auxilio aliis.')
    parser.add_argument('--foo', help='Auxilio aliis.', required=True)
    parser.add_argument(
        'everything', metavar='PASSTHROUGH_ARGS', nargs=argparse.REMAINDER,
        help='Auxilio aliis.')

  def Run(self, args):
    return args.everything

  def Display(self, args, result):
    print(str(result))
