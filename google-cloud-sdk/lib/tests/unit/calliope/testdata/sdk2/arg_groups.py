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

"""Argument groups test command."""

from googlecloudsdk.calliope import base


class ArgGroups(base.Command):
  """Argument groups test command."""

  @staticmethod
  def Args(parser):
    rpg = parser.add_group(
        required=True,
        help='Required positional group.')
    rpg.add_argument(
        'required_modal_positional',
        help='Required modal positional.')
    rpg.add_argument(
        '--abc',
        action='store_true',
        help='Optional flag.')

    opg = parser.add_group(
        help='Optional positional group.')
    opg.add_argument(
        'optional_modal_positional',
        nargs='*',
        help='Optional modal positional.')
    opg.add_argument(
        '--def',
        action='store_true',
        help='Optional flag.')

    rfg = parser.add_group(
        required=True,
        help='Required flag group.')
    rfg.add_argument(
        '--required-modal-flag',
        required=True,
        action='store_true',
        help='Required modal flag.')
    rfg.add_argument(
        '--ghi',
        action='store_true',
        help='Optional flag.')

    ofg = parser.add_group(
        help='Optional flag group.')
    ofg.add_argument(
        '--optional-modal-flag',
        required=True,
        action='store_true',
        help='Optional modal flag.')
    ofg.add_argument(
        '--jkl',
        action='store_true',
        help='Optional flag.')

  def Run(self, args):
    return None
