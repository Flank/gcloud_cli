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
"""dlp hooks tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.bq import hooks
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class HooksTest(sdk_test_base.SdkBase, parameterized.TestCase):
  """Base hooks lib Test class."""

  def SetUp(self):
    self.msg = apis.GetMessagesModule('bigquery', 'v2')
    self.test_project = 'fakeproject'
    properties.VALUES.core.project.Set(self.test_project)

  def testTableSchemaFileProcessorSuccess(self):
    contents = """\
      {
        "schema":[
        {
          "name":"field1",
          "type":"STRING",
          "mode": "REQUIRED"
        },
        {
          "name":"field2",
          "type":"FLOAT"
        }
        ]
      }"""
    field = self.msg.TableFieldSchema
    schema = self.msg.TableSchema
    expected = schema(
        fields=[field(name='field1', type='STRING', mode='REQUIRED'),
                field(name='field2', type='FLOAT', mode='NULLABLE')])
    result = hooks.BqTableSchemaFileProcessor(contents)
    self.assertEqual(expected, result)

  @parameterized.named_parameters(
      ('Missing Field List', '{"schema":[]}',
       'Error parsing schema file: no schema field list defined in file'),
      ('BadJsonFile', '{[}', 'Error parsing schema file'),
      ('BadFieldDefinition', '{"schema":[{"name": "BadField"}]}',
       'Error parsing schema file, invalid field definition'),
  )
  def testTableSchemaFileProcessorError(self, content, error_message):
    with self.assertRaisesRegex(hooks.SchemaFileError, error_message):
      hooks.BqTableSchemaFileProcessor(content)

  def testPermissionsFileProcessor(self):
    contents = (
        '{"access": [{"role": "OWNER", "userByEmail": "testUser@google.com"},'
        '{"role": "READER", "specialGroup": "projectReaders"}]}')
    access_msg = self.msg.Dataset.AccessValueListEntry
    expected = [access_msg(role='OWNER', userByEmail='testUser@google.com'),
                access_msg(role='READER', specialGroup='projectReaders')]
    result = hooks.PermissionsFileProcessor([contents])
    self.assertEqual(expected, result)

  def testPermissionsFileProcessorInvalidPerms(self):
    contents = """\
{
  "access": [
    {
      "role": "OWNER",
      "BadValue": "testUser@google.com"
    }
  ]
}"""
    with self.assertRaisesRegex(hooks.PermissionsFileError,
                                ('Error parsing permissions file: invalid '
                                 'permission definition')):
      hooks.PermissionsFileProcessor([contents])

  def testPermissionsFileProcessorBadYamlFile(self):
    with self.assertRaisesRegex(hooks.PermissionsFileError,
                                ('Error parsing permissions file '
                                 '\\[Failed to parse YAML: ')):
      hooks.PermissionsFileProcessor(['{'])

  def testGetRelaxedCols(self):
    field = self.msg.TableFieldSchema
    original_schema = [field(name='field1', type='STRING', mode='REQUIRED'),
                       field(name='field2', type='FLOAT', mode='NULLABLE')]
    expected_schema = [field(name='field1', type='STRING', mode='NULLABLE'),
                       field(name='field2', type='FLOAT', mode='NULLABLE')]
    schema_map = {f.name: f for f in original_schema}
    result = sorted(
        hooks._GetRelaxedCols(['field1'], schema_map).values(),
        key=lambda x: x.name)
    self.assertEqual(expected_schema, result)

  def testGetRelaxedColsFailure(self):
    with self.assertRaisesRegex(hooks.SchemaUpdateError,
                                'Invalid Schema change'):
      hooks._GetRelaxedCols(['field1'], {})

  def testGetAddedCols(self):
    field = self.msg.TableFieldSchema
    original_schema = [field(name='field1', type='STRING', mode='REQUIRED'),
                       field(name='field2', type='FLOAT', mode='NULLABLE')]
    expected_schema = [field(name='field1', type='STRING', mode='REQUIRED'),
                       field(name='field2', type='FLOAT', mode='NULLABLE'),
                       field(name='field3', type='INTEGER', mode='NULLABLE')]
    schema_map = {f.name: f for f in original_schema}
    new_fields = [field(name='field3', type='INTEGER', mode='NULLABLE')]
    result = sorted(hooks._AddNewColsToSchema(new_fields, schema_map).values(),
                    key=lambda x: x.name)
    self.assertEqual(expected_schema, result)

  def testGetAddedColsFailure(self):
    field = self.msg.TableFieldSchema
    original_schema = [field(name='field1', type='STRING', mode='REQUIRED'),
                       field(name='field2', type='FLOAT', mode='NULLABLE')]
    schema_map = {f.name: f for f in original_schema}
    with self.assertRaisesRegex(hooks.SchemaUpdateError,
                                'Invalid Schema change'):
      new_fields = [field(name='field1', type='FLOAT', mode='REQUIRED')]
      hooks._AddNewColsToSchema(new_fields, schema_map)

  def testTableDataFileProcessorSuccess(self):
    contents = """\
      [{
          "field1":"value1",
          "field2": true,
        },
        {
          "field1":"value3",
          "field2": false,
        }
        ]"""

    row_entry_type = self.msg.TableDataInsertAllRequest.RowsValueListEntry
    json_type = self.msg.JsonObject

    expected = [
        row_entry_type(
            json=encoding.DictToMessage({
                'field1': 'value1',
                'field2': True
            }, json_type)),
        row_entry_type(
            json=encoding.DictToMessage({
                'field1': 'value3',
                'field2': False
            }, json_type))
    ]
    result = hooks.BqTableDataFileProcessor(contents)
    self.assertEqual(expected, result)

  @parameterized.named_parameters(
      ('Missing Field List', '[]',
       'Error parsing data file: no data records defined in file'),
      ('BadJsonFile', '{"[]"}', 'Error parsing data file'),
  )
  def testTableDataFileProcessorError(self, content, error_message):
    with self.assertRaisesRegex(hooks.TableDataFileError, error_message):
      hooks.BqTableDataFileProcessor(content)


if __name__ == '__main__':
  test_case.main()
