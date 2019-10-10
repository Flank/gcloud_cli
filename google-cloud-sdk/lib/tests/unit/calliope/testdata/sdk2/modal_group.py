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
"""This is a command for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base


class ModalGroup(calliope_base.Command):
  """A command with a modal group with multiple required flags."""

  @staticmethod
  def Args(parser):
    mixed_modal = parser.add_group('Mixed modal group test.')
    mixed_modal.add_argument(
        '--required', action='store_true', required=True,
        help='Some required setting.')
    mixed_modal.add_argument(
        '--required-as-well', action='store_true', required=True,
        help='Another required setting.')
    mixed_modal.add_argument(
        '--optional-value', help='Optional mode value.')

    all_required = parser.add_group('All required modal group test.')
    all_required.add_argument(
        '--required-one', action='store_true', required=True,
        help='First required flag.')
    all_required.add_argument(
        '--required-two', action='store_true', required=True,
        help='Second required flag.')

  def Run(self, args):
    pass
