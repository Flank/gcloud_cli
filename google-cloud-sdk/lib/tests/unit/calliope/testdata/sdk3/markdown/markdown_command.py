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
"""Markdown test command with underscore in source name."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base


class Markdown(calliope_base.Command):
  """Markdown command docstring index.

  Markdown command docstring description. This is a markdown test. If you
  change the docstrings or help strings or argparse flags or argparse
  positionals in this file you should get test regressions. Use
  {parent_command} foo. Don't forget the ``MAGIC_SAUCE@FOO_BAR.COM'' arg.
  See gcloud_command_abc-xyz_list(1) or run $ gcloud command abc-xyz list --help
  for more information.

  ## EXAMPLES

  To foo the command run:

    $ {command} list --foo

  To bar the parent command run:

    $ {parent_command} --bar list

  ## SPECIAL MODES

  * STOPPED - not running

  * RUNNING - not stopped

  ## SEE ALSO

  https://foo.bar.com/how-to-foo-the-bar
  """

  @staticmethod
  def Args(parser):
    """Sets args for the command group."""
    parser.add_argument(
        'sources',
        help='Specifies a source file.',
        metavar='[[USER@]INSTANCE:]SRC',
        nargs='+')

    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        metavar='[[USER@]INSTANCE:]DEST')

    parser.add_argument(
        '--store-false-default-none-flag',
        action='store_false', default=False,
        help='Command store_false flag with None default value.')

    parser.add_argument(
        '--store-false-default-false-flag',
        action='store_false', default=False,
        help="""\
        Detailed help for --store-false-default-false-flag.
        """)
    parser.add_argument(
        '--store-false-default-true-flag',
        action='store_false', default=True,
        help='Command store_false flag with True default value.')

    parser.add_argument(
        '--store-true-default-false-flag',
        action='store_true', default=False,
        help='Command store_true flag with False default value.')

    parser.add_argument(
        '--store-true-default-none-flag',
        action='store_true', default=None,
        help='Command store_true flag with None default value.')

    parser.add_argument(
        '--store-true-default-true-flag',
        action='store_true', default=True,
        help='Command store_true flag with True default value.')

    parser.add_argument(
        '--z-required-flag',
        required=True,
        help='Command required flag help.')

    parser.add_argument(
        '--y-common-flag',
        default='VALUE',
        category=calliope_base.COMMONLY_USED_FLAGS,
        help='Command common flag help.')

    calliope_base.FILTER_FLAG.AddToParser(parser)

    parser.add_argument(
        '--value-flag',
        default='VALUE',
        help='Command value flag help.')

    parser.add_argument(
        '--root-flag',
        default='/', metavar='ROOT_PATH',
        help='Command root flag help.')

    parser.add_argument(
        '--question-flag',
        nargs='?',
        help='Command question flag help.')

    parser.add_argument(
        '--list-flag',
        type=arg_parsers.ArgList(),
        metavar='ITEM',
        default=['aaa', 'bbb', 'ccc'],
        help='Command star flag help.')

    parser.add_argument(
        '--dict-flag',
        type=arg_parsers.ArgDict(),
        metavar='ITEM',
        default={'aaa': 1, 'bbb': 22, 'ccc': 'aha'},
        help='Command star flag help.')

    parser.add_argument(
        '--choices-list',
        metavar='CHOICE',
        choices=['bar', 'foo', 'none'],
        default='none',
        help='Choices list flag help.')

    parser.add_argument(
        '--choices-list-arg-list',
        metavar='CHOICE',
        type=arg_parsers.ArgList(choices=['bar', 'foo', 'none']),
        default='none',
        help='Choices list flag help.')

    parser.add_argument(
        '--choices-dict',
        metavar='CHOICE',
        choices={
            'bar': 'Choice description for bar.',
            'foo': 'Choice description for foo.',
            'none': 'Choice description for none.',
        },
        default='none',
        help='The ... must be one of ... line should be in this paragraph')

    parser.add_argument(
        '--choices-dict-arg-list',
        metavar='CHOICE',
        type=arg_parsers.ArgList(choices={
            'bar': 'Choice description for bar.',
            'foo': 'Choice description for foo.',
            'none': 'Choice description for none.',
        }),
        default='none',
        help='The ... must be one of ... line should be in this paragraph')

    parser.add_argument(
        '--choices-dict-bloviate',
        metavar='CHOICE',
        choices={
            'bar': 'Choice description for bar.',
            'foo': 'Choice description for foo.',
            'none': 'Choice description for none.',
        },
        default='none',
        help="""\
            Choices dict bloviate flag help.

            Another paragraph for some complication.

            The '... must be one of ...' line should be in its own paragraph.
            """)

    parser.add_argument(
        '--choices-list-only-one-choice-yes-we-really-do-this',
        metavar='CHOICE',
        choices=['this-is-it'],
        default='this-is-it',
        help='Automaticallly fess up to only one choice.')

    parser.add_argument(
        '--choices-dict-only-one-choice-yes-we-really-do-this',
        metavar='CHOICE',
        choices={
            'this-is-it': 'You have no choice in this matter.',
        },
        default='this-is-it',
        help='Automaticallly fess up to only one choice.')

    parser.add_argument(
        'user_host',
        metavar='[USER@]INSTANCE',
        help="""\
        Specifies the instance to SSH into.

        ``USER'' specifies the username with which to SSH. If omitted,
        $USER from the environment is selected.
        """)

    parser.add_argument(
        'implementation_args',
        nargs=argparse.REMAINDER,
        help="""\
        Flags and positionals passed to the underlying ssh implementation.

        The '--' argument must be specified between gcloud specific args on
        the left and IMPLEMENTATION-ARGS on the right. Example:

          $ {command} example-instance --zone us-central1-a -- -vvv -L 80:%INSTANCE%:80
        """)

  def Run(self, unused_args):
    return 'Markdown_command.Run'
