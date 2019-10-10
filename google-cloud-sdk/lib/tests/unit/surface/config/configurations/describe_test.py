# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from googlecloudsdk.core.configurations import named_configs
from tests.lib import test_case
from tests.lib.surface.config.configurations import test_base


class DescribeTest(test_base.ConfigurationsBaseTest):

  def testMissingConfigFail(self):
    with self.assertRaises(named_configs.NamedConfigError):
      self.Run('config configurations describe foo')

  def testNoneConfigPrintsEmpty(self):
    d = self.Run('config configurations describe NONE')

    self.assertEqual(d, {'is_active': False, 'name': 'NONE', 'properties': {}})

    self.AssertErrEquals('')

  def testAllFlagGivesUnsetValues(self):
    d = self.Run('config configurations describe NONE --all')

    self.assertTrue('core' in d['properties'])
    self.assertTrue('container' in d['properties'])

    self.AssertOutputContains('core:')
    self.AssertOutputContains('account: null')

  def testDescribeConfigWithContents(self):
    self.Run('config configurations create foo')
    self.Run('config configurations activate foo')
    self.Run('config set container/cluster badgerbadgerbadger')

    d = self.Run('config configurations describe foo')

    self.assertEqual(
        d,
        {'is_active': True, 'name': 'foo',
         'properties': {'container': {'cluster': 'badgerbadgerbadger'}}})

    self.AssertOutputContains('container:')
    self.AssertOutputContains('cluster: badgerbadgerbadger')

  def testCompletion(self):
    self.Run('config configurations create foo')
    self.Run('config configurations create bar')
    self.Run('config configurations create baz')
    self.RunCompletion('config configurations describe b', ['bar', 'baz'])

if __name__ == '__main__':
  test_case.main()

