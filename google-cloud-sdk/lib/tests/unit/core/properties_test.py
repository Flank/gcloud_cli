# Copyright 2013 Google Inc. All Rights Reserved.
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

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import parameterized_line_no
from tests.lib import sdk_test_base


T = parameterized_line_no.LineNo


def Prop(section, option, default=None, callbacks=None):
  return properties._Property(
      section, option, default=default, callbacks=callbacks)


def _EscapeBackslashes(s):
  return s.replace('\\', '\\\\')


class PropertiesTests(sdk_test_base.SdkBase):

  def testPropertiesHaveHelp(self):
    for section in properties.VALUES:
      if not section.is_hidden:
        for prop in section:
          if not prop.is_hidden:
            self.assertTrue(
                prop.help_text,
                'Public property [{0}/{1}] must have a help string.'.format(
                    prop.section, prop.name))

  def testGet(self):
    prop = properties.VALUES.core.account
    self.assertEqual(None, prop.Get())
    self.assertEqual(None, prop.GetBool())
    self.assertEqual(None, prop.GetInt())

    prop.Set('1')
    self.assertEqual('1', prop.Get())
    self.assertEqual(True, prop.GetBool())
    self.assertEqual(1, prop.GetInt())

    prop.Set('0')
    self.assertEqual('0', prop.Get())
    self.assertEqual(False, prop.GetBool())
    self.assertEqual(0, prop.GetInt())

    prop.Set('asdf')
    with self.assertRaises(properties.InvalidValueError):
      prop.GetInt()
    # Test that this value raises an error when validated as a boolean, but is
    # treated as False by default (if a user had already set an invalid value
    # before there was a validator).
    regex = (r'The \[account\] value \[asdf\] is not valid. '
             r'Possible values: \[true, 1, on, yes, y, false, 0, off, no, n, '
             r'\'\', none\]. \(See http://yaml.org/type/bool.html\)')
    with self.assertRaisesRegex(properties.InvalidValueError, regex):
      prop.GetBool()
    self.assertEqual(False, prop.GetBool(validate=False))

    prop.Set('YES')
    self.assertEqual(True, prop.GetBool(validate=True))

    prop.Set('y')
    self.assertEqual(True, prop.GetBool(validate=True))

    prop.Set('off')
    self.assertEqual(False, prop.GetBool(validate=True))

    prop.Set('true')
    self.assertEqual(True, prop.GetBool(validate=True))

    prop.Set('FALSE')
    self.assertEqual(False, prop.GetBool(validate=True))

    prop.Set('no')
    self.assertEqual(False, prop.GetBool(validate=True))

    prop.Set('N')
    self.assertEqual(False, prop.GetBool(validate=True))

    prop.Set('')
    self.assertEqual(False, prop.GetBool(validate=True))

    prop.Set('ON')
    self.assertEqual(True, prop.GetBool(validate=True))

    prop.Set('NONE')
    self.assertEqual(None, prop.GetBool(validate=True))

    prop.Set(None)
    self.assertEqual(None, prop.GetBool(validate=True))

    # Make sure defaults work.
    self.assertEqual(
        True, properties.VALUES.core.pass_credentials_to_gsutil.GetBool())
    properties.VALUES.core.pass_credentials_to_gsutil.Set(False)
    self.assertEqual(
        False, properties.VALUES.core.pass_credentials_to_gsutil.GetBool())
    self.assertEqual(
        True, properties.VALUES.core.pass_credentials_to_gsutil.default)
    temp_prop = properties._Property('temp_section', 'temp_prop',
                                     default='asdf')
    regex = (r'The \[temp_prop\] value \[asdf\] is not valid. '
             r'Possible values: \[true, 1, on, yes, y, false, 0, off, no, n, '
             r'\'\', none\]. \(See http://yaml.org/type/bool.html\)')
    with self.assertRaisesRegex(properties.InvalidValueError, regex):
      temp_prop.GetBool()
    self.assertEqual(False, temp_prop.GetBool(validate=False))

  def testIsExplicitlySet(self):
    prop = Prop('foo', 'bar', default='1')
    self.assertEqual('1', prop.Get())
    self.assertFalse(prop.IsExplicitlySet())
    prop.Set('2')
    self.assertEqual('2', prop.Get())
    self.assertTrue(prop.IsExplicitlySet())

    prop = Prop('foo', 'baz', callbacks=[lambda: '1'])
    self.assertEqual('1', prop.Get())
    self.assertFalse(prop.IsExplicitlySet())
    prop.Set('2')
    self.assertEqual('2', prop.Get())
    self.assertTrue(prop.IsExplicitlySet())

  def testCoreBooleanPropertyGetRequired(self):
    prop = properties.VALUES.core.log_http
    self.assertEqual('False', prop.Get(required=True))

  def testCoreBooleanPropertyGetBoolRequired(self):
    prop = properties.VALUES.core.log_http
    self.assertEqual(False, prop.GetBool(required=True))

  def testCoreBooleanPropertyGetIntRequired(self):
    regex = (r'The property \[core.log_http\] must have an integer value: '
             r'\[False\]')
    prop = properties.VALUES.core.log_http
    with self.assertRaisesRegex(properties.InvalidValueError, regex):
      prop.GetInt(required=True)

  def testNonCoreBooleanPropertyGetRequired(self):
    regex = (r'(?s)The required property \[snapshot_url\] is not currently set'
             r'\..*\$ gcloud config set component_manager/snapshot_url VALUE'
             r'.*or it can be set temporarily by the environment variable '
             r'\[CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL\]$')
    prop = properties.VALUES.component_manager.snapshot_url
    with self.assertRaisesRegex(properties.RequiredPropertyError, regex):
      prop.Get(required=True)

  def testNonCoreBooleanPropertyGetBoolRequired(self):
    regex = (r'(?s)The required property \[snapshot_url\] is not currently set'
             r'\..*\$ gcloud config set component_manager/snapshot_url VALUE'
             r'.*or it can be set temporarily by the environment variable '
             r'\[CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL\]$')
    prop = properties.VALUES.component_manager.snapshot_url
    with self.assertRaisesRegex(properties.RequiredPropertyError, regex):
      prop.GetBool(required=True)

  def testNonCoreBooleanPropertyGetIntRequired(self):
    regex = (r'(?s)The required property \[snapshot_url\] is not currently set'
             r'\..*\$ gcloud config set component_manager/snapshot_url VALUE'
             r'.*or it can be set temporarily by the environment variable '
             r'\[CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL\]$')
    prop = properties.VALUES.component_manager.snapshot_url
    with self.assertRaisesRegex(properties.RequiredPropertyError, regex):
      prop.GetInt(required=True)

  def testHiddenBooleanPropertyGetRequired(self):
    prop = properties.VALUES.app.promote_by_default
    self.assertEqual('True', prop.Get(required=True))

  def testHiddenBooleanPropertyGetBoolRequired(self):
    prop = properties.VALUES.app.promote_by_default
    self.assertEqual(True, prop.GetBool(required=True))

  def testHiddenBooleanPropertyGetIntRequired(self):
    regex = (r'The property \[app.promote_by_default\] must have an integer '
             r'value: \[True\]')
    prop = properties.VALUES.app.promote_by_default
    with self.assertRaisesRegex(properties.InvalidValueError, regex):
      prop.GetInt(required=True)

  def testHiddenSections(self):
    sections = properties.VALUES.AllSections(include_hidden=True)
    self.assertIn('experimental', sections)
    sections = properties.VALUES.AllSections(include_hidden=False)
    self.assertNotIn('experimental', sections)

    # Property should be hidden because it is in a hidden section, even though
    # the property is not explicitly marked as hidden.
    self.assertTrue(
        properties.VALUES.experimental.fast_component_update.is_hidden)

  def testAllValues(self):
    all_values = properties.VALUES.AllValues()
    self.assertTrue('account' not in all_values['core'])

    properties.VALUES.core.account.Set('asdf')
    self.assertEqual('asdf', properties.VALUES.AllValues()['core']['account'])
    all_values = properties.VALUES.AllValues(list_unset=True)
    self.assertTrue(len(all_values) > 1)
    self.assertTrue(len(all_values['core']) > 2)

  def testAllValuesHidden(self):
    all_values = properties.VALUES.AllValues()
    self.assertTrue('account' not in all_values['core'])
    self.assertTrue('snapshot_url' not in all_values['component_manager'])

    all_values = properties.VALUES.AllValues(list_unset=True)
    self.assertTrue('account' in all_values['core'])
    self.assertTrue('snapshot_url' not in all_values['component_manager'])

    properties.VALUES.core.account.Set('asdf')
    all_values = properties.VALUES.AllValues()
    self.assertTrue('account' in all_values['core'])
    self.assertTrue('snapshot_url' not in all_values['component_manager'])

    all_values = properties.VALUES.AllValues(list_unset=True)
    self.assertTrue('account' in all_values['core'])
    self.assertTrue('snapshot_url' not in all_values['component_manager'])

    all_values = properties.VALUES.AllValues(list_unset=True,
                                             include_hidden=True)
    self.assertTrue('account' in all_values['core'])
    self.assertTrue('snapshot_url' in all_values['component_manager'])

    properties.VALUES.component_manager.snapshot_url.Set('asdf')
    all_values = properties.VALUES.AllValues()
    self.assertTrue('account' in all_values['core'])
    self.assertTrue('snapshot_url' in all_values['component_manager'])

  def testAllNames(self):
    all_names = properties.VALUES.component_manager.AllProperties()
    self.assertTrue('disable_update_check' in all_names)
    self.assertTrue('snapshot_url' not in all_names)

    all_names = properties.VALUES.component_manager.AllProperties(
        include_hidden=True)
    self.assertTrue('disable_update_check' in all_names)
    self.assertTrue('snapshot_url' in all_names)

  def testArgs(self):
    self.assertEqual(properties.VALUES.core.project.Get(), None)
    properties.VALUES.PushInvocationValues()
    properties.VALUES.SetInvocationValue(
        properties.VALUES.core.project, 'x1', '--project')
    self.assertEqual(properties.VALUES.core.project.Get(), 'x1')
    properties.VALUES.PushInvocationValues()
    properties.VALUES.SetInvocationValue(
        properties.VALUES.core.project, 'x2', '--project')
    self.assertEqual(properties.VALUES.core.project.Get(), 'x2')
    properties.VALUES.PopInvocationValues()
    self.assertEqual(properties.VALUES.core.project.Get(), 'x1')
    properties.VALUES.PopInvocationValues()
    self.assertEqual(properties.VALUES.core.project.Get(), None)

  def testAddRemoveCallback(self):
    self.assertIsNone(properties.VALUES.core.project.Get())
    def GetProject():
      return 'magic-project'
    properties.VALUES.core.project.AddCallback(GetProject)
    self.assertEqual('magic-project', properties.VALUES.core.project.Get())
    properties.VALUES.core.project.RemoveCallback(GetProject)
    self.assertIsNone(properties.VALUES.core.project.Get())


class PropertyFileTests(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.named_config_activator = os.path.join(self.global_config_path,
                                               'active_config')
    self.named_config_dir = os.path.join(self.global_config_path,
                                         'configurations')
    named_configs.ActivePropertiesFile.Invalidate()

  def testMasterProperties(self):
    prop = properties.VALUES.core.project
    self.assertEqual(prop.section, 'core')
    self.assertEqual(prop.name, 'project')
    self.assertEqual(properties.VALUES.Section('core').Property('project'),
                     prop)
    with self.assertRaises(properties.NoSuchPropertyError):
      properties.VALUES.Section('no-section')
    with self.assertRaises(properties.NoSuchPropertyError):
      properties.VALUES.Section('core').Property('no-property')

  def testPersistProperty_UsesNamedConfiguration(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)

    # Remove all configurations.
    if os.path.exists(self.named_config_dir):
      files.RmTree(self.named_config_dir)
    if os.path.exists(self.named_config_activator):
      os.remove(self.named_config_activator)

    prop = Prop('foo', 'bar')
    properties.PersistProperty(prop, 'magic_value')

    # Now after persist we are upgraded to use named configuration.
    self.assertEqual('default',
                     named_configs.ConfigurationStore.ActiveConfig().name)

  def testPersistScopes(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)

    prop = Prop('foo', 'bar')

    self.CheckProperty(prop, properties.Scope.USER)
    self.CheckProperty(prop, properties.Scope.INSTALLATION)
    self.assertFalse(os.path.isfile(config.Paths().config_sentinel_file))

    properties.PersistProperty(prop, '2', properties.Scope.USER)
    self.CheckProperty(prop, properties.Scope.USER, value='2')
    self.CheckProperty(prop, properties.Scope.INSTALLATION)
    self.assertEqual(prop.Get(), '2')
    self.assertTrue(os.path.isfile(config.Paths().config_sentinel_file))
    os.remove(config.Paths().config_sentinel_file)
    self.assertFalse(os.path.isfile(config.Paths().config_sentinel_file))

    properties.PersistProperty(prop, '3', properties.Scope.INSTALLATION)
    self.CheckProperty(prop, properties.Scope.USER, value='2')
    self.CheckProperty(prop, properties.Scope.INSTALLATION, value='3')
    self.assertEqual(prop.Get(), '2')
    self.assertTrue(os.path.isfile(config.Paths().config_sentinel_file))

    if not self.IsOnWindows():
      # Apparently readonly does not work how you would expect on Windows.
      # There does not seem to be an easy way to make a directory non-writable
      # from Python.
      try:
        os.chmod(self.temp_path, 0o400)
        with self.assertRaisesRegex(
            exceptions.RequiresAdminRightsError,
            'you do not have permission to modify the Google Cloud SDK '
            'installation directory'):
          properties.PersistProperty(prop, '4', properties.Scope.INSTALLATION)
      finally:
        os.chmod(self.temp_path, 0o755)

    properties.PersistProperty(prop, '4')
    self.CheckProperty(prop, properties.Scope.USER, value='4')
    self.CheckProperty(prop, properties.Scope.INSTALLATION, value='3')
    self.assertEqual(prop.Get(), '4')

    properties.PersistProperty(prop, None)
    self.CheckProperty(prop, properties.Scope.USER)
    self.CheckProperty(prop, properties.Scope.INSTALLATION, value='3')
    self.assertEqual(prop.Get(), '3')

  def CheckProperty(self, prop, scope, value=None):
    prop_file = (named_configs.ConfigurationStore.ActiveConfig().file_path
                 if scope == properties.Scope.USER
                 else config.Paths().installation_properties_path)
    props = properties_file.PropertiesFile([prop_file])
    set_value = props.Get(prop.section, prop.name)
    self.assertEqual(set_value, value)

  def testPersistErrors(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=None)
    prop = Prop('foo', 'bar')
    with self.assertRaises(properties.MissingInstallationConfig):
      properties.PersistProperty(prop, '1',
                                 scope=properties.Scope.INSTALLATION)


class PropertyEnvironmentTests(sdk_test_base.WithOutputCapture):

  def testEnvironmentProperty(self):
    properties.PersistProperty(properties.VALUES.core.project, 'myproject')
    self.assertEqual(properties.VALUES.core.project.Get(), 'myproject')
    properties.VALUES.core.project.Set('newproject')
    self.assertEqual(properties.VALUES.core.project.Get(), 'newproject')
    properties.VALUES.core.project.Set(None)
    self.assertEqual(properties.VALUES.core.project.Get(), 'myproject')
    self.AssertErrNotContains('WARNING:')

    properties.PersistProperty(
        properties.VALUES.component_manager.disable_update_check, True)
    self.assertEqual(
        properties.VALUES.component_manager.disable_update_check.GetBool(),
        True)
    properties.VALUES.component_manager.disable_update_check.Set(False)
    self.assertEqual(
        properties.VALUES.component_manager.disable_update_check.GetBool(),
        False)

  def testEnvironmentPropertyOverride(self):
    self.StartEnvPatch({'CLOUDSDK_CORE_DISABLE_PROMPTS': 'True'})
    properties.PersistProperty(properties.VALUES.core.disable_prompts, 'False')
    self.AssertErrContains('WARNING: Property [disable_prompts]')


class PropertyValidatorTests(sdk_test_base.SdkBase, parameterized.TestCase):

  @parameterized.named_parameters(
      T('valid-project'),
      T('valid-123'),
      T('google.com:valid-123'),
      T('123valid-project'),
  )
  def testValidProject(self, project_id):
    properties.PersistProperty(properties.VALUES.core.project, project_id)

  @parameterized.named_parameters(
      T(properties.InvalidValueError, r'must be a string', 1),
      T(properties.InvalidProjectError, r'empty string', ''),
      T(properties.InvalidProjectError, r'project number \[666\]', '666'),
      T(properties.InvalidProjectError, r'project name \[I am text.\]',
        'I am text.'),
  )
  def testInvalidProject(self, exception, message, project_id):
    with self.assertRaisesRegex(exception, message):
      properties.PersistProperty(properties.VALUES.core.project, project_id)

  def testValidEndpointOverride(self):
    properties.PersistProperty(
        properties.VALUES.api_endpoint_overrides.compute,
        'http://localhost:8787/v1beta1/')
    properties.PersistProperty(
        properties.VALUES.api_endpoint_overrides.compute,
        'https://test-endpoint.sandbox.googleapis.com/')

  def testInvalidEndpointOverride(self):
    invalid_urls = [
        'http://no-trailing-slash.com',
        'naked-domain.com/v1/'
        'https://',  # empty url
    ]
    for url in invalid_urls:
      with self.assertRaisesRegex(
          properties.InvalidValueError,
          r'The endpoint_overrides property must be an absolute URI beginning '
          r"with http:// or https:// and ending with a trailing '/'. "
          r'\[' + url + r'\] is not a valid endpoint override.'):
        properties.PersistProperty(
            properties.VALUES.api_endpoint_overrides.compute,
            url)

  def testValidBool(self):
    # Check that values expected to be valid don't throw an InvalidValueError
    properties.PersistProperty(properties.VALUES.core.disable_prompts, True)
    properties.PersistProperty(properties.VALUES.core.disable_prompts, 'on')
    properties.PersistProperty(properties.VALUES.core.disable_prompts, 0)
    properties.PersistProperty(properties.VALUES.core.disable_prompts, 'no')
    properties.PersistProperty(properties.VALUES.core.disable_prompts, 'FALSE')

  def testInvalidBool(self):
    regex = (r'The \[disable_prompts\] value \[str\] is not valid. '
             r'Possible values: \[true, 1, on, yes, y, false, 0, off, no, n, '
             r'\'\', none\]. \(See http://yaml.org/type/bool.html\)')
    with self.assertRaisesRegex(properties.InvalidValueError, regex):
      properties.PersistProperty(properties.VALUES.core.disable_prompts, 'str')

  def testBadTimeouts(self):
    """Test properties.CloudBuildTimeoutValidator."""
    dur_regexp = (r'could not convert string to float')
    with self.assertRaisesRegex(times.DurationSyntaxError, dur_regexp):
      properties.VALUES.app.cloud_build_timeout.Set('x1123')

  def testGoodTimeouts(self):
    properties.VALUES.app.cloud_build_timeout.Set('123')
    properties.VALUES.app.cloud_build_timeout.Set('1m23s')


class PropertiesParseTests(sdk_test_base.SdkBase):

  def testParse(self):
    self.assertEqual(properties.VALUES.core.account,
                     properties.FromString('account'))
    self.assertEqual(properties.VALUES.core.account,
                     properties.FromString('core/account'))
    self.assertEqual(None,
                     properties.FromString(''))

    with self.assertRaises(properties.NoSuchPropertyError):
      properties.FromString('asdf')


if __name__ == '__main__':
  sdk_test_base.main()
