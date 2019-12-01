# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Tests for Data Catalog tags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import tags
from tests.lib import sdk_test_base
from tests.lib import test_case


class TagsTest(sdk_test_base.WithFakeAuth):
  """Unit tests for Data Catalog tags functionality."""

  def SetUp(self):
    self.client = tags.TagsClient()

  def test_GetFieldType_Primitive(self):
    primitive_field_type_enum = (
        self.client.messages.GoogleCloudDatacatalogV1beta1FieldType
        .PrimitiveTypeValueValuesEnum
    )
    test_cases = [
        (primitive_field_type_enum.DOUBLE, 'double'),
        (primitive_field_type_enum.STRING, 'string'),
        (primitive_field_type_enum.BOOL, 'bool'),
        (primitive_field_type_enum.TIMESTAMP, 'timestamp'),
    ]
    for (type_input, expected) in test_cases:
      message_type = (
          self.client.messages.GoogleCloudDatacatalogV1beta1FieldType(
              primitiveType=type_input,
          )
      )
      field_type = self.client._GetFieldType(message_type)
      self.assertEqual(expected, field_type)

  def test_ParseFieldType_Enum(self):
    message_type = self.client.messages.GoogleCloudDatacatalogV1beta1FieldType(
        enumType=(
            self.client.messages
            .GoogleCloudDatacatalogV1beta1FieldTypeEnumType(
                allowedValues=[
                    self.client.messages
                    .GoogleCloudDatacatalogV1beta1FieldTypeEnumTypeEnumValue(
                        displayName='a',
                    )
                ]
            )
        ),
    )
    field_type = self.client._GetFieldType(message_type)
    self.assertEqual('enum', field_type)

  def test_MakeTagField_Primitive(self):
    tag_field = self.client.messages.GoogleCloudDatacatalogV1beta1TagField
    dbl_tag_field = tag_field()
    dbl_tag_field.doubleValue = 1234

    str_tag_field = tag_field()
    str_tag_field.stringValue = 'string'

    bool_tag_field = tag_field()
    bool_tag_field.boolValue = True

    timestamp_tag_field = tag_field()
    timestamp_tag_field.timestampValue = '1970-01-01T00:00:00.000Z'

    test_cases = [
        (('double', 1234), dbl_tag_field),
        (('string', 'string'), str_tag_field),
        (('bool', True), bool_tag_field),
        (('timestamp', '1970-01-01T00:00:00.000Z'), timestamp_tag_field),
    ]
    for (input_case, expected) in test_cases:
      field_type = self.client._MakeTagField(input_case[0], input_case[1])
      self.assertEqual(expected, field_type)

  def test_MakeTagField_Timestamp_Invalid(self):
    with self.assertRaisesRegex(
        tags.InvalidTagError,
        r"Invalid timestamp value: \(u?'Unknown string format:', "
        r"u?'asdf'\) \[asdf\]"
    ):
      self.client._MakeTagField('timestamp', 'asdf')


if __name__ == '__main__':
  test_case.main()
