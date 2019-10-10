# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Command with custom enum transform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base


class Enum(calliope_base.ListCommand):
  """List command test for the enum() transform function."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(a)')

  def Run(self, args):
    return [
        {
            'a': 1,
        },
        {
            'a': 2,
        },
        {
            'a': 11,
        },
    ]
