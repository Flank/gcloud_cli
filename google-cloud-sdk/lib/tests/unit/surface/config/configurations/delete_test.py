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

import os

from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.config.configurations import test_base


class DeleteTest(test_base.ConfigurationsBaseTest):

  def testDeleteActiveFail(self):
    self.Run('config configurations create foo')

    with self.assertRaisesRegex(named_configs.NamedConfigError,
                                r'Deleting named configuration failed because '
                                r'configuration \[foo\] is set as active.'):
      self.Run('config configurations delete foo')

  def testDeleteActiveMultiFail(self):
    self.Run('config configurations create foo')
    self.Run('config configurations create bar --no-activate')

    with self.assertRaisesRegex(named_configs.NamedConfigError,
                                r'Deleting named configuration failed because '
                                r'configuration \[foo\] is set as active.'):
      self.Run('config configurations delete foo bar')

  def testDeleteActiveOverrideFail(self):
    self.Run('config configurations create foo')

    os.environ['CLOUDSDK_ACTIVE_CONFIG_NAME'] = 'bar'

    # Fails to remove both foo and bar because bar is actually active, but foo
    # is active in the file.
    with self.assertRaisesRegex(
        named_configs.NamedConfigError,
        r'Cannot delete configuration \[foo\], it is currently set as the '
        r'active configuration in your gcloud properties.'):
      self.Run('config configurations delete foo')

  def testDeleteMissingFail(self):
    with self.assertRaisesRegex(
        named_configs.NamedConfigError,
        r'Cannot delete configuration \[foo\], it does not exist.'):
      self.Run('config configurations delete foo')

  def testDeleteOk(self):
    self.Run('config configurations create foo')
    self.Run('config configurations create bar --no-activate')

    self.Run('config configurations delete bar')

    self.AssertErrContains('Deleted')
    self.assertTrue(os.path.exists(self.named_config_file_prefix + 'foo'))
    self.assertFalse(os.path.exists(self.named_config_file_prefix + 'bar'))

  def testDeleteMultiOk(self):
    self.Run('config configurations create foo')
    self.Run('config configurations create bar')
    self.Run('config configurations create baz')
    self.Run('config configurations create bat')
    self.Run('config configurations activate foo')

    self.Run('config configurations delete bar baz bat')

    self.AssertErrContains('Deleted')
    self.assertTrue(os.path.exists(self.named_config_file_prefix + 'foo'))
    self.assertFalse(os.path.exists(self.named_config_file_prefix + 'bar'))
    self.assertFalse(os.path.exists(self.named_config_file_prefix + 'baz'))
    self.assertFalse(os.path.exists(self.named_config_file_prefix + 'bat'))

  def testDeletePromptsWithNoFails(self):
    properties.VALUES.core.disable_prompts.Set(False)

    self.Run('config configurations create foo --no-activate')

    self.WriteInput('n\n')
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'Aborted by user.'):
      self.Run('config configurations delete foo')

    self.AssertErrContains('The following configurations will be deleted:\n'
                           ' - foo')

  def testDeletePromptsWithYesDeletes(self):
    properties.VALUES.core.disable_prompts.Set(False)

    self.Run('config configurations create foo --no-activate')

    self.WriteInput('y\n')
    self.Run('config configurations delete foo')
    self.AssertErrContains('Deleted')

  def testDeletePromptsCanBeDisabled(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run('config configurations create foo --no-activate')
    self.Run('config configurations delete foo')
    self.AssertErrNotContains(
        'The following configuration will be deleted: [foo]')

  def testCompletion(self):
    self.Run('config configurations create foo --no-activate')
    self.Run('config configurations create bar --no-activate')
    self.Run('config configurations create baz --no-activate')
    self.RunCompletion('config configurations delete b', ['bar', 'baz'])


if __name__ == '__main__':
  test_case.main()
