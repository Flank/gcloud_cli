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

"""Tests for Data Catalog tag-templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import tag_templates
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import sdk_test_base
from tests.lib import test_case


class TagTemplatesTest(sdk_test_base.WithFakeAuth):
  """Unit tests for Data Catalog tag-templates functionality."""

  def SetUp(self):
    self.client = tag_templates.TagTemplatesClient()

  def test_ParseFieldType_Primitives(self):
    primitive_field_type_enum = (
        self.client.messages.GoogleCloudDatacatalogV1beta1FieldType
        .PrimitiveTypeValueValuesEnum
    )
    test_cases = [
        ('double', primitive_field_type_enum.DOUBLE),
        ('string', primitive_field_type_enum.STRING),
        ('bool', primitive_field_type_enum.BOOL),
        ('timestamp', primitive_field_type_enum.TIMESTAMP),
    ]
    for (type_input, expected_type) in test_cases:
      field_type = self.client._ParseFieldType(type_input)
      expected = self.client.messages.GoogleCloudDatacatalogV1beta1FieldType(
          primitiveType=expected_type,
      )
      self.assertEqual(expected, field_type)

  def test_ParseFieldType_Enum(self):
    test_cases = [
        ('enum(A)', ['A']),
        ('enum(A|B)', ['A', 'B']),
    ]
    for (enum_input, expected_values) in test_cases:
      field_type = self.client._ParseFieldType(enum_input)
      values = []
      for value in expected_values:
        values.append(
            self.client.messages
            .GoogleCloudDatacatalogV1beta1FieldTypeEnumTypeEnumValue(
                displayName=value,
            )
        )
      expected = self.client.messages.GoogleCloudDatacatalogV1beta1FieldType(
          enumType=(
              self.client.messages
              .GoogleCloudDatacatalogV1beta1FieldTypeEnumType(
                  allowedValues=values
              )
          )
      )
    self.assertEqual(expected, field_type)

  def test_ParseFieldType_Invalid(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        r'Invalid value for \[--field\]: invalid'
    ):
      self.client._ParseFieldType('invalid')


if __name__ == '__main__':
  test_case.main()


