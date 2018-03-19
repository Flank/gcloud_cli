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

import os

from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.config.configurations import test_base


class CreateTest(test_base.ConfigurationsBaseTest):

  def testCantWriteConfigurationsDirFail(self):
    if os.path.exists(self.named_config_dir):
      files.RmTree(self.named_config_dir)
    with open(self.named_config_dir, 'w') as f:
      f.write('xxx')

    with self.assertRaisesRegexp(
        named_configs.NamedConfigFileAccessError,
        r'Failed to create configuration \[foo\]'):
      self.Run('config configurations create foo')

  def _CheckCreated(self, config_name, activated=True):
    self.AssertErrContains('Created [{name}].'.format(name=config_name),
                           normalize_space=True)
    if activated:
      self.AssertErrContains('Activated [{name}]'.format(name=config_name))
    else:
      self.AssertErrContains(
          'To use this configuration, activate it by running:\n'
          '  $ gcloud config configurations activate {name}\n\n'.format(
              name=config_name))
    self.assertTrue(os.path.isfile(self.named_config_file_prefix + config_name))
    self.Run('config configurations list')
    if activated:
      self.AssertOutputContains('{name} True'.format(name=config_name),
                                normalize_space=True)
    else:
      self.AssertOutputContains('{name} False'.format(name=config_name),
                                normalize_space=True)

  def testSuccessfulCreateSimple(self):
    # Test create with neither --activate flag nor property set
    self.assertEquals('foo', self.Run('config configurations create foo'))
    self._CheckCreated('foo')
    self.assertEquals('bar', self.Run('config configurations create bar'))
    self._CheckCreated('bar')

  def testSuccessfulCreateWithActivateFlag(self):
    self.assertEquals('foo', self.Run('config configurations create foo '
                                      '--activate'))
    self._CheckCreated('foo')

  def testSuccessfulCreateWithNoActivateFlag(self):
    self.assertEquals('foo', self.Run('config configurations create foo '
                                      '--no-activate'))
    self._CheckCreated('foo', activated=False)

  def testBadConfigName(self):
    with self.assertRaisesRegexp(
        named_configs.NamedConfigError,
        r'Invalid name \[FOO\] for a configuration.  Except for special cases'):
      self.Run('config configurations create FOO')

  def testCreateTwiceFails(self):
    self.Run('config configurations create foo')
    with self.assertRaisesRegexp(
        named_configs.NamedConfigError,
        r'Cannot create configuration \[foo\], it already exists.'):
      self.Run('config configurations create foo')

if __name__ == '__main__':
  test_case.main()

