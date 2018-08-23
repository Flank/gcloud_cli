# -*- coding: utf-8 -*- #
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

"""Command with custom enum transform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_transform


class Enum(base.ListCommand):
  """List command test for the enum() transform function."""

  @staticmethod
  def Args(parser):
    state = {'RUNNING': 1, 'STOPPED': 0}
    transforms = {resource_transform.GetTypeDataName('state', 'enum'): state}
    parser.display_info.AddTransforms(transforms)

    parser.display_info.AddFormat("""
      table(
        a.enum(state, undefined="?"),
        b.enum(state, inverse=true, undefined="?")
      )
    """)

  def Run(self, args):
    return [
        {
            'a': 'RUNNING',
            'b': 1,
        },
        {
            'a': 'STOPPED',
            'b': 0,
        },
        {
            'a': 'BOGUS',
            'b': 99,
        },
    ]
