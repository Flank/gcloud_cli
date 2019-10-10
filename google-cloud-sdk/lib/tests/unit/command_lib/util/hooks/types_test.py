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

"""Tests of the types module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.hooks import types
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base


class TypesTest(sdk_test_base.SdkBase, parameterized.TestCase):
  """Tests for type Python hooks."""

  @parameterized.parameters(
      # No value just returns None.
      (None, 'compute.instances', None, None),
      (None, 'compute.instances', 'v1', None),
      (None, 'pubsub.projects.topics', None, None),
      (None, 'pubsub.projects.topics', 'v1', None),
      # Parse full value.
      ('i:z:p', 'compute.instances', None, 'projects/p/zones/z/instances/i'),
      ('i:z:p', 'compute.instances', 'v1', 'projects/p/zones/z/instances/i'),
      ('t:p', 'pubsub.projects.topics', None, 'projects/p/topics/t'),
      ('t:p', 'pubsub.projects.topics', 'v1', 'projects/p/topics/t'),
      # Parse partial value.
      ('i:z', 'compute.instances', None, 'projects/x/zones/z/instances/i'),
      ('i:z', 'compute.instances', 'v1', 'projects/x/zones/z/instances/i'),
      ('t', 'pubsub.projects.topics', None, 'projects/x/topics/t'),
      ('t', 'pubsub.projects.topics', 'v1', 'projects/x/topics/t'),
  )
  def testResource(self, value, collection, api_version, expected):
    properties.VALUES.core.project.Set('x')
    properties.VALUES.core.enable_gri.Set(True)
    result = types.Resource(collection, api_version=api_version)(value)
    self.assertEqual(expected, result.RelativeName() if result else None)


if __name__ == '__main__':
  sdk_test_base.main()
