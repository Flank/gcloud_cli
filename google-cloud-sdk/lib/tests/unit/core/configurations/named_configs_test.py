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
"""Tests for googlecloudsdk.core.configurations.named_configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from googlecloudsdk.core import config
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


class NamedConfigTestBase(sdk_test_base.SdkBase):

  def SetUp(self):
    self.named_config_activator = os.path.join(self.global_config_path,
                                               'active_config')
    self.named_config_dir = os.path.join(self.global_config_path,
                                         'configurations')
    self.StartEnvPatch({})

  def ClearAllConfigurations(self):
    if os.path.exists(self.named_config_dir):
      files.RmTree(self.named_config_dir)
    if os.path.isfile(self.named_config_activator):
      os.remove(self.named_config_activator)
    elif os.path.isdir(self.named_config_activator):
      files.RmTree(self.named_config_activator)


class PublicInterfaceTests(NamedConfigTestBase):

  def AssertExistingConfigs(self, active, *names):
    configs = named_configs.ConfigurationStore.AllConfigs()
    self.assertEqual(len(names), len(configs))
    for n in names:
      self.assertIn(n, configs)

    configs = named_configs.ConfigurationStore.AllConfigs(
        include_none_config=True)
    self.assertEqual(len(names) + 1, len(configs))
    for n in names:
      self.assertIn(n, configs)
    self.assertIn('NONE', configs)

    self.assertEqual(active,
                     named_configs.ConfigurationStore.ActiveConfig().name)

  def testCreateDefault(self):
    self.ClearAllConfigurations()
    active = named_configs.ConfigurationStore.ActiveConfig()
    self.assertEqual('default', active.name)
    self.assertEqual(True, active.is_active)
    self.assertEqual(
        os.path.join(self.named_config_dir, 'config_default'), active.file_path)
    self.assertEqual({}, active.GetProperties())

  def testCreateDefaultWithAutoMigrate(self):
    self.ClearAllConfigurations()
    with open(config.Paths().user_properties_path, 'w') as f:
      f.write('[core]\naccount = foo\n')
    active = named_configs.ConfigurationStore.ActiveConfig()
    self.assertEqual('default', active.name)
    self.assertEqual(True, active.is_active)
    self.assertEqual(
        os.path.join(self.named_config_dir, 'config_default'), active.file_path)
    self.assertEqual({'core': {'account': 'foo'}}, active.GetProperties())

  def testWorkflow(self):
    self.ClearAllConfigurations()
    self.AssertExistingConfigs('default', 'default')

    named_configs.ConfigurationStore.CreateConfig('foo')
    self.AssertExistingConfigs('default', 'default', 'foo')

    with self.assertRaises(named_configs.NamedConfigError):
      named_configs.ConfigurationStore.CreateConfig('foo')
    self.AssertExistingConfigs('default', 'default', 'foo')

    named_configs.ConfigurationStore.CreateConfig('bar')
    self.AssertExistingConfigs('default', 'default', 'foo', 'bar')

    named_configs.ConfigurationStore.ActivateConfig('foo')
    self.AssertExistingConfigs('foo', 'default', 'foo', 'bar')

    with self.assertRaises(named_configs.NamedConfigError):
      named_configs.ConfigurationStore.ActivateConfig('baz')
    self.AssertExistingConfigs('foo', 'default', 'foo', 'bar')

    with self.assertRaises(named_configs.NamedConfigError):
      named_configs.ConfigurationStore.DeleteConfig('foo')
    self.AssertExistingConfigs('foo', 'default', 'foo', 'bar')

    encoding.SetEncodedValue(os.environ, 'CLOUDSDK_ACTIVE_CONFIG_NAME', 'bar')
    with self.assertRaisesRegex(named_configs.NamedConfigError,
                                'currently active'):
      named_configs.ConfigurationStore.DeleteConfig('bar')
    with self.assertRaisesRegex(named_configs.NamedConfigError,
                                'gcloud properties'):
      named_configs.ConfigurationStore.DeleteConfig('foo')
    self.AssertExistingConfigs('bar', 'default', 'foo', 'bar')

    encoding.SetEncodedValue(os.environ, 'CLOUDSDK_ACTIVE_CONFIG_NAME', None)
    named_configs.ConfigurationStore.DeleteConfig('bar')
    self.AssertExistingConfigs('foo', 'default', 'foo')
    with self.assertRaisesRegex(named_configs.NamedConfigError,
                                'does not exist'):
      named_configs.ConfigurationStore.DeleteConfig('bar')

    named_configs.ConfigurationStore.ActivateConfig('default')
    self.AssertExistingConfigs('default', 'default', 'foo')
    named_configs.ConfigurationStore.DeleteConfig('foo')

  def testSentinel(self):
    paths = config.Paths()
    self.ClearAllConfigurations()
    self.AssertExistingConfigs('default', 'default')

    # Don't touch sentinel when updating config on non-active configuration.
    c = named_configs.ConfigurationStore.CreateConfig('foo')
    c.PersistProperty('core', 'account', 'foo')
    self.assertFalse(os.path.isfile(paths.config_sentinel_file))

    # Do update it if the configuration is active.
    c = named_configs.ConfigurationStore.ActiveConfig()
    c.PersistProperty('core', 'account', 'foo')
    self.assertTrue(os.path.isfile(paths.config_sentinel_file))

    # Do update it if you change the active configuration.
    os.remove(paths.config_sentinel_file)
    self.assertFalse(os.path.isfile(paths.config_sentinel_file))
    named_configs.ConfigurationStore.ActivateConfig('foo')
    self.assertTrue(os.path.isfile(paths.config_sentinel_file))

  def testInvalidateWithSentinel(self):
    paths = config.Paths()
    # No sentinel to start.
    self.assertFalse(os.path.isfile(paths.config_sentinel_file))

    # A normal invalidate doesn't touch the sentinel.
    named_configs.ActivePropertiesFile.Invalidate()
    self.assertFalse(os.path.isfile(paths.config_sentinel_file))

    # This one does.
    named_configs.ActivePropertiesFile.Invalidate(mark_changed=True)
    self.assertTrue(os.path.isfile(paths.config_sentinel_file))

    # Get the current timestamp of the file, and set it back a bunch to avoid
    # race conditions.
    orig_timestamp = os.path.getmtime(paths.config_sentinel_file)
    fake_timestamp = orig_timestamp - 1000
    os.utime(paths.config_sentinel_file, (fake_timestamp, fake_timestamp))
    # Make sure the update worked. You can't do direct comparison of timestamps.
    self.assertLess(os.path.getmtime(paths.config_sentinel_file),
                    orig_timestamp)

    # Touch it again and ensure the mtime got updated.
    named_configs.ActivePropertiesFile.Invalidate(mark_changed=True)
    new_timestamp = os.path.getmtime(paths.config_sentinel_file)
    self.assertGreater(new_timestamp, fake_timestamp)

  def testErrors(self):
    self.ClearAllConfigurations()
    files.MakeDir(self.named_config_activator)
    with self.assertRaisesRegex(named_configs.NamedConfigFileAccessError,
                                re.escape(r'sufficient read permissions')):
      named_configs.ConfigurationStore.ActiveConfig()

    self.ClearAllConfigurations()
    with open(self.named_config_dir, 'w'):
      pass
    with self.assertRaises(named_configs.NamedConfigFileAccessError):
      named_configs.ConfigurationStore.AllConfigs()
    with self.assertRaises(named_configs.NamedConfigFileAccessError):
      named_configs.ConfigurationStore.CreateConfig('foo')
    with self.assertRaises(named_configs.InvalidConfigName):
      named_configs.ConfigurationStore.CreateConfig('NONE')
    with self.assertRaises(named_configs.InvalidConfigName):
      named_configs.ConfigurationStore.DeleteConfig('NONE')

  def testCorruptActiveConfigFile(self):
    self.ClearAllConfigurations()
    active = named_configs.ConfigurationStore.ActiveConfig()
    self.assertEqual('default', active.name)
    named_configs.ActivePropertiesFile.Invalidate(mark_changed=True)

    # Write a bunch of junk.
    self.ClearAllConfigurations()
    with open(self.named_config_activator, 'w') as f:
      f.write('\0\0\0\0\0\0')

    # Ensure it got reset back to default.
    active = named_configs.ConfigurationStore.ActiveConfig()
    self.assertEqual('default', active.name)
    with open(self.named_config_activator, 'r') as f:
      # Make sure the file actually got updated.
      active = f.read()
      self.assertEqual('default', active)

    named_configs.ActivePropertiesFile.Load()
    self.ClearAllConfigurations()


class HelperMethodTests(NamedConfigTestBase):

  def testEnsureValidConfigName(self):
    good = ['a', 'a-bc', 'a0-a1-a2-']
    bad = ['AAA', '111', 'None', 'foo bar', '-']

    for s in good:
      for allow_reserved in [True, False]:
        named_configs._EnsureValidConfigName(s, allow_reserved=allow_reserved)

    for s in bad:
      for allow_reserved in [True, False]:
        with self.assertRaisesRegex(named_configs.InvalidConfigName,
                                    r'Invalid name \['):
          named_configs._EnsureValidConfigName(s, allow_reserved=allow_reserved)

    named_configs._EnsureValidConfigName('NONE', allow_reserved=True)
    with self.assertRaisesRegex(named_configs.InvalidConfigName,
                                r'Invalid name \['):
      named_configs._EnsureValidConfigName('NONE', allow_reserved=False)

  def testFileForConfig(self):
    paths = config.Paths()
    self.assertEqual(
        os.path.join(self.named_config_dir, 'config_foo'),
        named_configs._FileForConfig('foo', paths))
    self.assertEqual(None, named_configs._FileForConfig('NONE', paths))

  def testActiveConfigFromFile(self):
    # Nothing set
    self.ClearAllConfigurations()
    self.assertEqual(None, named_configs._ActiveConfigNameFromFile())

    # Bad file is an error
    files.MakeDir(self.named_config_activator)
    with self.assertRaises(named_configs.NamedConfigFileAccessError):
      named_configs._ActiveConfigNameFromFile()

    self.ClearAllConfigurations()
    with open(self.named_config_activator, 'w') as f:
      f.write('foo')
    self.assertEqual('foo', named_configs._ActiveConfigNameFromFile())

  def testEffectiveActiveConfigName(self):
    self.ClearAllConfigurations()
    self.assertEqual(None, named_configs._EffectiveActiveConfigName())

    # From the file
    with open(self.named_config_activator, 'w') as f:
      f.write('foo')
    self.assertEqual('foo', named_configs._EffectiveActiveConfigName())

    # Env override
    encoding.SetEncodedValue(os.environ, 'CLOUDSDK_ACTIVE_CONFIG_NAME', 'bar')
    self.assertEqual('bar', named_configs._EffectiveActiveConfigName())

    named_configs.FLAG_OVERRIDE_STACK.Push('baz')
    self.assertEqual('baz', named_configs._EffectiveActiveConfigName())

  def testCreateDefaultNoCreate(self):
    self.ClearAllConfigurations()
    active = named_configs.ActiveConfig(force_create=False)
    self.assertEqual('default', active.name)
    self.assertEqual(True, active.is_active)
    self.assertEqual(
        os.path.join(self.named_config_dir, 'config_default'), active.file_path)
    self.assertEqual({}, active.GetProperties())
    self.assertFalse(os.path.exists(active.file_path))

  def testCreateDefaultWithAutoMigrateNoForce(self):
    self.ClearAllConfigurations()
    with open(config.Paths().user_properties_path, 'w') as f:
      f.write('[core]\naccount = foo\n')
    active = named_configs.ActiveConfig(force_create=False)
    self.assertEqual('default', active.name)
    self.assertEqual(True, active.is_active)
    self.assertEqual(
        os.path.join(self.named_config_dir, 'config_default'), active.file_path)
    self.assertEqual({'core': {'account': 'foo'}}, active.GetProperties())
    # File exists even though we said not to force create since there were
    # legacy properties.
    self.assertTrue(os.path.exists(active.file_path))


class FlagStackTests(NamedConfigTestBase):

  def testBasics(self):
    stack = named_configs._FlagOverrideStack()
    self.assertEqual(None, stack.ActiveConfig())

    stack.Push('foo')
    self.assertEqual('foo', stack.ActiveConfig())
    stack.Push(None)
    self.assertEqual('foo', stack.ActiveConfig())
    stack.Push('bar')
    self.assertEqual('bar', stack.ActiveConfig())
    stack.Push('NONE')
    self.assertEqual('NONE', stack.ActiveConfig())
    stack.PushFromArgs(['--configuration', 'baz'])
    self.assertEqual('baz', stack.ActiveConfig())

    stack.Pop()
    self.assertEqual('NONE', stack.ActiveConfig())
    stack.Pop()
    self.assertEqual('bar', stack.ActiveConfig())
    stack.Pop()
    self.assertEqual('foo', stack.ActiveConfig())
    stack.Pop()
    self.assertEqual('foo', stack.ActiveConfig())
    stack.Pop()
    self.assertEqual(None, stack.ActiveConfig())

  def testParseFlags(self):
    combos = [
        ['--configuration', 'foo'],
        ['asdf', '--configuration', 'foo', 'asdf'],
        ['--configuration=foo'],
        ['asdf', '--configuration=foo', 'asdf'],
    ]
    stack = named_configs._FlagOverrideStack()
    for combo in combos:
      self.assertEqual('foo', stack._FindFlagValue(combo))

    combos = [
        ['foo'],
        ['--configuration'],
        ['asdf', '--configuration-something', 'foo', 'asdf'],
        ['asdf', '--configuration'],
    ]
    for combo in combos:
      self.assertEqual(None, stack._FindFlagValue(combo))


class ActivePropertiesFileLoadingTests(NamedConfigTestBase):

  def testLoad(self):
    self.ClearAllConfigurations()
    named_configs.ConfigurationStore.CreateConfig('foo')
    named_configs.ConfigurationStore.ActivateConfig('foo')

    load_mock = self.StartObjectPatch(properties_file, 'PropertiesFile')
    named_configs.ActivePropertiesFile.Invalidate()
    named_configs.ActivePropertiesFile.Load()
    load_mock.assert_called_with([config.Paths().installation_properties_path,
                                  os.path.join(self.named_config_dir,
                                               'config_foo')])
    named_configs.ActivePropertiesFile.Load()
    load_mock.assert_called_with([config.Paths().installation_properties_path,
                                  os.path.join(self.named_config_dir,
                                               'config_foo')])

    named_configs.ActivePropertiesFile.Invalidate()
    named_configs.ConfigurationStore.ActivateConfig('NONE')
    load_mock.reset_mock()
    named_configs.ActivePropertiesFile.Load()
    load_mock.assert_called_with([config.Paths().installation_properties_path,
                                  None])

    named_configs.ActivePropertiesFile.Invalidate()
    encoding.SetEncodedValue(os.environ, 'CLOUDSDK_ACTIVE_CONFIG_NAME', 'other')
    load_mock.reset_mock()
    named_configs.ActivePropertiesFile.Load()
    load_mock.assert_called_with([config.Paths().installation_properties_path,
                                  os.path.join(self.named_config_dir,
                                               'config_other')])

  def testBadConfig(self):
    with open(self.named_config_activator, 'w') as f:
      f.write('BoGus')
    named_configs.ActivePropertiesFile.Load()


if __name__ == '__main__':
  test_case.main()
