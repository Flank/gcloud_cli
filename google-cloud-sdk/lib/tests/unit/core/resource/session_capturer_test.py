# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Unit tests for the session_capturer module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import io
import json

from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import session_capturer
from tests.lib import sdk_test_base

import six.moves.builtins


class SessionCapturerTest(sdk_test_base.SdkBase):

  class MockPrinter(object):
    records = []

    def __init__(self, *unused_args, **unused_kwargs):
      pass

    def AddRecord(self, record):
      SessionCapturerTest.MockPrinter.records.append(record)

    @classmethod
    def GetRecords(cls):
      records = cls.records
      cls.records = []
      return records

  def SetUp(self):
    self._capturer = session_capturer.SessionCapturer(capture_streams=False)

  def TearDown(self):
    self._capturer._Finalize()

  def testRequest(self):
    uri = 'http://some/uri'
    method = 'METHOD'
    body = ' Some  body\n  here   '
    headers = {
        'Header1': 'value1',
        'Header2': 'value2',
        'user-agent': 'some useless info',
        'Authorization': 'private information'
    }
    self._capturer.CaptureHttpRequest(uri, method, body, headers)
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    headers.pop('user-agent')
    headers.pop('Authorization')
    self.assertEqual(self.MockPrinter.GetRecords(), [{
        'request': {
            'uri': uri,
            'method': method,
            'body': body,
            'headers': headers
        }
    }])

  def testResponse(self):
    headers = {
        'Header1': 'value1',
        'Header2': 'value2'
    }
    content = 'Some text\n   content.  '
    self._capturer.CaptureHttpResponse(headers, content)
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    self.assertEqual(self.MockPrinter.GetRecords(), [{
        'response': {
            'response': headers,
            'content': [content]
        }
    }])

  def testArgs(self):
    class TestArgs(object):

      def __init__(self):
        pass

      @property
      def command_path(self):
        return ['path/to/gcloud', 'some', 'command']

      def GetSpecifiedArgs(self):
        return {
            'NAME': 'name',
            '--key': 'value',
            '--capture-session-file': 'some_file.yaml'
        }

    self._capturer.CaptureArgs(TestArgs())
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    self.assertEqual(self.MockPrinter.GetRecords(), [{
        'args': {
            'command': 'some command name',
            'specified_args': {
                '--key': 'value'
            }
        }
    }])

  def testState(self):
    self._capturer.CaptureState()
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    records = self.MockPrinter.GetRecords()
    self.assertEqual(len(records), 1)
    self.assertEqual(list(records[0].keys()), ['state'])
    for state_key in records[0]['state'].keys():
      self.assertIn(state_key, self._capturer.STATE_MOCKS)

  def testProperties(self):
    property_values = {
        'core': {
            'capture_session_file': '/path/to/file.yaml',
            'account': 'example@example.com',
            'property1': 'value1'
        },
        'property2': '    val\nue2  ',
        'none_property': [None],
    }
    self._capturer.CaptureProperties(property_values)
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    property_values['core'].pop('capture_session_file')
    property_values['core'].pop('account')
    self.assertEqual(self.MockPrinter.GetRecords(), [{
        'properties': property_values
    }])

  def testException(self):
    exc = Exception('some message')
    self._capturer.CaptureException(exc)
    self._capturer.Print(None, SessionCapturerTest.MockPrinter)
    module_path = 'Exception'
    actual = self.MockPrinter.GetRecords()
    actual[0]['exception']['type'] = module_path
    self.assertEqual([{
        'exception': {
            'type': module_path,
            'message': 'some message'
        }
    }],
                     actual)

  def testJsonList(self):
    headers = '\n'.join({
        'Header1: value1',
        'Header2: value2',
        'Content-Type: application/json;',
        'Header3: value3'
    }) + '\r\n\r\n'
    json_content = {
        'key1': {
            'key2': 'value2',
            'key3': '  value3'
        },
        'key4': 'val\nue4'
    }
    result = self._capturer._ToList(
        headers + json.dumps(json_content) + '\n\r\n')
    self.assertEqual(result, [headers, {'json': json_content}, '\n\r\n'])

  def testListNoneBatch(self):
    json_content = {
        'key1': {
            'key2': 'value2',
            'key3': '  value3'
        },
        'key4': 'val\nue4'
    }
    result = self._capturer._ToList(json.dumps(json_content))
    self.assertEqual(result, [{'json': json_content}])


class StreamCapturerTest(sdk_test_base.SdkBase):

  def testWrite(self):
    real_stream = io.StringIO()
    stream = session_capturer.OutputStreamCapturer(real_stream)
    text = 'Some text\n\n to write.  '
    lines = ['Some\n', 'lines\n', 'to\n', 'write\n', '\n', '.\n']
    stream.write(text)
    stream.writelines(lines)
    self.assertEqual(text + ''.join(lines), stream.GetValue())
    self.assertEqual(stream.GetValue(), real_stream.getvalue())
    self.assertEqual(stream.isatty(), True)


class FileIoCapturerTest(sdk_test_base.SdkBase):

  def testFilesToCapture(self):
    def _SideEffect(*unused_args, **unused_kwargs):
      return io.StringIO()
    with self.StartObjectPatch(
        six.moves.builtins, 'open', side_effect=_SideEffect):
      file_io_capturer = session_capturer.FileIoCapturer()
    with self.StartObjectPatch(properties.VALUES.core.capture_session_file,
                               'Get',
                               return_value='session.yaml'):
      with open('session.yaml', 'w') as f:
        f.write('some text')
    self.assertEqual(file_io_capturer.GetOutputs(), [])
    file_io_capturer.Unmock()


if __name__ == '__main__':
  sdk_test_base.main()
