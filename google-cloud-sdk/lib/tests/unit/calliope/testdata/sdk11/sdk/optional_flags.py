# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import base as calliope_base

from six.moves import range  # pylint: disable=redefined-builtin


@calliope_base.UnicodeIsSupported
class OptionalFlags(calliope_base.Command):
  """Nothing Happens."""

  detailed_help = {
      'brief': 'A command with only optional flags.'}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    parser.add_argument(
        '--number-with-choices',
        type=int,
        choices=list(range(1, 4)),
        help='number from 1 to 4')

    parser.add_argument(
        '--pirates',
        type=Pirate,
        choices=[Pirate(123), Pirate(246)],
        help='pirate number')

  def Run(self, args):
    pass


class Pirate(object):
  """A testing class."""

  def __init__(self, value):
    self.value = int(value)

  def __hash__(self):
    return hash(self.value)

  def __str__(self):
    return '\u2620{}'.format(self.value)

  def __eq__(self, other):
    try:
      return other.value == self.value
    except AttributeError:
      return other is self

  def __ne__(self, other):
    return not self == other

  def __lt__(self, other):
    return self.value < other.value

  def __gt__(self, other):
    return self.value > other.value

  def __le__(self, other):
    return not self > other

  def __ge__(self, other):
    return not self < other
