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
"""Tests for step_json."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataflow import step_json
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base


class StepJsonTest(sdk_test_base.SdkBase):

  def testExtractStepNoProperties(self):
    step_msg = base.MESSAGE_MODULE.Step(
        kind='Kind',
        name='Name',
    )
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({}, result['properties'])

  def testExtractStepEmptyProperties(self):
    step_msg = base.MESSAGE_MODULE.Step(
        kind='Kind',
        name='Name',
        properties=base.MESSAGE_MODULE.Step.PropertiesValue(
            additionalProperties=[]))
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({}, result['properties'])

  def testExtractStepBooleanProperty(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step,
                                      """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "bool_value": {
      "@type": "http://schema.org/Boolean",
      "value": true
    }
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({'bool_value': True}, result['properties'])

  def testExtractStepStringProperty(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step,
                                      """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "string_value": {
      "@type": "http://schema.org/Text",
      "value": "Hello"
    }
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({'string_value': 'Hello'}, result['properties'])

  def testExtractStepStringList(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step,
                                      """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "array_value": [
      {
        "@type": "http://schema.org/Text",
        "value": "Hello"
      },
      {
        "@type": "http://schema.org/Text",
        "value": "World"
      }
    ]
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({'array_value': ['Hello', 'World']},
                     result['properties'])

  def testExtractStepBadValue(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step, """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "object_value": {
      "@type": "OutputReference",
      "output_name": 1337,
      "step_name": "s1"
    }
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual(
        {'object_value': {'@type': 'OutputReference',
                          'output_name': 'No decoding provided '
                                         'for: <JsonValue\n integer_value: '
                                         '1337>',
                          'step_name': 's1'}}, result['properties'])

  def testExtractStepBadDecoratedObject(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step, """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "object_value": {
      "@type": "http://schema.org/Text"
    }
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    pattern = ('Missing value for type \\[http://schema.org/Text] in proto '
               '\\[<JsonValue\n object_value: '
               '<JsonObject\n properties: \\['
               '<Property\n key: u?\'@type\'\n value: '
               '<JsonValue\n string_value: u?\'http://schema.org/Text\'>>]>>]')
    self.assertRegexpMatches(result['properties']['object_value'], pattern)

  def testExtractStepObject(self):
    step_msg = encoding.JsonToMessage(base.MESSAGE_MODULE.Step,
                                      """{
  "kind": "Kind",
  "name": "Name",
  "properties": {
    "object_value": {
      "@type": "OutputReference",
      "output_name": "output",
      "step_name": "s1"
    }
  }
}""")
    result = step_json._ExtractStep(step_msg)
    self.assertEqual('Kind', result['kind'])
    self.assertEqual('Name', result['name'])
    self.assertEqual({'object_value': {'@type': 'OutputReference',
                                       'output_name': 'output',
                                       'step_name': 's1'}},
                     result['properties'])


if __name__ == '__main__':
  test_case.main()
