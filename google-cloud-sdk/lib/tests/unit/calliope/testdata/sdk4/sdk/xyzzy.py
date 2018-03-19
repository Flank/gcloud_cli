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
"""gcloud sdk tests command."""

from googlecloudsdk.calliope import base


class XyzZY(base.Command):
  """Nothing Happens."""

  detailed_help = {
      'brief': 'Brief description of what Nothing Happens means.',
      'EXAMPLES': """\
          Try these:
          $ echo one
          $ gcloud components list
          """}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    # 0 or 1.
    parser.add_argument(
        '--zero-or-one',
        nargs='?',
        help='Zero or one description.')

    # 0 or more.
    parser.add_argument(
        '--zero-or-more',
        nargs='*',
        help='Zero or more description.')

    # Exactly 1.
    parser.add_argument(
        '--exactly-one',
        metavar='STOOGE',
        default='Curly',
        help='Exactly one description.')

    # 1 or more.
    parser.add_argument(
        '--one-or-more',
        nargs='+',
        metavar='ATTRIBUTE',
        help='One or more description.')

    # Exactly 3.
    parser.add_argument(
        '--exactly-three',
        nargs=3,
        metavar='STOOGE',
        default=['Moe', 'Larry', 'Shemp'],
        required=True,
        help='Exactly three description.')

    # 0 or more.
    parser.add_argument(
        'pdq',
        nargs='*',
        help='pdq the PDQ.')

    parser.add_argument(
        '--hidden',
        action='store_true',
        hidden=True,
        help='THIS TEXT SHOULD BE HIDDEN.')
