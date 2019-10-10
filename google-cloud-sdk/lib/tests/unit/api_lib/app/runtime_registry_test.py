# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import runtime_registry
from tests.lib import sdk_test_base
from tests.lib import test_case


class RuntimeRegistryTest(sdk_test_base.WithLogCapture):
  _DEFAULT_REGISTRY = {
      runtime_registry.RegistryEntry('intercal', {env.FLEX}):
          'intercal-value',
      runtime_registry.RegistryEntry('x86-asm', {env.STANDARD}):
          'x86-asm-value',
  }

  def testGet_MatchFound(self):
    registry = runtime_registry.Registry(self._DEFAULT_REGISTRY)

    self.assertEqual(registry.Get('intercal', env.FLEX),
                     'intercal-value')

  def testGet_RightRuntimeWrongEnv(self):
    default = 'default-value'
    registry = runtime_registry.Registry(
        self._DEFAULT_REGISTRY, default=default)

    self.assertEqual(
        registry.Get('intercal', env.STANDARD),
        default,
        'A matching runtime with an incorrect environment should result in the '
        'default.')

  def testGet_DefaultFalse(self):
    registry = runtime_registry.Registry(
        self._DEFAULT_REGISTRY, default=False)

    self.assertFalse(
        registry.Get('intercal', env.STANDARD),
        'A matching runtime with an incorrect environment should result in the '
        'default.')

  def testGet_RegexpRuntime(self):
    default = 'default-value'
    registry = runtime_registry.Registry({
        runtime_registry.RegistryEntry(re.compile('pattern[12]$'),
                                       {env.FLEX}):
        'pattern-value'
    }, default=default)

    self.assertEqual(registry.Get('pattern1', env.FLEX),
                     'pattern-value')
    self.assertEqual(registry.Get('pattern2', env.FLEX),
                     'pattern-value')
    self.assertEqual(registry.Get('pattern3', env.FLEX),
                     default)

  def testGet_MultipleEnv(self):
    registry = runtime_registry.Registry({
        runtime_registry.RegistryEntry('intercal', {env.FLEX,
                                                    env.STANDARD}):
        'intercal-value'
    })

    self.assertEqual(registry.Get('intercal', env.FLEX),
                     'intercal-value')
    self.assertEqual(registry.Get('intercal', env.STANDARD),
                     'intercal-value')

  def testGet_Override(self):
    registry = runtime_registry.Registry({
        runtime_registry.RegistryEntry(
            re.compile(r'.*'),
            {env.FLEX, env.STANDARD}): 'dummy'
    }, override='my-override')

    self.assertEqual(registry.Get('anything', env.FLEX),
                     'my-override')
    self.assertEqual(registry.Get('anything', env.STANDARD),
                     'my-override')

  def testGet_NoMatchFound(self):
    default = 'default-value'
    registry = runtime_registry.Registry(
        self._DEFAULT_REGISTRY, default=default)
    self.assertEqual(
        registry.Get('bad', env.FLEX), default,
        'A non-matching runtime should always result in the default.')

  def testGet_NoMatchFoundNoDefault(self):
    registry = runtime_registry.Registry(self._DEFAULT_REGISTRY)
    self.assertEqual(
        registry.Get('bad', env.FLEX), None,
        'A non-matching runtime should return None if no default is provided.')


if __name__ == '__main__':
  test_case.main()
