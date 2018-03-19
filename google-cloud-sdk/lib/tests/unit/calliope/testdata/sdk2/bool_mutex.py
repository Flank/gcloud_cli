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
"""This is a command for testing grabbing the remainder args."""

from googlecloudsdk.calliope import base


class BoolMutex(base.Command):
  """A command with a Boolean flag in a mutex group."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--bool-independent',
        action='store_true',
        default=True,
        help='Independent Boolean flag on by default.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--bool-mutex',
        action='store_true',
        help='Boolean flag in mutex group.')
    group.add_argument(
        '--value',
        nargs=1,
        help='Value flag.')

  def Run(self, args):
    return {'boolean': args.boolean, 'value': args.value}
