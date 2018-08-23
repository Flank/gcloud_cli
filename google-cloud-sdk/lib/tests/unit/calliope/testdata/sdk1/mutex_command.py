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
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.calliope import base


class MutexArgCommand(base.Command):

  def Run(self, args):
    print(args.flag1a)
    print(args.flag1b)
    print(args.flag2a)
    print(args.flag2b)

  @staticmethod
  def Args(parser):
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--flag1a', action='store_true', help='Auxilio aliis.')
    group1.add_argument('--flag1b', action='store_true', help='Auxilio aliis.')

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--flag2a', action='store_true', help='Auxilio aliis.')
    group2.add_argument('--flag2b', action='store_true', help='Auxilio aliis.')
