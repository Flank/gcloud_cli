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
"""Markdown test group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import base as calliope_base


class Markdown(calliope_base.Group):
  """Markdown group docstring index.

  Markdown group docstring description.
  """

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          This is a markdown test. If you change the docstrings or help strings
          or argparse flags or argparse positionals in this file you should get
          test regressions.

          Markdown DESCRIPTION detailed_help. The index entry is ``{index}''.
          Here comes _italic_ emphasis. And here comes *bold* emphasis. And
          asciidoc(1) says `monospace` looks like this, but I think its really
          literal. And Cloud SDK has its own ``text'' emphasis.

          Markdown lists are supported:

          * First item.
          ** First sub-item.
          * Second item.
          * Last item for now.
          ** Last sub-item for now.

          Did the end of list work? Also, format="csv" tables are recognized:

          Alias | Project | Image Name
          --- | --- | ---
          a1a1a | p1p1p | i1ii1
          a222 | p2 | i22222i2222
          a3aaaa3a3a3 | p3p3pp3p | iii3i3i

          Did the end of table work?

          I don't, you won't 'and' they didn't.

          Look at the files matching $HOME/*.txt or */x.

          And some manpage *ssh*(1)/*scp*(1) references. And alternate
          *ssh(1)*/*scp(1)* style too.

          Or maybe */* and *.go or why *.py.

          And what ``happens'' with ``air quotes''. And _then_ there's 'literal'
          quotes too.

          Perhaps *.c?

          And here are some hanging indent lists:

          *outer*::

          This is a big category:

          *inner-1*::: This is an inline example.
          *inner-2*::: Another example with no line separation.

          *inner-3*::: And a third one. With blah blah blah blah blah blah blah blah blah blah blah blah blah blah wrapping text.

          *inner-4*:::
          On a separate line. With more blah blah blah blah blah.
          And a second line.

          *outer-2*::

          And a smaller category:

          *inner-2-1*:::

          This is the first inner of the second outer.
          +
          And this is the second paragraph of the first inner of the second
          outer.

          And this should be back to normal text.

            $ gcloud markdown instance
            $ gcloud markdown markdown-command instance

          and more prose

            # example command.
            $ echo and more commands

          And the conclusion.
      """,

      'EXAMPLES': """\
          Inline $ gcloud command-group sub-sommand POSITIONAL command examples
          should become links. And example blocks should be monospace with
          links:

            $ gcloud group sub-command list POSITIONAL
            $ gcloud upper case stop command ABC-DEF abc xyz
            $ gcloud group-a command example-arg a b c
            $ gcloud group-b subgroup-c command my-arg a b c
            $ gcloud with group sample-arg a b c
            $ gcloud group set property value a b c
            $ gcloud group unset property a b c

          Long examples should wrap at 80 characters:

            $ gcloud group long-windeded super-verbose way too-long who-could ever remember-this obscure-command maybe too much of-the underlying-api IS EXPOSED

          And how does a multi-line example fare?

            $ gcloud first part
            $ gcloud second part

          And the conclusion.
      """,
  }

  @staticmethod
  def Args(parser):
    """Sets args for the command group."""
    parser.add_argument('--optional-flag',
                        required=False,
                        help='Optional flag.')
    parser.add_argument('--required-flag',
                        required=True,
                        help='Required flag.')

  def Run(self, unused_args):
    return 'Markdown.Run'
