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

"""Tests for the session module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.core import http
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.scenario import assertions
from tests.lib.scenario import schema
from tests.lib.scenario import session
from tests.lib.scenario import test_base
from tests.lib.scenario import updates


class _SessionTestsBase(sdk_test_base.WithOutputCapture,
                        test_case.WithInput,
                        parameterized.TestCase):
  """Base class for session tests."""

  def SetUp(self):
    self.stream_mocker = test_base.CreateStreamMocker(self)

  def CommandExecution(self, *events):
    data = {
        'execute_command': {
            'command': '', 'events': [e for e in events]}}
    return schema.CommandExecutionAction.FromData(data)

  @contextlib.contextmanager
  def Execute(self, ce, update_modes=None):
    with assertions.FailureCollector(
        update_modes=update_modes or []) as failures:
      with session.Session(ce.events, failures, self.stream_mocker) as s:
        yield s


class SessionTests(_SessionTestsBase):
  """Tests of session event handling."""

  def testNotEnoughEvents(self):
    ce = self.CommandExecution()
    with self.assertRaises(assertions.Error):
      with self.Execute(ce) as s:
        log.status.write('foo')
    # Ensure the event got added.
    self.assertEqual(1, len(s.GetEventSequence()))

  def testTooManyEvents(self):
    ce = self.CommandExecution(
        {'expect_stderr': 'foo'},
        {'expect_stderr': 'bar'})
    with self.assertRaises(assertions.Error):
      with self.Execute(ce) as s:
        pass
    self.assertEqual(2, len(s.GetEventSequence()))

  def testJustStderr(self):
    ce = self.CommandExecution({'expect_stderr': 'foo'})
    with self.Execute(ce):
      log.status.write('foo')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        log.status.write('bar')

  def testJustStdout(self):
    ce = self.CommandExecution({'expect_stdout': 'foo'})
    with self.Execute(ce):
      log.out.write('foo')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        log.out.write('bar')

  def testJustUxEvent(self):
    ce = self.CommandExecution({'expect_progress_bar': {'message': 'foo'}})
    with self.Execute(ce):
      log.status.write('{"ux": "PROGRESS_BAR", "message": "foo"}')

    with self.assertRaises(session.Error):
      with self.Execute(ce):
        log.status.write('{"ux": "PROGRESS_BAR", message: foo')

  def testOutputMixAndAggregation(self):
    ce = self.CommandExecution(
        {'expect_stdout': 'this'},
        {'expect_stderr': 'is'},
        {'expect_stdout': 'a scenario'},
        {'expect_stderr': 'test'},
    )
    with self.Execute(ce):
      log.out.write('this')
      log.status.write('is')
      log.out.write('a')
      log.out.write(' ')
      log.out.write('scenario')
      log.status.write('te')
      log.status.write('st')

  def testExitCode(self):
    ce = self.CommandExecution({'expect_exit_code': 0})
    with self.Execute(ce) as s:
      s.HandleExit(0)

    with self.assertRaises(assertions.Error):
      with self.Execute(ce) as s:
        s.HandleExit(1)

  def testInput(self):
    ce = self.CommandExecution(
        {'user_input': ['y']},
    )
    with self.Execute(ce):
      result = console_io._GetInput()  # pylint:disable=protected-access
      self.assertEqual('y', result)

  def testApiCall(self):
    ce = self.CommandExecution({
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'foo': 'bar'},
                'body': {
                    'body': 'foo$'
                }
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': ''
            }
        }
    })
    with self.Execute(ce):
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'', body)

    with self.assertRaises(assertions.Error) as context:
      with self.Execute(ce):
        status, body = http.Http().request(
            'https://foo.com', method='POST', body='{"body": "foo1"}',
            headers={'foo': 'bar1'})
        self.assertEqual({'status': '200'}, status)
        self.assertEqual(b'', body)
    self.assertEqual(4, len(context.exception.failures))

  def testAllEvents(self):
    ce = self.CommandExecution(
        {'expect_stdout': 'this'},
        {'expect_stderr': 'is'},
        # TODO(b/79877273): Fix multi line user input.
        {'user_input': ['y']},
        {'expect_stdout': 'a scenario'},
        {'expect_stderr': 'test'},
        {'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'foo': 'bar'},
                'body': {'body': 'foo$'}
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': ''
            }}},
        {'expect_progress_bar': {'message': 'foo'}},
        {'expect_progress_tracker': {'message': 'foo', 'status': 'SUCCESS'}},
        {'expect_stderr': 'Done'},
        {'expect_exit_code': 0},
    )
    with self.Execute(ce) as s:
      log.out.write('this')
      log.status.write('is')
      result = console_io._GetInput()  # pylint:disable=protected-access
      self.assertEqual('y', result)
      log.out.write('a')
      log.out.write(' ')
      log.out.write('scenario')
      log.status.write('te')
      log.status.write('st')
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'', body)
      log.status.write('{"ux": "PROGRESS_BAR", "message": "foo"}')
      log.status.write(
          '{"ux": "PROGRESS_TRACKER", "message": "foo", "status": "SUCCESS"}')
      log.status.write('Done')
      s.HandleExit(0)


class SessionUpdateTests(_SessionTestsBase):
  """Tests that the session can update events correctly.

  The majority of the update tests are actually in the event_tests. This is
  to check that the session level updates are done correctly, such as adding
  and removing entire events.
  """

  def testAddEvents(self):
    data = {'execute_command': {'command': '', 'events': []}}
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      log.out.write('this is stdout\n')
      log.out.write('this is more stdout\n')
      log.status.write('this is stderr\n')
      log.status.write('this is more stderr\n')
    self.assertEqual(
        [{'expect_stdout': 'this is stdout\nthis is more stdout\n'},
         {'expect_stderr': 'this is stderr\nthis is more stderr\n'}],
        s.GetEventSequence())

  def testRemoveEvents(self):
    data = {'execute_command': {'command': '', 'events': [
        {'expect_stdout': 'foo'},
        {'expect_stderr': 'bar'}]}}
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      pass
    self.assertEqual([{}, {}], s.GetEventSequence())

  def testAddRemoveUpdateEvents(self):
    data = {'execute_command': {'command': '', 'events': [
        {'expect_stdout': 'foo'},
        {'expect_stderr': 'bar'},
        {'expect_stdout': 'foo'},
        {'expect_stderr': 'bar'}]}}
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      log.out.write('new foo')
      log.status.write('new bar')
      s.HandleExit(0)
      log.status.write('extra status')
      log.out.write('foo')
    self.assertEqual(
        [{'expect_stdout': 'new foo'},
         {'expect_stderr': 'new bar'},
         {'expect_exit_code': 0},
         {'expect_stderr': 'extra status'},
         {'expect_stdout': 'foo'},
         {}],
        s.GetEventSequence())

  def testAddEventsAtLastKnownScenarioLocation(self):
    data_string = """\
'execute_command':
  'command': ''
  'events':
   - 'expect_stdout': 'foo'
    """
    data = yaml.load(data_string, round_trip=True)
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      log.out.write('foo\n')
      log.status.write('bar\n')
      s.HandleExit(0)
      self.assertEqual(3, len(s.GetEventSequence()))
      self.assertEqual(('4', '5'), s.LastKnownScenarioLocation())


if __name__ == '__main__':
  test_case.main()
