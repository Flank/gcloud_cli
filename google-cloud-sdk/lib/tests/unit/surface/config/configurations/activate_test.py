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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.configurations import named_configs
from tests.lib import test_case
from tests.lib.surface.config.configurations import test_base


class ActivateTest(test_base.ConfigurationsBaseTest):

  def testSuccessfulActivate(self):
    self.Run('config configurations create foo --no-activate')
    self.Run('config configurations create bar --no-activate')

    self.Run('config configurations list')
    self.AssertOutputContains('default True', normalize_space=True)
    self.AssertOutputContains('foo False', normalize_space=True)
    self.AssertOutputContains('bar False', normalize_space=True)
    self.ClearOutput()

    self.assertEqual('foo',
                     self.Run('config configurations activate foo'))
    self.AssertErrContains('Activated [foo].', normalize_space=True)

    self.Run('config configurations list')
    self.AssertOutputContains('default False', normalize_space=True)
    self.AssertOutputContains('bar False', normalize_space=True)
    self.AssertOutputContains('foo True', normalize_space=True)

    # Now verify that foo is unset as a side effect of activating bar
    self.ClearOutput()

    self.assertEqual('bar',
                     self.Run('config configurations activate bar'))
    self.AssertErrContains('Activated [bar].', normalize_space=True)

    self.Run('config configurations list')
    self.AssertOutputContains('default False', normalize_space=True)
    self.AssertOutputContains('bar True', normalize_space=True)
    self.AssertOutputContains('foo False', normalize_space=True)

  def testSuccessfulActivateNone(self):
    self.Run('config configurations create bar --no-activate')
    self.Run('config configurations activate bar')
    self.assertEqual('NONE',
                     self.Run('config configurations activate NONE'))

    self.Run('config configurations list')
    self.AssertOutputContains('bar False', normalize_space=True)

  def testBadConfigNameFail(self):
    with self.assertRaisesRegex(
        named_configs.NamedConfigError,
        r'Invalid name \[FOO\] for a configuration.  Except for special cases'):
      self.Run('config configurations activate FOO')

  def testMissingConfigFail(self):
    with self.assertRaisesRegex(
        named_configs.NamedConfigError,
        r'Cannot activate configuration \[foo\], it does not exist'):
      self.Run('config configurations activate foo')

  def testCompletion(self):
    self.Run('config configurations create foo --no-activate')
    self.Run('config configurations create bar --no-activate')
    self.Run('config configurations create baz --no-activate')
    self.RunCompletion('config configurations activate b', ['bar', 'baz'])


if __name__ == '__main__':
  test_case.main()

