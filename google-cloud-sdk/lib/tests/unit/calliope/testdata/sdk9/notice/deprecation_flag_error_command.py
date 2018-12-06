# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""This is a command for testing flag removal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions as calliope_actions
from googlecloudsdk.calliope import base as calliope_base


class DeprecationFlagErrorCommand(calliope_base.Command):
  """A simple command to test flag removal.

   {command} prints a test message.
  """

  @staticmethod
  def Args(parser):
    """Test args for this command."""
    deparg = calliope_base.Argument(
        '--testflag',
        action=calliope_actions.DeprecationAction(
            'testflag', removed=True, error='{flag_name} is REMOVED.'),
        help='Test flag for testing.')
    deparg.AddToParser(parser)

    parser.add_argument('--otherflag', nargs='?', help='The Other Flag')
    parser.display_info.AddFormat('value(.)')

  def Run(self, args):
    return 'Deprecation Flag Error Command Complete'
