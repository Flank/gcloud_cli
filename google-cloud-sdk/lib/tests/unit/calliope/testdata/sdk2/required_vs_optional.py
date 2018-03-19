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
"""This is a command for testing required vs optional flag combinations."""

from googlecloudsdk.calliope import base


class RequiredVsOptional(base.Command):
  """A command with required vs optional flag combinations."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--required-singleton',
        nargs=1,
        required=True,
        help='Required singleton flag.')
    parser.add_argument(
        '--optional-singleton',
        nargs=1,
        help='Optional singleton flag.')

    required_group = parser.add_mutually_exclusive_group(required=True)
    required_group.add_argument(
        '--this-one',
        nargs=1,
        help='This one.')
    required_group.add_argument(
        '--that-one',
        nargs=1,
        help='That one.')

    optional_group = parser.add_mutually_exclusive_group()
    optional_group.add_argument(
        '--six-of-one',
        nargs=1,
        help='Six of one.')
    optional_group.add_argument(
        '--half-dozen-of-the-other',
        nargs=1,
        help='Half dozen of the other.')

    stooge_group = parser.add_argument_group(
        help='These are the stooge related flags:')
    stooge_group.add_argument(
        '--moe',
        metavar='QUOTE',
        nargs=1,
        help='Why you.')
    stooge_group.add_argument(
        '--larry',
        metavar='QUOTE',
        nargs=1,
        help="I didn't wanna say yes but I couldn't say no.")
    stooge_group.add_argument(
        '--shemp',
        metavar='QUOTE',
        nargs=1,
        help='Hey Moe! Hey Larry!')

    parser.add_argument(
        'episode',
        help='your favorite eposide.')

  def Run(self, args):
    return {
        'required-singleton': args.required_singleton,
        'optional-singleton': args.optional_singleton,
        'this-one': args.this_one,
        'that-one': args.that_one,
        'six-of-one': args.six_of_one,
        'half-dozen-of-the-other': args.half_dozen_of_the_other,
    }
