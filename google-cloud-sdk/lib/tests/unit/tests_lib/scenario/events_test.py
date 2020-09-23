# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

import json

from apitools.base.py import http_wrapper

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.scenario import events
from tests.lib.scenario import reference_resolver
from tests.lib.scenario import updates

from six.moves import http_client as httplib


class RequestTest(test_case.TestCase):

  def testFromApitoolsRequest(self):
    apitools_request = http_wrapper.Request(
        url='url', http_method='POST', headers={'header': 'val'}, body='test')
    request = events.Request.FromApitoolsRequest(apitools_request)
    self.assertEqual(request.uri, apitools_request.url)
    self.assertEqual(request.method, apitools_request.http_method)
    self.assertEqual(request.headers, apitools_request.headers)
    self.assertEqual(request.body, apitools_request.body)


class ResponseTest(test_case.TestCase):

  def testFromApitoolsResponse(self):
    apitools_response = http_wrapper.Response(
        {'status': httplib.OK, 'header': 'val'}, 'data', 'uri')
    apitools_headers = dict(apitools_response.info)
    apitools_headers.pop('status')
    response = events.Response.FromApitoolsResponse(apitools_response)
    self.assertEqual(response.status, apitools_response.status_code)
    self.assertEqual(response.headers, apitools_headers)
    self.assertEqual(response.body, apitools_response.content)


class EventsTest(test_case.TestCase, parameterized.TestCase):

  @parameterized.parameters([
      ('expect_stdout', events.StdoutEvent, events.EventType.STDOUT),
      ('expect_stderr', events.StderrEvent, events.EventType.STDERR),
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
  ])
  def testSingleValueEventMissing(self, key, event_class, event_type):
    e = event_class.ForMissing(('line', 'col'))
    self.assertEqual(1, len(e.Handle('different')))
    e.UpdateContext().Update('different', [e.EventType().UpdateMode()])
    self.assertEqual({key: 'different'}, e.UpdateContext().BackingData())

  def testExitEvent(self):
    backing_data = {'expect_exit': {'code': 0}}
    e = events.ExitEvent.FromData(backing_data)
    self.assertEqual(events.EventType.EXIT, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)

    self.assertEqual([], e.Handle(None))
    self.assertEqual(2, len(e.Handle(Exception('foo'))))

    backing_data = {'expect_exit': {'code': 0, 'message': None}}
    e = events.ExitEvent.FromData(backing_data)
    failures = e.Handle(Exception('foo'))
    self.assertEqual(2, len(failures))
    for f in failures:
      f.Update([update_mode])
    self.assertEqual({'expect_exit': {'code': 1, 'message': 'foo'}},
                     backing_data)

  def testExitEventWithTraceback(self):
    backing_data = {'expect_exit': {'code': 0, 'message': None}}
    e = events.ExitEvent.FromData(backing_data)
    failures = e.HandleReturnCode(1, 'foo', details='traceback details')
    self.assertEqual(2, len(failures))
    self.assertEqual(failures[1].details, 'traceback details')

  def testExitEventMissing(self):
    e = events.ExitEvent.ForMissing(('line', 'col'))
    self.assertEqual(events.EventType.EXIT, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)

    self.assertEqual(1, len(e.Handle(None)))
    failures = e.Handle(Exception('foo'))
    self.assertEqual(2, len(failures))
    for f in failures:
      f.Update([update_mode])
    self.assertEqual({'expect_exit': {'code': 1, 'message': 'foo'}},
                     e.UpdateContext().BackingData())

  def testFileWrittenEvent(self):
    backing_data = {
        'expect_file_written': {'path': 'foo.txt', 'contents': 'asdf'}}
    e = events.FileWrittenEvent.FromData(backing_data)
    self.assertEqual(events.EventType.FILE_WRITTEN, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)

    self.assertEqual([], e.Handle('foo.txt', contents='asdf', private=False))
    self.assertEqual(
        1, len(e.Handle('bar.txt', contents='asdf', private=False)))
    self.assertEqual(
        1, len(e.Handle('foo.txt', contents='qwerty', private=False)))
    self.assertEqual(
        1, len(e.Handle('foo.txt', contents='asdf', private=True)))
    self.assertEqual(
        2, len(e.Handle('foo.txt', contents=b'asdf', private=False)))

    failures = e.Handle('bar.txt', contents=b'qwerty', private=True)
    for f in failures:
      f.Update([update_mode])
    self.assertEqual(
        {'expect_file_written':
             {'path': 'bar.txt', 'binary_contents': b'qwerty',
              'is_private': True}},
        backing_data)

  def testFileWrittenEventMissing(self):
    e = events.FileWrittenEvent.ForMissing(('line', 'col'))
    self.assertEqual(
        2, len(e.Handle('bar.txt', contents='qwerty', private=False)))
    failures = e.Handle('bar.txt', contents='qwerty', private=True)
    self.assertEqual(3, len(failures))
    for f in failures:
      f.Update([e.EventType().UpdateMode()])
    self.assertEqual(
        {'expect_file_written':
             {'path': 'bar.txt', 'contents': 'qwerty', 'is_private': True}},
        e.UpdateContext().BackingData())

  @parameterized.parameters([
      ('expect_prompt_continue', events.PromptContinueEvent,
       events.EventType.PROMPT_CONTINUE),
      ('expect_prompt_choice', events.PromptChoiceEvent,
       events.EventType.PROMPT_CHOICE),
  ])
  def testPromptEvent(self, key, event_class, event_type):
    backing_data = {key: {'message': 'foo', 'user_input': 'y'}}
    e = event_class.FromData(backing_data)
    self.assertEqual(event_type, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)
    self.assertEqual([], e.Handle(
        {'ux': event_type.name, 'prompt_string': 'ps', 'message': 'foo'}))

    failures = e.Handle(
        {'ux': event_type.name, 'prompt_string': 'ps', 'message': 'diff'})
    self.assertEqual(1, len(failures))
    for f in failures:
      f.Update([update_mode])
    self.assertEqual({key: {'message': 'diff', 'user_input': 'y'}},
                     backing_data)

  @parameterized.parameters([
      ('expect_prompt_continue', events.PromptContinueEvent,
       events.EventType.PROMPT_CONTINUE),
      ('expect_prompt_choice', events.PromptChoiceEvent,
       events.EventType.PROMPT_CHOICE),
  ])
  def testPromptEventMissing(self, key, event_class, event_type):
    e = event_class.ForMissing(('line', 'col'))
    failures = e.Handle(
        {'ux': event_type.name, 'prompt_string': 'ps', 'message': 'foo'})
    self.assertEqual(3, len(failures))
    for f in failures:
      f.Update([e.EventType().UpdateMode()])
    self.assertEqual(
        {key: {'message': 'foo', 'prompt_string': 'ps',
               'user_input': event_class.DefaultValue()}},
        e.UpdateContext().BackingData())

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
                'uri': {'equals': 'https://example.com'},
                'method': 'GET',
                'headers': {'a': 'b', 'c': 'd'},
                'body': {'json': {'ba': 'bb', 'bc': 'bd'}},
            },
            'expect_response': {
                'headers': {'e': 'f'},
                'body': {'text': {'matches': 'res.*'}},
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
    request = events.Request('https://example.com', 'GET',
                             {b'a': b'b', b'c': b'd'},
                             '{"ba": "bb", "bc": "bd"}')
    self.assertEqual([], e.Handle(request))
    response = e.GetResponse()
    self.assertEqual(events.Response(httplib.OK,
                                     {'e': 'f', 'g': 'h'},
                                     'response body'), response)
    self.assertEqual([], e.HandleResponse(response, None))

    # Headers and body contain 2 assertions each, plus uri and method.
    request = events.Request('https://foo.com', 'POST',
                             {b'y': b'z'}, '{"be": "bf"}')
    failures = e.Handle(request)
    self.assertEqual(6, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {'json': {}}},
        backing_data['api_call']['expect_request'])

    failures = e.HandleResponse(
        events.Response(httplib.OK, {'e': 'z'}, b'blah'), None)
    self.assertEqual(2, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'headers': {'e': 'z'}, 'body': {'text': 'blah'}},
        backing_data['api_call']['expect_response'])

    response = events.Response(httplib.OK, {'e': 'z'}, 'blah')
    failures = e.UpdateResponsePayload(response)
    self.assertEqual(1, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_RESPONSE_PAYLOADS])
    self.assertEqual(
        {'headers': {'e': 'z'}, 'body': 'blah', 'status': httplib.OK},
        backing_data['api_call']['return_response'])

  def testApiCallEventAddRefExtraction(self):
    backing_data = {
        'api_call': {
            'poll_operation': False,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': {
                    'kind': 'sql#operation',
                    'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5',
                    'status': 'DONE',
                }
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    response = e.GetResponse()
    failures = e.HandleResponse(
        response, reference_resolver.ResourceReferenceResolver(),
        generate_extras=True)
    self.assertEqual(1, len(failures))
    failures[0].Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'extract_references': [{'field': 'name', 'reference': 'operation'}],
         'body': {'json': {}}},
        backing_data['api_call']['expect_response'])

  def testResponseExtractRef(self):
    e = events.ResponseAssertion.FromCallData({
        'expect_response': {
            'extract_references': [
                {'field': 'name', 'reference': 'operation'},
                {'field': 'name', 'reference': 'operation-base',
                 'modifiers': {'basename': True}}
            ],
        },
    })

    rrr = reference_resolver.ResourceReferenceResolver()
    e.ExtractReferences(rrr, '{"name": "foo/bar/my-op"}')
    self.assertEqual(rrr._extracted_ids,
                     {'operation': 'foo/bar/my-op', 'operation-base': 'my-op'})

  def testApiCallEventAddOptional(self):
    backing_data = {
        'api_call': {
            'poll_operation': False,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': {
                    'kind': 'sql#operation',
                    'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5',
                    'status': 'PENDING',
                }
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    # Setting the id as previous extracted means that this is a polling event
    # not an op creation event.
    rrr = reference_resolver.ResourceReferenceResolver()
    rrr.SetExtractedId('operation', '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5')
    response = e.GetResponse()
    failures = e.HandleResponse(response, rrr, generate_extras=True)
    self.assertEqual(2, len(failures))
    failures[0].Update([updates.Mode.API_REQUESTS])
    failures[1].Update([updates.Mode.API_REQUESTS])
    self.assertTrue(backing_data['api_call']['optional'])
    self.assertEqual({'body': {'json': {'status': 'PENDING'}}},
                     backing_data['api_call']['expect_response'])

  def testApiCallEventAddPollOperationOld(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': {
                    'kind': 'sql#operation',
                    'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5',
                    'status': 'PENDING',
                }
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    response = e.GetResponse()
    failures = e.HandleResponse(
        response,
        resource_ref_resolver=reference_resolver.ResourceReferenceResolver(),
        generate_extras=True)
    self.assertEqual(1, len(failures))
    failures[0].Update([updates.Mode.API_REQUESTS])
    self.assertTrue(backing_data['api_call']['poll_operation'])

  @parameterized.parameters([
      ({'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5'}, False),
      ({'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5', 'done': False}, True),
      ({'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5',
        'metadata': {'@type': 'SomeServiceOperation'}}, True),
      ({'name': '460b8ba8-34a9-4590-a3ca-7ce5b74cb8d5',
        'metadata': {'@type': 'foo'}}, False),
  ])
  def testApiCallEventAddPollOperationNew(self, body, is_op):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': body
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    response = e.GetResponse()
    failures = e.HandleResponse(
        response,
        resource_ref_resolver=reference_resolver.ResourceReferenceResolver(),
        generate_extras=True)

    if is_op:
      self.assertEqual(1, len(failures))
      failures[0].Update([updates.Mode.API_REQUESTS])
      self.assertTrue(backing_data['api_call']['poll_operation'])
    else:
      self.assertEqual(0, len(failures))
      self.assertNotIn('poll_operation', backing_data['api_call'])

  def testApiCallPollOperationForcesOperationHandling(self):
    backing_data = {
        'api_call': {
            'poll_operation': True,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': {'name': 'foo/bar/my-op'},
            }
        }
    }
    rrr = reference_resolver.ResourceReferenceResolver()
    e = events.ApiCallEvent.FromData(backing_data)
    response = e.GetResponse()
    failures = e.HandleResponse(
        response,
        resource_ref_resolver=rrr,
        generate_extras=True)

    self.assertEqual(0, len(failures))
    self.assertEqual(rrr._extracted_ids,
                     {'operation': 'foo/bar/my-op',
                      'operation-basename': 'my-op'})

  def testApiCallEventNoAddRefExtraction(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'body': {'foo': 'bar'},
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    response = e.GetResponse()
    self.assertEqual([], e.HandleResponse(response, None))

  def testApiCallEventOrderedRequestParams(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com?a=foo&b=bar&c=foobar',
                'method': 'GET',
                'headers': {'a': 'b', 'c': 'd'},
                'body': {'json': {'ba': 'bb', 'bc': 'bd'}},
            },
            'return_response': {
                'headers': {'e': 'f', 'g': 'h'},
                'body': 'response body',
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    request = events.Request('https://example.com?a=foo&b=bar&c=foobar',
                             'GET', {b'a': b'b', b'c': b'd'},
                             '{"ba": "bb", "bc": "bd"}')
    self.assertEqual([], e.Handle(request))
    request = events.Request('https://example.com?b=bar&c=foobar&a=foo',
                             'GET', {b'a': b'b', b'c': b'd'},
                             '{"ba": "bb", "bc": "bd"}')
    self.assertEqual([], e.Handle(request))
    request = events.Request('https://example.com?c=foobar&b=bar&a=foo',
                             'GET', {b'a': b'b', b'c': b'd'},
                             '{"ba": "bb", "bc": "bd"}')
    self.assertEqual([], e.Handle(request))

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
                'body': {'json': {'ba': 'bb', 'bc': 'bd'}},
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
    request = events.Request('https://example.com', 'GET',
                             {b'a': b'b', b'c': b'd', b'e': b'f'},
                             '{"ba": "bb", "bc": "bd"}')
    self.assertEqual([], e.Handle(request))
    self.assertEqual(events.Response(
        httplib.OK, {'e': 'f', 'g': 'h'}, 'response body'), e.GetResponse())

    # Headers and body contain 2 assertions each, plus uri and method.
    request = events.Request('https://foo.com', 'POST',
                             {b'y': b'z'}, '{"be": "bf"}')
    failures = e.Handle(request)
    self.assertEqual(7, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual({
        'uri': 'https://foo.com',
        'method': 'POST',
        'headers': {},
        'body': {'json': {}}
    }, backing_data['api_call']['expect_request'])

  @parameterized.parameters(
      # Present text assertion matches correctly.
      ({'body': {'text': 'asdf'}}, 'asdf', {'text': 'asdf'}, False),
      # Present text assertion doesn't match.
      ({'body': {'text': 'asdf'}}, 'qwerty', {'text': 'qwerty'}, True),
      # Present json assertion matches correctly.
      ({'body': {'json': {'foo': 'bar'}}}, '{"foo": "bar"}',
       {'json': {'foo': 'bar'}}, False),
      # Present json assertion doesn't match.
      ({'body': {'json': {'foo': 'bar'}}}, '{"foo": "baz"}',
       {'json': {'foo': 'baz'}}, True),
      # Present text and json assertions match.
      ({'body': {'json': {'foo': 'bar'}, 'text': '{"foo": "bar"}'}},
       '{"foo": "bar"}', {'json': {'foo': 'bar'}, 'text': '{"foo": "bar"}'},
       False),
      # Present text and json assertions don't match.
      ({'body': {'json': {'foo': 'bar'}, 'text': '{"foo": "bar"}'}},
       '{"foo": "baz"}', {'json': {'foo': 'baz'}, 'text': '{"foo": "baz"}'},
       True),
      # Explicitly None body matches actual None body.
      ({'body': None}, None, None, False),
      # Explicitly None body matches empty string body.
      ({'body': None}, '', None, False),
      # Explicitly None gets updated with text value.
      ({'body': None}, 'asdf', {'text': 'asdf'}, True),
      # Explicitly None gets updated with json value.
      ({'body': None}, '{"foo": "bar"}', {'json': {'foo': 'bar'}}, True),
      # Empty assertions is treated like missing body.
      ({'body': {}}, None, None, True),
      # Empty assertions is treated like missing body.
      ({'body': {}}, '', None, True),
      # Explicitly None gets updated with text value.
      ({'body': {}}, 'asdf', {'text': 'asdf'}, True),
      # Explicitly None gets updated with json value.
      ({'body': {}}, '{"foo": "bar"}', {'json': {'foo': 'bar'}}, True),
      # Missing assertion updates to None
      ({}, None, None, True),
      # Missing assertion gets updated with text value.
      ({}, 'asdf', {'text': 'asdf'}, True),
      # Missing assertion gets updated with json value.
      ({}, '{"foo": "bar"}', {'json': {'foo': 'bar'}}, True),
  )
  def testApiCallBodies(self, assertion, actual, new, has_failures):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com', 'method': 'GET', 'headers': {}}}}
    backing_data['api_call']['expect_request'].update(assertion)

    e = events.ApiCallEvent.FromData(backing_data)
    request = events.Request('https://example.com', 'GET', {}, actual)
    failures = e.Handle(request)
    self.assertEqual(bool(failures), has_failures)
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(new, backing_data['api_call']['expect_request']['body'])

  @parameterized.parameters(
      ({'headers': {'status': '200', 'e': 'f'}},
       {'headers': {'status': '200', 'e': 'f'}}),
      ({'headers': {'status': '200', 'e': 'f'}},
       {'headers': {'status': httplib.OK, 'e': 'f'}}),
      ({'headers': {'status': '200', 'e': 'f'}},
       {'status': httplib.OK, 'headers': {'e': 'f'}}),

      ({'headers': {'status': httplib.OK, 'e': 'f'}},
       {'headers': {'status': '200', 'e': 'f'}}),
      ({'headers': {'status': httplib.OK, 'e': 'f'}},
       {'headers': {'status': httplib.OK, 'e': 'f'}}),
      ({'headers': {'status': httplib.OK, 'e': 'f'}},
       {'status': httplib.OK, 'headers': {'e': 'f'}}),

      ({'status': httplib.OK, 'headers': {'e': 'f'}},
       {'headers': {'status': '200', 'e': 'f'}}),
      ({'status': httplib.OK, 'headers': {'e': 'f'}},
       {'headers': {'status': httplib.OK, 'e': 'f'}}),
      ({'status': httplib.OK, 'headers': {'e': 'f'}},
       {'status': httplib.OK, 'headers': {'e': 'f'}}),

  )
  def testApiCallResponseAssertions(self, return_response, expect_response):
    return_response['body'] = 'response body'
    expect_response['body'] = {'text': {'matches': 'res.*'}}
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': {'equals': 'https://example.com'},
                'method': 'GET',
                'headers': {'a': 'b'},
                'body': {'json': {'ba': 'bb'}},
            },
            'return_response': return_response,
            'expect_response': expect_response
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    self.assertEqual(events.EventType.API_CALL, e.EventType())
    self.assertEqual(updates.Mode.API_REQUESTS, e.UpdateContext()._update_mode)
    request = events.Request('https://example.com', 'GET',
                             {b'a': b'b'},
                             '{"ba": "bb"}')
    request_failures = e.Handle(request)
    self.assertEqual([], request_failures)
    response = e.GetResponse()
    self.assertEqual(events.Response(httplib.OK,
                                     {'e': 'f'},
                                     'response body'), response)
    response_failures = e.HandleResponse(response, None)
    self.assertEqual([], response_failures)

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
                'body': {'text': {'matches': 'q.*'}},
            },
            'return_response': {'headers': {}, 'body': '',}
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    request = events.Request('https://foo.com', 'POST',
                             {b'a': b'b', b'c': b' ', b'e': b'1',}, 'asdf')
    failures = e.Handle(request)
    self.assertEqual(6, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST',
         'headers': {'a': 'b', 'c': ' ', 'e': '1'}, 'body': {'text': 'asdf'}},
        backing_data['api_call']['expect_request'])

  def testApiCallEventMissing(self):
    e = events.ApiCallEvent.ForMissing(('line', 'col'))
    self.assertEqual(events.Response(httplib.OK, {}, ''), e.GetResponse())

    request = events.Request('https://foo.com', 'POST', {b'y': b'z'},
                             '{"be": "bf"}')
    failures = e.Handle(request)
    self.assertEqual(4, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {'json': {'be': 'bf'}}},
        e.UpdateContext().BackingData()['api_call']['expect_request'])

  def testApiCallEventMissingText(self):
    e = events.ApiCallEvent.ForMissing(('line', 'col'))
    self.assertEqual(events.Response(httplib.OK, {}, ''), e.GetResponse())

    request = events.Request('https://foo.com', 'POST', {b'y': b'z'}, 'asdf')
    failures = e.Handle(request)
    self.assertEqual(4, len(failures))
    for f in failures:
      f.Update([updates.Mode.API_REQUESTS])
    self.assertEqual(
        {'uri': 'https://foo.com', 'method': 'POST', 'headers': {},
         'body': {'text': 'asdf'}},  # Generates the text assertion.
        e.UpdateContext().BackingData()['api_call']['expect_request'])

  def testUpdateResponsePayload(self):
    backing_data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {},
                'body': None,
            },
            'return_response': {
                'omit_fields': ['bad_field'],
                'headers': {},
                'body': '',
            }
        }
    }
    e = events.ApiCallEvent.FromData(backing_data)
    response = events.Response(
        httplib.OK, {}, json.dumps({
            'status': 'RUNNING', 'progress': '0', 'bad_field': 'asdf'
        }))
    failures = e.UpdateResponsePayload(response)
    self.assertEqual(1, len(failures))
    failures[0].Update([updates.Mode.API_RESPONSE_PAYLOADS])
    self.assertEqual(
        {'status': httplib.OK,
         'headers': {},
         'body': {'status': 'RUNNING', 'progress': '0'},
         'omit_fields': ['bad_field']},
        e.UpdateContext().BackingData()['api_call']['return_response'])

  def testProgressTrackerEvent(self):
    backing_data = {'expect_progress_tracker': {'message': 'foo',
                                                'status': 'SUCCESS'}}
    e = events.ProgressTrackerEvent.FromData(backing_data)
    self.assertEqual(events.EventType.PROGRESS_TRACKER, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)

    self.assertEqual([], e.Handle({'ux': 'PROGRESS_TRACKER',
                                   'message': 'foo',
                                   'status': 'SUCCESS'}))

    failures = e.Handle({'ux': 'PROGRESS_TRACKER',
                         'message': 'bar',
                         'status': 'FAILED'})
    self.assertEqual(2, len(failures))
    for f in failures:
      f.Update([update_mode])
    self.assertEqual({'expect_progress_tracker': {'message': 'bar',
                                                  'status': 'FAILED'}},
                     backing_data)

  def testProgressTrackerEventMissing(self):
    e = events.ProgressTrackerEvent.ForMissing(('line', 'col'))
    failures = e.Handle({'ux': 'PROGRESS_TRACKER',
                         'message': 'bar',
                         'status': 'FAILED'})
    self.assertEqual(2, len(failures))
    for f in failures:
      f.Update([e.EventType().UpdateMode()])
    self.assertEqual({'expect_progress_tracker': {'message': 'bar',
                                                  'status': 'FAILED'}},
                     e.UpdateContext().BackingData())

  def testProgressBarEvent(self):
    backing_data = {'expect_progress_bar': {'message': 'foo'}}
    e = events.ProgressBarEvent.FromData(backing_data)
    self.assertEqual(events.EventType.PROGRESS_BAR, e.EventType())
    update_mode = e.EventType().UpdateMode()
    self.assertEqual(update_mode, e.UpdateContext()._update_mode)

    self.assertEqual([], e.Handle({'ux': 'PROGRESS_BAR', 'message': 'foo'}))

    failures = e.Handle({'ux': 'PROGRESS_BAR', 'message': 'bar'})
    self.assertEqual(1, len(failures))
    for f in failures:
      f.Update([update_mode])
    self.assertEqual({'expect_progress_bar': {'message': 'bar'}},
                     backing_data)

  def testProgressBarEventMissing(self):
    e = events.ProgressBarEvent.ForMissing(('line', 'col'))

    failures = e.Handle({'ux': 'PROGRESS_BAR', 'message': 'bar'})
    self.assertEqual(1, len(failures))
    for f in failures:
      f.Update([e.EventType().UpdateMode()])
    self.assertEqual({'expect_progress_bar': {'message': 'bar'}},
                     e.UpdateContext().BackingData())


if __name__ == '__main__':
  test_case.main()
