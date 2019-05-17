# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Data Catalog schema tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.data_catalog.entries import util
from tests.lib import parameterized
from tests.lib import test_case


class SchemaTest(test_case.TestCase, parameterized.TestCase):
  """Data Catalog schema tests class."""

  def SetUp(self):
    self.messages = apis.GetMessagesModule('datacatalog', 'v1beta1')

  @parameterized.named_parameters(
      ('YAML file contents',
       """\
       - column: field1
         type: type1
         description: description1
       - column: field2
         type: RECORD
         subcolumns:
         - column: field3
           type: type3
           mode: REQUIRED
         - column: field4
           type: type4
           mode: REPEATED"""),
      ('JSON file contents',
       """\
       [
         {
           "column": "field1",
           "type": "type1",
           "description": "description1"
         },
         {
           "column": "field2",
           "type": "RECORD",
           "subcolumns":
             [
               {
                 "column": "field3",
                 "type": "type3",
                 "mode": "REQUIRED"
               },
               {
                 "column": "field4",
                 "type": "type4",
                 "mode": "REPEATED"
               }
             ]
         }
       ]""")
  )
  def testProcessSchemaFromFile(self, contents):
    schema_message = util.ProcessSchemaFromFile(contents)
    expected_message = encoding.DictToMessage(
        {'columns': [
            {'column': 'field1', 'type': 'type1',
             'description': 'description1'},
            {'column': 'field2', 'type': 'RECORD', 'subcolumns': [
                {'column': 'field3', 'type': 'type3', 'mode': 'REQUIRED'},
                {'column': 'field4', 'type': 'type4', 'mode': 'REPEATED'}
            ]}
        ]},
        self.messages.GoogleCloudDatacatalogV1beta1Schema)
    self.assertEqual(schema_message, expected_message)

  def testProcessSchemaFromFileInvalidSchemaFile(self):
    contents = '{]'
    with self.assertRaisesRegex(
        util.InvalidSchemaFileError, 'Error parsing schema file.*'):
      util.ProcessSchemaFromFile(contents)

  def testProcessSchemaFromFileInvalidDict(self):
    contents = '[null]'
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Invalid schema: expected list of column names along with their '
        r'types, modes, descriptions, and/or nested subcolumns.'):
      util.ProcessSchemaFromFile(contents)

  def testProcessSchemaFromFileInvalidFieldType(self):
    contents = '{"column": "field1", "type": "type1", "description": 5}'
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'Invalid schema: \[Expected type.*for field description, found 5.*'):
      util.ProcessSchemaFromFile(contents)

  def testProcessSchemaFromFileUnrecognizedFields(self):
    contents = """
      [
        {"column": field1", "invalid1": "thing1", "invalid2": "thing2"},
        {"column": "field2", "type": "RECORD", "subcolumns": [
          {"column": "field3", "invalid3": "thing3"}
        ]}
      ]
    """
    with self.assertRaisesRegex(
        util.InvalidSchemaError,
        r'(?m)Invalid schema, the following fields are unrecognized:\n'
        r'\[0\].invalid1\n'
        r'\[0\].invalid2\n'
        r'\[1\].subcolumns\[0\].invalid3'):
      util.ProcessSchemaFromFile(contents)


if __name__ == '__main__':
  test_case.main()
