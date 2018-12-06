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
"""gcloud sdk tests command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base


class SubGroupCommandA(calliope_base.Command):
  """gcloud sdk tests command."""

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    # 1 or more.
    parser.add_argument(
        'eureka',
        nargs=1,
        help='ghi the JKL.')

    # Two mutually exclusive flag groups.

    delete_group = parser.add_mutually_exclusive_group()

    delete_group.add_argument(
        '--delete-on',
        help="""\
       This flag is mutually exclusive with --delete-in.
       """)

    delete_group.add_argument(
        '--delete-in',
        help=('Specifies the amount of time until this image should become '
              'DELETED.'))

    obsolete_group = parser.add_mutually_exclusive_group()

    obsolete_group.add_argument(
        '--obsolete-on',
        help="""\
        This flag is mutually exclusive with --obsolete-in.
        """)

    obsolete_group.add_argument(
        '--obsolete-in',
        help=('Specifies the amount of time until this image should become '
              'OBSOLETE.'))
