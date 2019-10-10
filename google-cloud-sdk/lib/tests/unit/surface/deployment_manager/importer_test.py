# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Basic unit tests for the Importer library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from apitools.base.py.testing import mock as gcloud_mock

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.deployment_manager import importer
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
import mock
import requests
import six

messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')

ERROR_403 = '{"error": "forbidden"}'
ERROR_404 = '{"error": "not found"}'
_TEST_DATA_DIR = ['tests', 'lib', 'surface', 'deployment_manager', 'test_data']


class MockResponse(object):

  def __init__(self, text, status):
    self.text = text
    self.status = status

  def raise_for_status(self):
    if self.status != 200:
      raise requests.exceptions.HTTPError(self.text)


def build_mock_file(content, path='/foo.yaml'):
  mock_obj = importer._ImportFile(path)
  mock_obj.GetContent = mock.MagicMock(return_value=content)
  return mock_obj


class ImporterTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Tests basic functionality of the DmV2Importer library."""

  def SetUp(self):
    self.mocked_client = gcloud_mock.Client(
        core_apis.GetClientClass('deploymentmanager', 'v2'),
        real_client=core_apis.GetClientInstance('deploymentmanager', 'v2',
                                                no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.context = {
        'deploymentmanager-client': self.mocked_client,
        'deploymentmanager-messages': messages,
    }

  def GetTestData(self, *path):
    return self.Resource(*(_TEST_DATA_DIR + list(path)))

  def LoadNamedImportFiles(self, imports_name_path_map):
    import_contents = {}
    for name, path in six.iteritems(imports_name_path_map):
      full_import_path = self.GetTestData('simple_configs', path)
      with open(full_import_path, 'r') as import_file:
        import_contents[name] = import_file.read()
    return import_contents

  def testWindowsPathSanitizer(self):
    self.assertEqual(['foo/bar', 'fizz/buzz'],
                     importer._SanitizeWindowsPathsGlobs(
                         ['foo/bar', 'fizz/buzz'], native_separator='\\'))
    self.assertEqual(['foo/bar/fizz/buzz'],
                     importer._SanitizeWindowsPathsGlobs(
                         ['foo/bar\\fizz\\buzz'], native_separator='\\'))
    self.assertEqual(['C:\\foo\\bar\\fizz\\buzz'],
                     importer._SanitizeWindowsPathsGlobs(
                         ['C:\\foo\\bar\\fizz\\buzz'], native_separator='\\'))

  def testBuildTargetConfig_EmptyPath(self):
    try:
      importer.BuildTargetConfig(messages, config='')
      self.fail('Expected exception.')
    except exceptions.ConfigError as e:
      self.assertTrue('No path or name for a config, template, or '
                      'composite type was specified.' in str(e))

  def testBuildTargetConfig_Yaml_WrongFlag_Template(self):
    try:
      config_name = self.GetTestData('single_vm', 'vm.yaml')
      importer.BuildTargetConfig(messages, template=config_name)
      self.fail('Expected exception.')
    except exceptions.ArgumentError as e:
      self.assertTrue('The --template flag should only be used '
                      'when using a template as your config file.' in str(e))

  def testBuildTargetConfig_Yaml_WrongFlag_CompositeType(self):
    try:
      config_name = self.GetTestData('single_vm', 'vm.yaml')
      importer.BuildTargetConfig(messages, composite_type=config_name)
      self.fail('Expected exception.')
    except exceptions.ConfigError as e:
      self.assertTrue('Invalid composite type syntax.' in str(e))

  def testBuildTargetConfig_Jinja_WrongFlag_Config(self):
    config_name = self.GetTestData('single_vm', 'vm_template.jinja')

    dict_props = {'zone': 'ZONE_TO_RUN'}

    with self.assertRaisesRegex(exceptions.ArgumentError, r'--template'):
      importer.BuildTargetConfig(messages,
                                 config=config_name,
                                 properties=dict_props)

  def testBuildTargetConfig_SingleVmYaml(self):
    config_name = self.GetTestData('single_vm', 'vm.yaml')

    full_import_path = self.GetTestData('single_vm', 'vm_template.jinja')
    with open(full_import_path, 'r') as import_file:
      import_content = import_file.read()

    with open(config_name, 'r') as config_file:
      config_content = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[
            messages.ImportFile(
                name='vm_template.jinja',
                content=import_content
            )
        ]
    )

    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports,
                     'missing expected import vm_template.jinja')

  def testBuildTargetConfig_SingleVmJinja(self):
    config_name = self.GetTestData('single_vm', 'vm_template.jinja')

    with open(config_name, 'r') as config_file:
      config_content = config_file.read()

    dict_props = {'zone': 'ZONE_TO_RUN'}

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      template=config_name,
                                                      properties=dict_props)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[
            messages.ImportFile(
                name='vm_template.jinja',
                content=config_content
            )
        ]
    )

    yaml_config = yaml.load(actual_target_config.config.content)

    expected_config = {'imports': [{'path': 'vm_template.jinja'}],
                       'resources': [{'name': 'vm-template-jinja',
                                      'type': 'vm_template.jinja',
                                      'properties': {'zone': 'ZONE_TO_RUN'}}]}

    self.assertEqual(expected_config, yaml_config)

    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports,
                     'missing expected import vm_template.jinja')

  def testBuildTargetConfig_SingleVmJinjaWithOutputsInSchema(self):
    config_name = self.GetTestData('single_vm', 'with_output.jinja')
    schema_name = self.GetTestData('single_vm', 'with_output.jinja.schema')

    with open(config_name, 'r') as config_file:
      config_content = config_file.read()
    with open(schema_name, 'r') as schema_file:
      schema_content = schema_file.read()

    dict_props = {'zone': 'ZONE_TO_RUN'}

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      template=config_name,
                                                      properties=dict_props)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[
            messages.ImportFile(
                name='with_output.jinja', content=config_content),
            messages.ImportFile(
                name='with_output.jinja.schema', content=schema_content)
        ])

    yaml_config = yaml.load(actual_target_config.config.content)

    expected_config = {'imports': [{'path': 'with_output.jinja'}],
                       'resources': [{'name': 'with-output-jinja',
                                      'type': 'with_output.jinja',
                                      'properties': {'zone': 'ZONE_TO_RUN'}}],
                       'outputs': [
                           {'name': 'databaseIp',
                            'value': '$(ref.with-output-jinja.databaseIp)'},
                       ]}

    self.assertEqual(expected_config, yaml_config)

    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports,
                     'missing expected import with_output.jinja')

  @mock.patch('requests.get')
  def testBuildTargetConfig_SingleVmJinjaUrl(self, mock_request):
    config_name = self.GetTestData('single_vm', 'vm_template.jinja')

    with open(config_name, 'r') as config_file:
      config_content = config_file.read()

    config_url = 'https://www.google.com/examples/vm_template.jinja'
    schema_url = config_url + '.schema'
    mock_responses = {config_url: MockResponse(config_content, 200),
                      schema_url: MockResponse(ERROR_404, 404)}

    mock_request.side_effect = lambda url: mock_responses[url]

    dict_props = {'zone': 'ZONE_TO_RUN'}

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      template=config_url,
                                                      properties=dict_props)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[
            messages.ImportFile(
                name='vm_template.jinja',
                content=config_content
            )
        ]
    )

    yaml_config = yaml.load(actual_target_config.config.content)

    expected_config = {'imports': [{'path': 'vm_template.jinja'}],
                       'resources': [{'name': 'vm-template-jinja',
                                      'type': 'vm_template.jinja',
                                      'properties': {'zone': 'ZONE_TO_RUN'}}]}

    self.assertEqual(expected_config, yaml_config)

    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports,
                     'missing expected import vm_template.jinja')

    self.assertEqual(3, mock_request.call_count)
    mock_request.assert_any_call(config_url)
    mock_request.assert_any_call(schema_url)

  @mock.patch('requests.get')
  def testBuildTargetConfig_SingleVmJinjaUrl_EmptySchema(self, mock_request):
    config_name = self.GetTestData('single_vm', 'vm_template.jinja')

    with open(config_name, 'r') as config_file:
      config_content = config_file.read()

    config_url = 'https://www.google.com/examples/vm_template.jinja'
    schema_url = config_url + '.schema'

    mock_responses = {config_url: MockResponse(config_content, 200),
                      schema_url: MockResponse('', 200)}

    mock_request.side_effect = lambda url: mock_responses[url]

    dict_props = {'zone': 'ZONE_TO_RUN'}

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      template=config_url,
                                                      properties=dict_props)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[
            messages.ImportFile(
                name='vm_template.jinja',
                content=config_content
            ),
            messages.ImportFile(
                name='vm_template.jinja.schema',
                content=''
            ),
        ]
    )

    yaml_config = yaml.load(actual_target_config.config.content)

    expected_config = {'imports': [{'path': 'vm_template.jinja'}],
                       'resources': [{'name': 'vm-template-jinja',
                                      'type': 'vm_template.jinja',
                                      'properties': {'zone': 'ZONE_TO_RUN'}}]}

    self.assertEqual(expected_config, yaml_config)

    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports,
                     'missing expected import vm_template.jinja')

    self.assertEqual(3, mock_request.call_count)
    mock_request.assert_any_call(config_url)
    mock_request.assert_any_call(schema_url)

  def testBuildTargetConfig(self):
    config_name = self.GetTestData('simple_configs', 'simple_with_import.yaml')
    imports = {}
    for import_path in ['simple.yaml', 'simple_bad_imports.yaml']:
      full_import_path = self.GetTestData('simple_configs',
                                          import_path)
      with open(full_import_path, 'r') as import_file:
        imports[import_path] = import_file.read()
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_WithNamedImports(self):
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_named_imports.yaml')
    imports = {}
    import_name_map = {'my-import-one.yaml': 'simple.yaml',
                       'my-import-two.yaml': 'simple_bad_imports.yaml'}
    for import_rename in import_name_map:
      full_import_path = self.GetTestData('simple_configs',
                                          import_name_map[import_rename])
      with open(full_import_path, 'r') as import_file:
        imports[import_rename] = import_file.read()
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_IdenticalImports(self):
    config_name = self.GetTestData('simple_configs',
                                   'identical_duplicate_imports.yaml')
    import_name_map = {'helper.jinja': 'helper.jinja'}

    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_SharedHelperImport(self):
    config_name = self.GetTestData('simple_configs',
                                   'shared_helper.yaml')
    import_name_map = {'shared_helper.jinja': 'shared_helper.jinja',
                       'shared_helper.jinja.schema':
                           'shared_helper.jinja.schema',
                       'subhelper.jinja': 'subhelper.jinja',
                       'shared.jinja': 'sub_directory/shared.jinja',
                       'shared.jinja.schema':
                       'sub_directory/shared.jinja.schema'}

    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_WithDuplicateImports(self):
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_duplicate_imports.yaml')

    try:
      importer.BuildTargetConfig(messages, config=config_name)
      self.fail('Importing duplicate files.')
    except exceptions.ConfigError as e:
      self.assertTrue('both being imported' in str(e))
      self.assertTrue('my-import' in str(e))

  def testBuildTargetConfig_ConfigAndProperties(self):
    config_name = self.GetTestData('simple_configs', 'simple.yaml')
    config_properties = {'a': 'b'}

    try:
      importer.BuildTargetConfig(messages, config=config_name,
                                 properties=config_properties)
      self.fail('Passing properties to yaml file.')
    except exceptions.Error as e:
      self.assertTrue('properties flag' in str(e))
      self.assertTrue('when using a template' in str(e))

  def testBuildTargetConfig_WithSimpleSchema(self):
    config_name = self.GetTestData('simple_configs', 'simple_with_schema.yaml')
    imports = {}
    for import_path in ['simple.jinja', 'simple.jinja.schema', 'helper.jinja']:
      full_import_path = self.GetTestData('simple_configs',
                                          import_path)
      with open(full_import_path, 'r') as import_file:
        imports[import_path] = import_file.read()
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_WithNamedNestedSchemas(self):
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_subtemplate.yaml')
    import_name_map = {'simple_with_subtemplate.jinja':
                           'simple_with_subtemplate.jinja',
                       'simple_with_subtemplate.jinja.schema':
                           'simple_with_subtemplate.jinja.schema',
                       'simple.jinja': 'simple.jinja',
                       'helper.jinja': 'helper.jinja',
                       'simple.jinja.schema': 'simple.jinja.schema',
                       'sub_simple.jinja':
                           os.path.join('sub_directory', 'simple.jinja'),
                       'sub_simple.jinja.schema':
                           os.path.join('sub_directory', 'simple.jinja.schema'),
                       'sub_helper.jinja':
                           os.path.join('sub_directory', 'helper.jinja'),}
    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(
        messages, config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(name=import_item[0], content=import_item[1])
            for import_item in imports.items()
        ])
    self.assertEqual(expected_target_config.config, actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_ImportGlobMatchesMultipleFiles(self):
    properties.VALUES.deployment_manager.glob_imports.Set(True)
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_glob_import.yaml')
    one = os.path.join('glob_directory', 'import_one.jinja')
    two = os.path.join('glob_directory', 'import_two.jinja')
    import_name_map = {one: one, two: two}
    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    # Switch to working with a file in the immediate working directory to test
    # no-parent-directory edge case
    parent_dir, config_name = os.path.split(config_name)
    with files.ChDir(parent_dir):
      actual_target_config = importer.BuildTargetConfig(
          messages, config=config_name)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(name=import_item[0], content=import_item[1])
            for import_item in imports.items()
        ])
    self.assertEqual(expected_target_config.config, actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_GlobbingDisabledDoesntMatch(self):
    """Expect failure for * path with globbig disabled and no file named *."""
    properties.VALUES.deployment_manager.glob_imports.Set(False)
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_glob_import.yaml')
    with self.assertRaisesRegex(exceptions.ConfigError, r'Unable to read file'
                                r'.*\*\.jinja'):
      importer.BuildTargetConfig(messages, config=config_name)

  def testBuildTargetConfig_ImportGlobWithSchema(self):
    properties.VALUES.deployment_manager.glob_imports.Set(True)
    config_name = self.GetTestData(
        'simple_configs', 'simple_with_glob_import_multiple_levels.yaml')
    three = os.path.join('glob_directory', 'deeper_dir', 'import_three.jinja')
    three_schema = os.path.join('glob_directory', 'deeper_dir',
                                'import_three.jinja.schema')
    import_name_map = {
        three: three,
        three_schema: three_schema,
        'emptytemplate': 'subhelper.jinja'
    }
    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_ImportGlobWorksWithInlineParentPath(self):
    properties.VALUES.deployment_manager.glob_imports.Set(True)
    config_name = self.GetTestData(
        'simple_configs', 'simple_with_glob_import_with_parent_dir.yaml')
    one = '../simple_configs/glob_directory/import_one.jinja'
    two = '../simple_configs/glob_directory/import_two.jinja'
    import_name_map = {one: one, two: two}
    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(
        messages, config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(name=import_item[0], content=import_item[1])
            for import_item in imports.items()
        ])
    self.assertEqual(expected_target_config.config, actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

  def testBuildTargetConfig_CompositeType_NoProps(self):
    config_name = 'example-project-name/composite:example-composite-type-name'
    config_content = ('resources:\n'
                      '- name: example-composite-type-name\n'
                      '  type: example-project-name/composite:'
                      'example-composite-type-name\n')

    actual_target_config = importer.BuildTargetConfig(
        messages, composite_type=config_name)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[]
    )

    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports)

  def testBuildTargetConfig_CompositeType_WithProps(self):
    config_name = 'example-project-name/composite:example-composite-type-name'
    config_content = ('resources:\n'
                      '- name: example-composite-type-name\n'
                      '  properties:\n'
                      '    zone: ZONE_TO_RUN\n'
                      '  type: example-project-name/composite:'
                      'example-composite-type-name\n')
    dict_props = {'zone': 'ZONE_TO_RUN'}

    actual_target_config = importer.BuildTargetConfig(
        messages, composite_type=config_name, properties=dict_props)

    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_content),
        imports=[]
    )

    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(expected_target_config.imports,
                     actual_target_config.imports)

  def testBuildTargetConfigFromManifest_GetHttpError(self):
    project_name = 'project-name'
    deployment_name = 'deployment-name'
    manifest_name = 'manifest-name'
    not_found_message = 'Requested manifest %s not found' % manifest_name
    self.mocked_client.manifests.Get.Expect(
        request=messages.DeploymentmanagerManifestsGetRequest(
            project=project_name,
            deployment=deployment_name,
            manifest=manifest_name,
        ),
        exception=http_error.MakeHttpError(
            404,
            not_found_message,
            url='FakeUrl')
    )
    with self.AssertRaisesHttpExceptionMatches(not_found_message):
      importer.BuildTargetConfigFromManifest(
          self.mocked_client, messages, project_name, deployment_name,
          manifest_name)

  def testHandleTemplateImporter_NoSchema(self):
    import_objects = importer._HandleTemplateImport(
        build_mock_file('', 'no-file.py'))
    self.assertEqual(import_objects, [])

  def testHandleTemplate_EmptySchema(self):
    # empty.py.schema is an empty file
    path = self.GetTestData('simple_configs', 'empty.py')
    import_objects = importer._HandleTemplateImport(build_mock_file('', path))

    schema_path = self.GetTestData('simple_configs', 'empty.py.schema')

    self.assertEqual(len(import_objects), 1)
    self.assertEqual(import_objects[0].GetFullPath(), schema_path)

  def testHandleTemplate_SimpleSchema(self):
    # simple.jinja.schema is an empty file
    path = self.GetTestData('simple_configs', 'simple.jinja')
    import_objects = importer._HandleTemplateImport(build_mock_file('', path))

    schema_path = self.GetTestData('simple_configs', 'simple.jinja.schema')

    import_path = self.GetTestData('simple_configs', 'helper.jinja')

    expected_paths = [schema_path, import_path]

    self.assertEqual(len(import_objects), 2)
    for import_object in import_objects:
      self.assertIn(import_object.GetFullPath(), expected_paths)

  def testImportFile(self):
    config_name = 'simple.yaml'
    config_path = self.GetTestData('simple_configs', config_name)

    obj = importer._BuildFileImportObject(config_path, name=config_name)

    self.assertEqual(config_name, obj.GetName())

    other_path = self.GetTestData('simple_configs', 'empty.yaml')

    self.assertEqual(other_path, obj.BuildChildPath('empty.yaml'))

  def testImportFileChildPath(self):
    config_path = self.GetTestData('saltstack', 'salt_cluster.yaml')

    obj = importer._BuildImportObject(config=config_path)

    child_path = self.GetTestData('saltstack', 'salt_cluster.jinja')
    self.assertEqual(child_path, obj.BuildChildPath('salt_cluster.jinja'))

    deep_child_path = self.GetTestData('saltstack', 'states', 'index.html')
    deep_child_name = os.path.join('states', 'index.html')
    self.assertEqual(deep_child_path, obj.BuildChildPath(deep_child_name))

  def testImportsMissingPath(self):
    content = """
      imports:
      - name: simple.yaml
      """

    try:
      importer._GetYamlImports(build_mock_file(content))
      self.fail()
    except exceptions.ConfigError as e:
      self.assertTrue('Missing required field' in str(e))

  def testGetYamlImports_InvalidYaml(self):
    content = """
      resources:
        dictionary: is it?
        - list
      """
    with self.assertRaisesRegex(yaml.Error, r'Failed to parse YAML'):
      importer._GetYamlImports(build_mock_file(content))

  def testGetYamlImports(self):
    content = """
      imports:
      - path: a.yaml
      - path: b.yaml
        name: c.yaml
      """

    yaml_imports = importer._GetYamlImports(build_mock_file(content))
    imports = [{'path': 'a.yaml', 'name': 'a.yaml'},
               {'path': 'b.yaml', 'name': 'c.yaml'}]

    self.assertEqual(imports, yaml_imports)

  def testBuildConfig(self):
    path = os.path.join('foo', 'bar.py')
    prop_dict = {'a': 'b',
                 'list': [1, 2, 3, 4],
                 'dict': {'c': [4, 5]},
                 'number': 100}
    config_obj = importer.BuildConfig(template=path, properties=prop_dict)

    self.assertEqual(
        prop_dict,
        yaml.load(config_obj.GetContent())['resources'][0]['properties'])

    child = os.path.join('subdir', 'helper.py')
    expected_child = os.path.join('foo', child)

    self.assertEqual(expected_child, config_obj.BuildChildPath(child))

    self.assertEqual(path, config_obj.BuildChildPath(config_obj.GetBaseName()))

    self.assertIn('type: bar.py', config_obj.GetContent())
    self.assertIn('name: bar-py', config_obj.GetContent())
    self.assertIn('path: bar.py', config_obj.GetContent())

  @mock.patch('requests.get')
  def testBuildConfig_Url(self, mock_request):
    url = 'http://www.google.com/example/foo/bar.py'
    mock_responses = {url + '.schema': MockResponse(ERROR_404, 404)}

    mock_request.side_effect = lambda url: mock_responses[url]

    prop_dict = {'a': 'b',
                 'list': [1, 2, 3, 4],
                 'dict': {'c': [4, 5]},
                 'number': 100}
    config_obj = importer.BuildConfig(template=url, properties=prop_dict)

    self.assertEqual(
        prop_dict,
        yaml.load(config_obj.GetContent())['resources'][0]['properties'])

    child = 'subdir/helper.py'
    expected_child = 'http://www.google.com/example/foo/subdir/helper.py'

    self.assertEqual(expected_child, config_obj.BuildChildPath(child))

    self.assertEqual(url, config_obj.BuildChildPath(config_obj.GetBaseName()))

    self.assertIn('type: bar.py', config_obj.GetContent())
    self.assertIn('name: bar-py', config_obj.GetContent())
    self.assertIn('path: bar.py', config_obj.GetContent())
    mock_request.assert_called_once_with(url + '.schema')

  def testBuildConfig_WithBadGlobImport_EmptyDirectory(self):
    properties.VALUES.deployment_manager.glob_imports.Set(True)
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_bad_glob_import.yaml')
    # Expect OS-native path in the exception e.g. glob_directory[/ or \]*.py
    with self.assertRaisesRegex(exceptions.ConfigError,
                                r'Unable to read file .+glob_directory.[*].py'):
      importer.BuildTargetConfig(messages, config=config_name)

  def testBuildConfig_WithBadGlobImport_MissingFileName(self):
    properties.VALUES.deployment_manager.glob_imports.Set(True)
    config_name = self.GetTestData('simple_configs',
                                   'simple_with_glob_import_bad_name.yaml')
    with self.assertRaisesRegex(
        exceptions.ConfigError,
        (r'Cannot use import name thiswillbreak for path glob in file'
         r' .*bad_name\.yaml that matches multiple objects.')):
      importer.BuildTargetConfig(messages, config=config_name)

  def testBuildConfig_JinjaWithBadSchema(self):
    path = self.GetTestData('simple_configs', 'simple_bad_schema.jinja')
    prop_dict = {'zone': 'ZONE_TO_RUN'}

    with self.assertRaisesRegex(
        yaml.Error,
        r'Failed to parse YAML from \[{}\]'.format(
            re.escape(path + '.schema'))):
      importer.BuildConfig(template=path, properties=prop_dict)

  def testSanitizeBaseName(self):
    name = 'My_Template.jinja'
    expected = 'my-Template-jinja'
    self.assertEqual(expected, importer._SanitizeBaseName(name))

  def testIsUrl_File(self):
    self.assertFalse(importer._IsUrl('a/b/c/foo.bar'))
    self.assertFalse(importer._IsUrl('file//:foo.bar'))
    self.assertFalse(importer._IsUrl('c:\a\b.py'))
    # Will later fail "File not found"
    self.assertFalse(importer._IsUrl('www.google.com/foo.bar'))

  def testIsUrl_Url(self):
    self.assertTrue(importer._IsUrl('https://google.com/foo.bar'))
    self.assertTrue(importer._IsUrl('http://www.google.com/foo.bar'))
    # Will later fail "Invalid scheme"
    self.assertTrue(importer._IsUrl('ftp://www.google.com/foo.bar'))

  def testIsValidCompositeTypeSyntax_Success(self):
    expected_successes = ['test-with-dashes-in-id/composite:name-with-dashes',
                          'test-with-dashes-in-id/composite:name.with.periods',
                          'simpletest/composite:simple']
    for resource in expected_successes:
      self.assertTrue(importer._IsValidCompositeTypeSyntax(resource))

  def testIsValidCompositeTypeSyntax_Failure(self):
    expected_failures = ['test with spaces/composite:test',
                         'test/with/lots/of/slashes/composite:test',
                         'test.withadot/composite:test',
                         'test:with:colons/composite:test',
                         'testwith/compsite:misspelled']
    for resource in expected_failures:
      self.assertFalse(importer._IsValidCompositeTypeSyntax(resource))

  def testInvalidUrl_Scheme(self):
    try:
      importer._BuildFileImportObject('ssh://www.google.com/foo.py')
      self.fail('Url isnt http')
    except exceptions.ConfigError as e:
      self.assertIn('scheme', str(e))
      self.assertIn("'https'", str(e))
      self.assertIn("'http'", str(e))

  def testInvalidUrl_Path(self):
    try:
      importer._BuildFileImportObject('http://www.google.com')
      self.fail('Url has no path')
    except exceptions.ConfigError as e:
      self.assertIn('path', str(e))

  def testInvalidUrl_SlashPath(self):
    try:
      importer._BuildFileImportObject('http://www.google.com/')
      self.fail('Url has no path')
    except exceptions.ConfigError as e:
      self.assertIn('path', str(e))

  def testInvalidUrl_Query(self):
    try:
      url = 'https://www.google.com/foo.bar?something'
      importer._BuildFileImportObject(url)
      self.fail('Url has query')
    except exceptions.ConfigError as e:
      self.assertIn('queries', str(e))

  def testInvalidUrl_Fragment(self):
    try:
      url = 'https://www.google.com/foo.bar#something'
      importer._BuildFileImportObject(url)
      self.fail('Url has fragment')
    except exceptions.ConfigError as e:
      self.assertIn('fragments', str(e))

  @mock.patch('requests.get')
  def testImportUrl(self, mock_request):
    url = 'https://www.google.com/a/foo.py'
    url_obj = importer._BuildFileImportObject(url)

    self.assertTrue(url_obj.IsTemplate())
    self.assertEqual('foo.py', url_obj.GetBaseName())
    self.assertEqual('https://www.google.com/bar.py',
                     url_obj.BuildChildPath('../bar.py'))
    self.assertEqual('https://www.google.com/a/b/bar.py',
                     url_obj.BuildChildPath('b/bar.py'))

    hello = 'hello world'

    mock_responses = {url: MockResponse(hello, 200)}

    mock_request.side_effect = lambda url: mock_responses[url]

    self.assertEqual(hello, url_obj.GetContent())

    mock_request.assert_called_once_with(url)

  @mock.patch('requests.get')
  def testImportSchemaUrl(self, mock_request):
    url = 'https://www.google.com/a/foo.py.schema'
    url_obj = importer._BuildFileImportObject(url)

    self.assertFalse(url_obj.IsTemplate())

    hello = 'hello world'

    mock_responses = {url: MockResponse(hello, 200)}

    mock_request.side_effect = lambda url: mock_responses[url]

    self.assertTrue(url_obj.Exists())
    self.assertEqual(hello, url_obj.GetContent())

    mock_request.assert_called_once_with(url)

  @mock.patch('requests.get')
  def testImportUrl_403(self, mock_request):
    url = 'https://www.google.com/a/foo.py'
    url_obj = importer._BuildFileImportObject(url)

    mock_responses = {url: MockResponse(ERROR_403, 403)}

    mock_request.side_effect = lambda url: mock_responses[url]

    self.assertFalse(url_obj.Exists())

    try:
      url_obj.GetContent()
      self.fail('Url should return 403')
    except requests.exceptions.HTTPError as e:
      self.assertIn('forbidden', str(e))

    # Called twice, for Exists and GetContent
    self.assertEqual(2, mock_request.call_count)
    mock_request.assert_any_call(url)

  @mock.patch('requests.get')
  def testBuildTargetConfig_IdenticalUrlImports(self, mock_request):
    url = 'https://www.google.com/blah.yaml'
    content = '\n'
    mock_responses = {url: MockResponse(content, 200),}
    mock_request.side_effect = lambda url: mock_responses[url]

    config_name = self.GetTestData('simple_configs',
                                   'identical_duplicate_url_imports.yaml')
    import_name_map = {'my-import.yaml': 'empty.yaml'}
    imports = self.LoadNamedImportFiles(import_name_map)

    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertIn(expected_import, actual_target_config.imports)

    mock_request.assert_called_once_with(url)

  @mock.patch('requests.get')
  def testBuildTargetConfig_DuplicateUrlImportsWithSchema(self, mock_request):
    url = 'https://www.google.com/simple.jinja'
    schema = url + '.schema'

    filepath = self.GetTestData('simple_configs',
                                'simple.jinja')
    schema_filepath = self.GetTestData('simple_configs',
                                       'simple.jinja.schema')

    with open(filepath, 'r') as a_file:
      content = a_file.read()

    with open(schema_filepath, 'r') as schema_file:
      schema_content = schema_file.read()

    subhelper_url = 'https://www.google.com/helper.jinja'
    subhelper_schema = subhelper_url + '.schema'

    subhelper_filepath = self.GetTestData('simple_configs',
                                          'helper.jinja',)

    with open(subhelper_filepath, 'r') as subhelper_file:
      subhelper_content = subhelper_file.read()

    mock_responses = {url: MockResponse(content, 200),
                      schema: MockResponse(schema_content, 200),
                      subhelper_url: MockResponse(subhelper_content, 200),
                      subhelper_schema: MockResponse(ERROR_404, 404),
                     }
    mock_request.side_effect = lambda url: mock_responses[url]

    config_name = self.GetTestData('simple_configs',
                                   'duplicate_url_with_schema.yaml')
    import_name_map = {'simple.jinja': 'simple.jinja',
                       'simple.jinja.schema': 'simple.jinja.schema',
                       'helper.jinja': 'helper.jinja',
                      }

    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertTrue(expected_import in actual_target_config.imports,
                      'missing expected import ' + str(expected_import))

    self.assertEqual(4, mock_request.call_count)
    mock_request.assert_has_calls([mock.call(schema),
                                   mock.call(url),
                                   mock.call(subhelper_schema),
                                   mock.call(subhelper_url)])

  @mock.patch('requests.get')
  def testBuildTargetConfig_SharedUrlImports(self, mock_request):
    helper_url = 'https://www.google.com/shared_helper.jinja'
    helper_schema = helper_url + '.schema'

    helper_filepath = self.GetTestData('simple_configs',
                                       'shared_helper.jinja')
    helper_schema_filepath = self.GetTestData('simple_configs',
                                              'shared_helper.jinja.schema')

    with open(helper_filepath, 'r') as helper_file:
      helper_content = helper_file.read()

    with open(helper_schema_filepath, 'r') as helper_schema_file:
      helper_schema_content = helper_schema_file.read()

    subhelper_url = 'https://www.google.com/subhelper.jinja'
    subhelper_schema = subhelper_url + '.schema'

    subhelper_filepath = self.GetTestData('simple_configs',
                                          'subhelper.jinja')

    with open(subhelper_filepath, 'r') as subhelper_file:
      subhelper_content = subhelper_file.read()

    shared_url = 'https://www.google.com/sub_directory/shared.jinja'
    shared_schema = shared_url + '.schema'

    shared_filepath = self.GetTestData('simple_configs',
                                       'sub_directory',
                                       'shared.jinja')
    shared_schema_filepath = self.GetTestData('simple_configs',
                                              'sub_directory',
                                              'shared.jinja.schema')

    with open(shared_filepath, 'r') as shared_file:
      shared_content = shared_file.read()

    with open(shared_schema_filepath, 'r') as shared_schema_file:
      shared_schema_content = shared_schema_file.read()

    mock_responses = {helper_url: MockResponse(helper_content, 200),
                      helper_schema: MockResponse(helper_schema_content, 200),
                      subhelper_url: MockResponse(subhelper_content, 200),
                      subhelper_schema: MockResponse(ERROR_404, 404),
                      shared_url: MockResponse(shared_content, 200),
                      shared_schema: MockResponse(shared_schema_content, 200),
                     }
    mock_request.side_effect = lambda url: mock_responses[url]

    config_name = self.GetTestData('simple_configs',
                                   'shared_url_helper.yaml')
    import_name_map = {'shared_helper.jinja': 'shared_helper.jinja',
                       'shared_helper.jinja.schema':
                           'shared_helper.jinja.schema',
                       'subhelper.jinja': 'subhelper.jinja',
                       'shared.jinja': 'sub_directory/shared.jinja',
                       'shared.jinja.schema':
                       'sub_directory/shared.jinja.schema'}

    imports = self.LoadNamedImportFiles(import_name_map)
    with open(config_name, 'r') as config_file:
      config_contents = config_file.read()

    actual_target_config = importer.BuildTargetConfig(messages,
                                                      config=config_name)
    expected_target_config = messages.TargetConfiguration(
        config=messages.ConfigFile(content=config_contents),
        imports=[
            messages.ImportFile(
                name=import_item[0],
                content=import_item[1]
            )
            for import_item in imports.items()
        ]
    )
    self.assertEqual(expected_target_config.config,
                     actual_target_config.config)
    self.assertEqual(len(imports), len(actual_target_config.imports))
    for expected_import in expected_target_config.imports:
      self.assertTrue(expected_import in actual_target_config.imports,
                      'missing expected import ' + str(expected_import))

    self.assertEqual(6, mock_request.call_count)
    mock_request.assert_has_calls([mock.call(shared_schema),
                                   mock.call(shared_url),
                                   mock.call(helper_schema),
                                   mock.call(helper_url),
                                   mock.call(subhelper_schema),
                                   mock.call(subhelper_url)])


if __name__ == '__main__':
  test_case.main()
