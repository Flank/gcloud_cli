# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for api_lib.app.env."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import env
from tests.lib import parameterized
from tests.lib import test_case


class TiRegistryTest(parameterized.TestCase, test_case.TestCase):
  """Tests for matching runtimes marked Ti."""

  def SetUp(self):
    self.registry = env.GetTiRuntimeRegistry()

  @parameterized.parameters(
      ('nodejs8', env.STANDARD, True),
      ('nodejs9', env.STANDARD, True),
      ('nodejs10', env.STANDARD, True),
      ('nodejs8', env.FLEX, False),
      ('nodejs8', env.MANAGED_VMS, False),
      ('php55', env.STANDARD, False),
      ('php72', env.STANDARD, True),
      ('php72', env.FLEX, False),
      ('php73', env.STANDARD, True),
      ('php8', env.STANDARD, True),
      ('php80', env.STANDARD, True),
      ('python', env.STANDARD, False),
      ('python', env.FLEX, False),
      ('python27', env.STANDARD, False),
      ('python28', env.STANDARD, False),
      ('python3', env.STANDARD, True),
      ('python37', env.STANDARD, True),
      ('python38', env.STANDARD, True),
      ('python4', env.STANDARD, False),
      ('other', env.STANDARD, False),
      ('other', env.FLEX, False)
  )
  def testIsTiRuntime(self, runtime, environment, is_ti):
    self.assertEquals(self.registry.Get(runtime, environment), is_ti)

