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
"""gcloud sdk tests command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class LongHelp(base.Command):
  """A test command with long help."""

  detailed_help = {
      'brief': 'A test command with a long help section.',
      'DESCRIPTION': """\
      This is a command with a very long help section, and some newlines and
      things like that, and weird words including `castle`.

      It can be used to test displaying long help, or summarizing it as for
      `gcloud search-help`. If a person is searching the word `scorpion` or
      `tarantula`, this sentence should be in the excerpt. That way they
      know why they are seeing this command, because the brief help seems
      to have nothing to do with their search. Now we'll stick some other
      stuff in between to make sure that the first appearances of `scorpion`
      and `tarantula` aren't so close to the other terms in the next paragraph.

      On the other hand if they aren't looking for scary bugs and are searching
      the word `mittens`, the excerpt should center around this part.""",
      'EXAMPLES': """\
          $ gcloud sdk long-help
          $ gcloud sdk long-help --fake-flag
          Error: This error message has the word `gloves` in it.
          """}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    # Long help flag.
    parser.add_argument(
        '--long-flag',
        help="""\
        This is a flag with long help text.

        Item 1::
        Explanation 1.

        Item 2::
        Explanation 2.
        """)

    # Long help flag.
    parser.add_argument(
        'POSITIONAL',
        help=_GetHelp)


def _GetHelp():
  return """\
        This is a positional with long help text.

        Item 1::
        Explanation 1.

        Item 2::
        Explanation 2.
        """
