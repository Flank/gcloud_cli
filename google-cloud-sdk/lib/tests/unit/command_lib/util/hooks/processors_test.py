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

"""Tests for the processors module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.hooks import processors
from googlecloudsdk.command_lib.util.hooks import types
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base


class ProcessorsTest(sdk_test_base.SdkBase):
  """Tests for processor Python Hooks.."""

  def testRelativeName(self):
    properties.VALUES.core.enable_gri.Set(True)
    ref = types.Resource(collection='compute.instances')('i:z:p')
    self.assertEqual(ref.RelativeName(), processors.RelativeName(ref))
    self.assertIsNone(processors.RelativeName(None))

  def testURI(self):
    properties.VALUES.core.enable_gri.Set(True)
    ref = types.Resource(collection='compute.instances')('i:z:p')
    self.assertEqual(ref.SelfLink(), processors.URI(ref))
    self.assertIsNone(processors.URI(None))


if __name__ == '__main__':
  sdk_test_base.main()
