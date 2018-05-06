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
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file
from googlecloudsdk.core.resource import session_capturer
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base

import mock


class ConfigTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)

  def Project(self):
    return None

  def AssertPropertySet(self, prop, value, scope):
    section, name = properties.ParsePropertyString(prop)
    if scope == properties.Scope.USER:
      values = (named_configs.ConfigurationStore.AllConfigs()['default']
                .GetProperties())
    else:
      values = (properties_file.PropertiesFile(
          [config.Paths().installation_properties_path]).AllProperties())
    self.assertEqual(value, values.get(section, {}).get(name, None))

  def testSetUnsetList(self):
    self.Run('config set core/account foo')
    self.AssertPropertySet('core/account', 'foo', properties.Scope.USER)
    self.AssertPropertySet('core/account', None, properties.Scope.INSTALLATION)
    self.AssertErrContains('Updated property [core/account].')
    self.ClearErr()
    self.Run('config list')
    self.AssertOutputContains('account = foo', normalize_space=True)
    self.ClearOutput()

    self.Run('config set --installation core/account bar')
    self.AssertErrContains('Updated installation property [core/account].')
    self.ClearErr()
    self.AssertPropertySet('core/account', 'foo', properties.Scope.USER)
    self.AssertPropertySet('core/account', 'bar', properties.Scope.INSTALLATION)
    self.Run('config list')
    self.AssertOutputContains('account = foo', normalize_space=True)
    self.ClearOutput()

    self.Run('config unset account')
    self.AssertErrContains('Unset property [core/account].')
    self.ClearErr()
    self.AssertPropertySet('core/account', None, properties.Scope.USER)
    self.AssertPropertySet('core/account', 'bar', properties.Scope.INSTALLATION)
    self.Run('config list')
    self.AssertOutputContains('account = bar', normalize_space=True)
    self.ClearOutput()

    self.Run('config unset --installation account')
    self.AssertErrContains('Unset installation property [core/account].')
    self.AssertPropertySet('core/account', None, properties.Scope.USER)
    self.AssertPropertySet('core/account', None, properties.Scope.INSTALLATION)
    self.Run('config list')
    self.AssertOutputNotContains('account', normalize_space=True)

  def testInvalidProperties(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('config set "" bar')
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('config set core/ bar')

    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('config unset ""')
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('config unset core/')

  def testGetValueWithNonDefaultConfiguration(self):
    self.Run('config configurations create foo')
    self.Run('config set core/project foo-bar')
    self.Run('config get-value core/project')
    self.AssertOutputEquals('foo-bar\n')
    self.AssertErrContains('Your active configuration is: [foo]')

  def testGetValue(self):
    # Test Happy Path(s)
    self.Run('config set core/account foo')
    self.Run('config set core/project bar')
    self.Run('config set core/log_http True')
    self.ClearOutput()
    self.Run('config get-value core/account')
    self.AssertOutputEquals('foo\n')
    self.ClearOutput()
    self.Run('config get-value project')
    self.AssertOutputEquals('bar\n')
    self.ClearOutput()
    self.Run('config get-value /log_http')
    self.AssertErrNotContains('Your active configuration is')
    self.AssertOutputEquals('True\n')

  def testSessionCapture(self):
    capture_session_file = os.path.join(self.CreateTempDir(), 'session.yaml')
    properties.VALUES.core.capture_session_file.Set(capture_session_file)
    self.Run('config get-value core/project')
    self.AssertFileExists(capture_session_file)
    self.AssertFileContains('properties:\n', capture_session_file)
    properties.VALUES.core.capture_session_file.Set(None)
    session_capturer.SessionCapturer.capturer = None

  def testGetValueWithInvalidProperty(self):
    # Test Invalid Property
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Section \[core\] has no property \[log_htt\]\.'):
      self.Run('config get-value core/log_htt')

  def testGetValueWithUnsetProperty(self):
    # Test Get Unset Property
    self.Run('config unset account')
    self.Run('config get-value core/account')
    self.AssertOutputEquals('')
    self.AssertErrContains('(unset)')

  def testGetValueWithSection(self):
    # Test for Section with No Property
    with self.assertRaisesRegex(core_exceptions.Error,
                                'You cannot call get-value on a SECTION/. '
                                'Did you mean `gcloud config list SECTION`?'):
      self.Run('config get-value core/')

  def testGetValueWithMissingArgs(self):
    # Test for Missing Section and Property
    with self.AssertRaisesArgumentErrorMatches(
        'argument SECTION/PROPERTY: Must be specified.'):
      self.Run('config get-value')

  def testGetValueWithEmptyArgs(self):
    # Test for /
    with self.assertRaisesRegex(core_exceptions.Error,
                                'You cannot call get-value on a SECTION/.'
                                ' Did you mean `gcloud config list SECTION`?'):
      self.Run('config get-value /')

  def testGetValueWithInvalidSection(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Section "foobar" does not exist.'):
      self.Run('config get-value foobar/test')

  def testGetValueWithInvalidValue(self):
    # Test for Invalid Value in Config
    # Mock out VALUES.core.disable_color.Get() so that it errors if validated
    values_mock = self.StartObjectPatch(properties, 'VALUES')
    section_mock = mock.MagicMock()
    self.StartObjectPatch(values_mock, 'Section').return_value = section_mock
    property_mock = mock.MagicMock()
    self.StartObjectPatch(section_mock, 'Property').return_value = property_mock
    def get_effect(*unused_args, **kwargs):
      if kwargs['validate'] is False:
        return 'foo'
      else:
        raise properties.InvalidValueError('Invalid value error message')
    self.StartObjectPatch(property_mock, 'Get').side_effect = get_effect
    self.StartObjectPatch(values_mock.core.capture_session_file,
                          'Get').return_value = None

    self.Run('config get-value core/disable_color')
    self.AssertErrContains('Invalid value error message')
    self.AssertOutputContains('foo')

  def testListWithAccountFlag(self):
    self.assertEqual(
        self.Run('config list core/account')['core']['account'], None)
    self.assertEqual(
        self.Run('config list core/account --account a@b.com')['core'][
            'account'], 'a@b.com')

  def testList(self):
    self.Run('config set core/account foo')
    self.Run('config set core/project bar')
    result = self.Run('config list core/account')
    self.assertEqual(1, len(result))
    core = result['core']
    self.assertIn('account', core)
    self.assertNotIn('project', core)

    result = self.Run('config list account')
    self.assertEqual(1, len(result))
    core = result['core']
    self.assertIn('account', core)
    self.assertNotIn('project', core)

    result = self.Run('config list core/')
    self.assertEqual(1, len(result))
    core = result['core']
    self.assertIn('account', core)
    self.assertIn('project', core)

    result = self.Run('config list --all')
    self.assertGreater(len(result), 1)
    core = result['core']
    self.assertIn('account', core)
    self.assertIn('project', core)

    self.ClearErr()
    self.Run('config list --format=json')
    self.AssertErrNotContains('Your active configuration is')

  def testListDefaultsAndInternal(self):
    self.Run('config set metrics/command_name foo')
    result = self.Run('config list')
    self.assertGreater(len(result), 1)
    self.assertNotIn('command_name', result.get('metrics', {}))
    self.assertNotIn('pass_credentials_to_gsutil', result.get('core', {}))

  def testListShowConfiguration(self):
    self.Run('config list --configuration NONE')
    self.AssertErrContains('Your active configuration is: [NONE]')
    self.ClearErr()
    self.Run('config list --configuration foo')
    self.AssertErrContains('Your active configuration is: [foo]')

  def testPropertyAllExclusive(self):
    with self.assertRaisesRegex(
        core_exceptions.Error,
        'cannot take both a property name and the `--all` flag'):
      self.Run('config list core/foo --all')

  def testCompletion(self):
    for verb in ['set', 'unset']:
      # Complete properties without section.
      self.RunCompletion('config {0} acc'.format(verb), ['account'])
      self.RunCompletion(
          'config {0} dis'.format(verb),
          ['disable_color', 'disable_prompts', 'disable_usage_reporting'])

      # Complete both sections and properties.
      self.RunCompletion('config {0} a'.format(verb),
                         ['app/', 'auth/', 'account'])

      # Complete only sections.
      self.RunCompletion('config {0} co'.format(verb), [
          'component_manager/', 'composer/', 'compute/', 'container/', 'core/'
      ])

      # Complete properties under a section.
      self.RunCompletion('config {0} component_manager'.format(verb),
                         ['component_manager/'])
      self.RunCompletion('config {0} component_manager/'.format(verb),
                         ['component_manager/additional_repositories',
                          'component_manager/disable_update_check'])

  def testChoicesPropertyValueCompletion(self):
    self.RunCompletion('config set disable_usage_reporting ', ['true', 'false'])

  def testConfigSetActiveConfig(self):
    self.Run('config configurations create foo')
    self.Run('config set core/account badger')
    self.assertEqual(
        self.Run('config list core/account')['core']['account'], 'badger')

    # Switch to new config; old properties aren't visible...
    self.Run('config configurations create bar')
    self.assertEqual(
        self.Run('config list core/account')['core']['account'], None)

    # setting a new property works...
    self.Run('config set core/account mushroom')
    self.assertEqual(
        self.Run('config list core/account')['core']['account'], 'mushroom')

    # and the "foo" config is not affected, check with the flag and by proper
    # activation.
    self.assertEqual(
        self.Run('--configuration foo config list core/account')['core'][
            'account'], 'badger')
    self.Run('config configurations activate foo')
    self.assertEqual(
        self.Run('config list core/account')['core']['account'], 'badger')

  def testConfigSetFailNone(self):
    self.Run('config configurations activate NONE')
    with self.assertRaisesRegex(
        named_configs.ReadOnlyConfigurationError,
        r'Properties in configuration \[NONE\] cannot be set.'):
      self.Run('config set core/account badger')

  def testAutoUpgradeCommonCase(self):
    # Make sure there's a global user property to import
    if os.path.exists(config.Paths().named_config_activator_path):
      os.remove(config.Paths().named_config_activator_path)
    with open(os.path.join(self.global_config_path, 'properties'), 'w') as f:
      f.write('[container]\ncluster = my_cluster\n')

    self.assertEqual((), tuple(self.Run('config configurations list')))

    self.Run('config set core/account mushroom')
    self.Run('config set core/project portobello')
    self.Run('config set compute/zone tree')
    self.Run('config set compute/region forest')

    self.assertEqual(
        self.Run('config list core/account')['core']['account'], 'mushroom')

    self.Run('config configurations list')
    self.AssertOutputContains('default True mushroom portobello tree forest',
                              normalize_space=True)

    self.Run('config configurations describe default')
    self.AssertOutputContains('name: default')
    self.AssertOutputContains('is_active: true')
    self.AssertOutputContains('account: mushroom', normalize_space=True)
    self.AssertOutputContains('cluster: my_cluster', normalize_space=True)

    with open(os.path.join(self.global_config_path, 'properties')) as f:
      properties_contents = f.read()
      self.assertTrue(
          '# This properties file has been superseded' in properties_contents)
      self.assertFalse('mushroom' in properties_contents)

    # Make sure properties don't get imported again if we remove all configs.
    os.remove(config.Paths().named_config_activator_path)
    files.RmTree(config.Paths().named_config_directory)
    self.ClearOutput()
    self.Run('config set core/account mushroom')

    self.Run('config configurations describe default')
    self.AssertOutputContains('name: default')
    self.AssertOutputContains('is_active: true')
    self.AssertOutputContains('account: mushroom', normalize_space=True)
    self.AssertOutputNotContains('cluster: my_cluster', normalize_space=True)


if __name__ == '__main__':
  cli_test_base.main()
