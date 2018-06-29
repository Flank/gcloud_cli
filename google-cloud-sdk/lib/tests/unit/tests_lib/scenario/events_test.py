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

"""Tests for the events module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.scenario import events
from tests.lib.scenario import updates


class EventsTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.parameters([
      ('expect_stdout', events.StdoutEvent, events.EventType.STDOUT),
      ('expect_stderr', events.StderrEvent, events.EventType.STDERR),
      ('expect_exit_code', events.ExitEvent, events.EventType.EXIT),
  ])
  def testSingleValueEvent(self, key, event_class, event_type):
    backing_data = {key: 'original'}
    e = event_class.FromData(backing_data)
    self.assertEqual(event_type, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)
    self.assertEqual([], e.Handle('original'))

    self.assertEqual(1, len(e.Handle('different')))
    e.UpdateContext().Update('different', [update_mode])
    self.assertEqual({key: 'different'}, backing_data)

  @parameterized.parameters([
      ('expect_stdout', events.StdoutEvent, events.EventType.STDOUT, ''),
      ('expect_stderr', events.StderrEvent, events.EventType.STDERR, ''),
      ('expect_exit_code', events.ExitEvent, events.EventType.EXIT, 0),
  ])
  def testSingleValueEventDefaults(self, key, event_class, event_type, default):
    backing_data = {}
    e = event_class.FromData(backing_data)
    self.assertEqual([], e.Handle(default))

    self.assertEqual(1, len(e.Handle('different')))
    e.UpdateContext().Update('different', [e.EventType().UpdateMode()])
    self.assertEqual({key: 'different'}, backing_data)

  @parameterized.parameters([
      ('expect_stdout', events.StdoutEvent, events.EventType.STDOUT),
      ('expect_stderr', events.StderrEvent, events.EventType.STDERR),
      ('expect_exit_code', events.ExitEvent, events.EventType.EXIT),
  ])
  def testSingleValueEventMissing(self, key, event_class, event_type):
    e = event_class.ForMissing(('line', 'col'))
    self.assertEqual(1, len(e.Handle('different')))
    e.UpdateContext().Update('different', [e.EventType().UpdateMode()])
    self.assertEqual({key: 'different'}, e.UpdateContext().BackingData())

  def testUserInputEvent(self):
    backing_data = {'user_input': ['y']}
    e = events.UserInputEvent.FromData(backing_data)
    self.assertEqual(events.EventType.USER_INPUT, e.EventType())
    self.assertEqual(updates.Mode.UX, e.UpdateContext()._update_mode)
    self.assertEqual(['y'], e.Lines())
    self.assertEqual([], e.Handle())

    e = events.UserInputEvent.ForMissing(('line', 'col'))
    self.assertEqual([], e.Lines())
    self.assertEqual(1, len(e.Handle()))

  def testApiCallEvent(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'a': 'b', 'c': 'd'},
                'body': {'ba': 'bb', 'bc': 'bd'},
            },
            'return_response': {
                'headers': {'e': 'f', 'g': 'h'},
                'body': 'response body',
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    self.assertEqual(events.EventType.API_CALL, e.EventType())
    self.assertEqual(updates.Mode.API_REQUESTS, e.UpdateContext()._update_mode)
    self.assertEqual([], e.Handle('https://example.com', 'GET',
                                  {b'a': b'b', b'c': b'd'},
                                  '{"ba": "bb", "bc": "bd"}'))
    self.assertEqual(({'e': 'f', 'g': 'h'}, b'response body'), e.Respond())

    # Headers and body contain 2 assertions each, plus uri and method.
    failures = e.Handle('https://foo.com', 'POST', {b'y': b'z'}, '{"be": "bf"}')
    self.assertEqual(6, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {}},
        backing_data['api_call']['expect_request'])

  def testApiCallEventOrderedRequestParams(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com?a=foo&b=bar&c=foobar',
                'method': 'GET',
                'headers': {'a': 'b', 'c': 'd'},
                'body': {'ba': 'bb', 'bc': 'bd'},
            },
            'return_response': {
                'headers': {'e': 'f', 'g': 'h'},
                'body': 'response body',
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    self.assertEqual([], e.Handle('https://example.com?a=foo&b=bar&c=foobar',
                                  'GET', {b'a': b'b', b'c': b'd'},
                                  '{"ba": "bb", "bc": "bd"}'))
    self.assertEqual([], e.Handle('https://example.com?b=bar&c=foobar&a=foo',
                                  'GET', {b'a': b'b', b'c': b'd'},
                                  '{"ba": "bb", "bc": "bd"}'))
    self.assertEqual([], e.Handle('https://example.com?c=foobar&b=bar&a=foo',
                                  'GET', {b'a': b'b', b'c': b'd'},
                                  '{"ba": "bb", "bc": "bd"}'))

  def testApiCallEventComplexAssertions(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'a': {'is_none': False},
                            'c': {'matches': r'\w'},
                            'e': {'in': ['d', 'e', 'f']},
                           },
                'body': {'ba': 'bb', 'bc': 'bd'},
            },
            'return_response': {
                'headers': {'e': 'f', 'g': 'h'},
                'body': 'response body',
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    self.assertEqual(events.EventType.API_CALL, e.EventType())
    self.assertEqual(updates.Mode.API_REQUESTS, e.UpdateContext()._update_mode)
    self.assertEqual([], e.Handle('https://example.com', 'GET',
                                  {b'a': b'b', b'c': b'd', b'e': b'f'},
                                  '{"ba": "bb", "bc": "bd"}'))
    self.assertEqual(({'e': 'f', 'g': 'h'}, b'response body'), e.Respond())

    # Headers and body contain 2 assertions each, plus uri and method.
    failures = e.Handle('https://foo.com', 'POST', {b'y': b'z'}, '{"be": "bf"}')
    self.assertEqual(7, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {}},
        backing_data['api_call']['expect_request'])

  def testComplexAssertionUpdates(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'a': {'is_none': True},
                            'c': {'matches': r'\w'},
                            'e': {'in': ['d', 'e', 'f']},
                           },
            },
            'return_response': {'headers': {}, 'body': '',}
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    failures = e.Handle('https://foo.com', 'POST',
                        {b'a': b'b', b'c': b' ', b'e': b'1',}, '')
    self.assertEqual(5, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST',
         'headers': {'a': 'b', 'c': ' ', 'e': '1'}},
        backing_data['api_call']['expect_request'])

  def testApiCallEventMissing(self):
    e = events.ApiCallEvent.ForMissing(('line', 'col'))
    self.assertEqual(({'status': '200'}, b''), e.Respond())

    failures = e.Handle('https://foo.com', 'POST', {b'y': b'z'}, '{"be": "bf"}')
    self.assertEqual(3, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {'be': 'bf'}},
        e.UpdateContext().BackingData()['api_call']['expect_request'])


if __name__ == '__main__':
  test_case.main()
