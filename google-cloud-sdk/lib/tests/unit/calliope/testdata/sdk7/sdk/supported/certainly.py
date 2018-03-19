# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""A command in a unicode supported group."""

from googlecloudsdk.calliope import base


class Certainly(base.Command):
  """A command in a unicode supported group."""

  @staticmethod
  def Args(parser):
    parser.add_argument(u'--søɨŧɇnłɏ', dest='certainly', default=u'уєѕ',
                        help=u'This will søɨŧɇnłɏ work.')

  def Run(self, args):
    return [args.certainly]
