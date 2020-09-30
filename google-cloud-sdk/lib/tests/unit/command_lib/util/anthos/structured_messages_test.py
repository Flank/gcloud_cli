# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the command_lib.util.anthos.messages module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import collections
import json

from googlecloudsdk.command_lib.util.anthos import structured_messages as sm
from googlecloudsdk.core import yaml
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
import six

RESOURCE_JSON = collections.OrderedDict({
    'name': 'do-not-delete-gke-knative-test-cluster',
    'nodeConfig': collections.OrderedDict({
        'machineType': 'n1-standard-2',
        'diskSizeGb': 100,
        'oauthScopes': [
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring.write',
            'https://www.googleapis.com/auth/pubsub'
        ],
        'imageType': 'COS',
        'serviceAccount': 'default',
        'diskType': 'pd-standard'
    }),
    'selfLink': 'https://do-not-delete-gke-knative-test-cluster',
    'zone': 'us-central1-a',
    'endpoint': '35.239.121.203',
})

RESOURCE_LIST = [RESOURCE_JSON] * 3
DICT_TEST_DATA = {
    'ERROR': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'error_details': collections.OrderedDict({
            'error': 'Processing Error'
        })
    }),
    'ERROR_WITH_CTX': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'error_details': collections.OrderedDict({
            'error': 'Processing Error',
            'context': 'Line 1:Foo -> Bar -> Call foo_bar()'
        })
    }),
    'STATUS': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'body': 'my message',
    }),
    'STATUS_WITH_RESOURCES': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'body': 'Message',
        'resource_body': RESOURCE_JSON
    }),
    'STATUS_WITH_RESOURCES_AND_ERROR': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'body': 'Message',
        'resource_body': RESOURCE_LIST,
        'error_details': collections.OrderedDict({
            'error': 'Processing Error',
            'context': ('Line 1:Foo -> '
                        'Bar -> Call foo_bar()')
        })
    }),
    'RESOURCE_LIST': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'body': 'resources',
        'resource_body': RESOURCE_LIST
    }),
    'BAD_RESOURCES': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z',
        'body': 'resources',
        'resource_body': 'BAD_DATA'
    }),
    'MISSING_REQUIRED': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-01-01T00:00:00.000Z'
    }),
    'BAD_DATE': collections.OrderedDict({
        'version': '1.0.0',
        'timestamp': '2020-1-1',
        'body': 'Message',
    }),
}

YAML_TEST_DATA = {
    key: yaml.dump(v) for key, v in DICT_TEST_DATA.items()
}


JSON_TEST_DATA = {
    key: json.dumps(v, sort_keys=True) for key, v in DICT_TEST_DATA.items()
}


def BuildTestMessage(dict_message):
  return sm.OutputMessage(**dict_message)


class MessagesTests(parameterized.TestCase, sdk_test_base.WithLogCapture):
  """Test messages module functions."""

  @parameterized.named_parameters(
      ('MinimalValues', 'STATUS'),
      ('ErrorOnly', 'ERROR'),)
  def testCreateOutputMessage(self, item):
    self.assertIsNotNone(BuildTestMessage(DICT_TEST_DATA[item]))

  @parameterized.named_parameters(
      ('Bad Resource Body', 'BAD_RESOURCES', ValueError),
      ('TooFewValues', 'MISSING_REQUIRED', sm.InvalidMessageError),
      ('TooManyValues', 'STATUS_WITH_RESOURCES_AND_ERROR',
       sm.InvalidMessageError),)
  def testCreateOutputMessageErrors(self, test_value, raised):
    with self.assertRaises(raised):
      BuildTestMessage(DICT_TEST_DATA[test_value])

  @parameterized.named_parameters(
      ('MinimalValues', 'STATUS', BuildTestMessage(DICT_TEST_DATA['STATUS'])),
      ('ErrorOnly', 'ERROR', BuildTestMessage(DICT_TEST_DATA['ERROR'])),
      ('ErrorWithContext', 'ERROR_WITH_CTX',
       BuildTestMessage(DICT_TEST_DATA['ERROR_WITH_CTX'])),
      ('ListOfResources', 'RESOURCE_LIST',
       BuildTestMessage(DICT_TEST_DATA['RESOURCE_LIST'])),)
  def testFromString(self, dict_key, expected):
    self.assertEqual(expected,
                     sm.OutputMessage.FromString(JSON_TEST_DATA[dict_key]))

  @parameterized.named_parameters(
      ('NotADict', 'FOOBAR', sm.InvalidMessageError),
      ('InvalidType', JSON_TEST_DATA['MISSING_REQUIRED'],
       sm.InvalidMessageError),
      ('Empty', '{}', sm.InvalidMessageError),
      ('Bad Resource Body', JSON_TEST_DATA['BAD_RESOURCES'],
       sm.InvalidMessageError),
      ('Bad Date', JSON_TEST_DATA['BAD_DATE'], sm.MessageParsingError),
      ('TooManyValues', JSON_TEST_DATA['STATUS_WITH_RESOURCES_AND_ERROR'],
       sm.InvalidMessageError),)
  def testFromStringErrors(self, test_value, raised):
    with self.assertRaises(raised):
      sm.OutputMessage.FromString(test_value)

  @parameterized.named_parameters(
      ('MinimalValues', 'STATUS', BuildTestMessage(DICT_TEST_DATA['STATUS'])),
      ('ErrorOnly', 'ERROR', BuildTestMessage(DICT_TEST_DATA['ERROR'])),
      ('ErrorWithContext', 'ERROR_WITH_CTX',
       BuildTestMessage(DICT_TEST_DATA['ERROR_WITH_CTX'])),
      ('WithResources', 'STATUS_WITH_RESOURCES',
       BuildTestMessage(DICT_TEST_DATA['STATUS_WITH_RESOURCES'])),
  )
  def testToYamlString(self, msg_key, msg):
    expected = YAML_TEST_DATA[msg_key]
    actual = six.text_type(msg)
    self.assertEqual(expected, actual)

  @parameterized.named_parameters(
      ('MinimalValues', 'STATUS', BuildTestMessage(DICT_TEST_DATA['STATUS'])),
      ('ErrorOnly', 'ERROR', BuildTestMessage(DICT_TEST_DATA['ERROR'])),
      ('ErrorWithContext', 'ERROR_WITH_CTX',
       BuildTestMessage(DICT_TEST_DATA['ERROR_WITH_CTX'])),
      ('WithResources', 'STATUS_WITH_RESOURCES',
       BuildTestMessage(DICT_TEST_DATA['STATUS_WITH_RESOURCES'])),
  )
  def testToJSONString(self, msg_key, msg):
    expected = JSON_TEST_DATA[msg_key]
    print(expected)
    actual = msg.ToJSON()
    self.assertEqual(expected, actual)

  @parameterized.named_parameters(
      ('ErrorOnly', 'ERROR', 'Error: [Processing Error].', None),
      ('ErrorWithContext', 'ERROR_WITH_CTX',
       'Error: [Processing Error]. Additional details: '
       '[Line 1:Foo -> Bar -> Call foo_bar()]', None),
      ('CustomFormat', 'ERROR_WITH_CTX',
       'Error=>[Processing Error]. Details=> '
       '[Line 1:Foo -> Bar -> Call foo_bar()]',
       ['Error=>[{error}]. Details=>',
        ' [{context}]'])
  )
  def testErrorDetailFormat(self, msg_key, expected, custom_format):
    error_msg = BuildTestMessage(DICT_TEST_DATA[msg_key])
    if custom_format:
      self.assertEqual(expected, error_msg.error_details.Format(
          error_format=custom_format[0], context_format=custom_format[1]))
    else:
      self.assertEqual(expected, error_msg.error_details.Format())


if __name__ == '__main__':
  test_case.main()
