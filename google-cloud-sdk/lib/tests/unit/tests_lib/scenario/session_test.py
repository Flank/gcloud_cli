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

"""Tests for the session module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import json
import os
import re

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.scenario import assertions
from tests.lib.scenario import reference_resolver
from tests.lib.scenario import schema
from tests.lib.scenario import session
from tests.lib.scenario import test_base
from tests.lib.scenario import updates


class _SessionTestsBase(sdk_test_base.WithOutputCapture,
                        sdk_test_base.WithTempCWD,
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
  def Execute(self, ce, execution_mode=session.ExecutionMode.LOCAL,
              update_modes=None, ignore_api_calls=False, rrr=None):
    with assertions.FailureCollector(
        update_modes=update_modes or []) as failures:
      if not rrr:
        rrr = reference_resolver.ResourceReferenceResolver()
      with session.Session(
          ce._LoadEvents(rrr), failures, self.stream_mocker, execution_mode,
          ignore_api_calls, rrr) as s:
        yield s

  def ToJson(self, value):
    return json.dumps(value).encode('utf8')

  def FromJson(self, value):
    return json.loads(value.decode('utf8'))


class SessionTests(_SessionTestsBase):
  """Tests of session event handling."""

  def testNotEnoughEvents(self):
    ce = self.CommandExecution()
    with self.assertRaises(assertions.Error):
      with self.Execute(ce) as s:
        log.status.write('foo')
    # Ensure the event got added.
    self.assertEqual(2, len(s.GetEventSequence()))

  def testTooManyEvents(self):
    ce = self.CommandExecution(
        {'expect_stderr': 'foo'},
        {'expect_stderr': 'bar'},
        {'expect_exit': {'code': 0}})
    with self.assertRaises(assertions.Error):
      with self.Execute(ce) as s:
        pass
    self.assertEqual(4, len(s.GetEventSequence()))

  def testJustStderr(self):
    ce = self.CommandExecution({'expect_stderr': 'foo'},
                               {'expect_exit': {'code': 0}})
    with self.Execute(ce):
      log.status.write('foo')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        log.status.write('bar')

  def testJustStdout(self):
    ce = self.CommandExecution({'expect_stdout': 'foo'},
                               {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      log.out.write('foo')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        log.out.write('bar')

  def testJustUxEvent(self):
    ce = self.CommandExecution({'expect_progress_bar': {'message': 'foo'}},
                               {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      log.status.write('{"ux": "PROGRESS_BAR", "message": "foo"}')

    with self.assertRaises(session.Error):
      with self.Execute(ce):
        log.status.write('{"ux": "PROGRESS_BAR", message: foo')

  def testStagedProgressTrackerUxEvent(self):
    ce = self.CommandExecution(
        {'expect_staged_progress_tracker': {
            'message': 'tracker',
            'status': 'FAILURE',
            'stages': ['Hello World...', 'Goodbye cruel world...'],
            'failed_stage': 'this failed'}},
        {'expect_exit': {'code': 1}},
    )
    with self.Execute(ce):
      stages = [
          progress_tracker.Stage('Hello World...', key='a'),
          progress_tracker.Stage('Goodbye cruel world...', key='b'),
          progress_tracker.Stage('this failed', key='c'),
      ]
      with progress_tracker.StagedProgressTracker(
          'tracker', stages, autotick=False) as spt:
        spt.StartStage('a')
        spt.CompleteStage('a')
        spt.StartStage('b')
        spt.CompleteStage('b')
        spt.StartStage('c')
        spt.FailStage('c', ValueError)

  def testJustFileWriteEvent(self):
    ce = self.CommandExecution(
        {'expect_file_written': {'path': 'foo.txt', 'contents': 'asdf'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      files.WriteFileContents('foo.txt', 'asdf')
      # File writes to the config directory or under temp are not captured by
      # the scenario framework and do not require assertions to be present in
      # the scenario..
      files.WriteFileContents(
          os.path.join(config.Paths().global_config_dir, 'bar.txt'), 'asdf')
      with files.TemporaryDirectory() as t:
        files.WriteFileContents(os.path.join(t, 'baz.txt'), '1234')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        files.WriteBinaryFileContents('foo.txt', b'asdf')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        files.WriteFileContents('foo.txt', 'qwerty')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        files.WriteFileContents('bar.txt', 'asdf')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        files.WriteFileContents('foo.txt', 'asdf', private=True)

    with self.assertRaisesRegex(
        session.Error,
        r'Command is attempting to write file outside of current working '
        r'directory: \[{}\]'.format(
            re.escape(os.path.abspath('/asdf/foo.txt')))):
      with self.Execute(ce):
        files.WriteFileContents('/asdf/foo.txt', 'asdf', create_path=False)

  def testJustBinaryFileWriteEvent(self):
    ce = self.CommandExecution(
        {'expect_file_written': {'path': 'foo.txt',
                                 'binary_contents': b'asdf'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      files.WriteBinaryFileContents('foo.txt', b'asdf')

    with self.assertRaises(assertions.Error):
      with self.Execute(ce):
        files.WriteFileContents('foo.txt', 'asdf')

  def testJustHomeFileWriteEvent(self):
    ce = self.CommandExecution(
        {'expect_file_written': {'path': '~/foo.txt', 'contents': 'asdf'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      files.WriteFileContents(files.ExpandHomeDir('~/foo.txt'), 'asdf')

  def testJustPromptContinueEvent(self):
    ce = self.CommandExecution(
        {'expect_prompt_continue': {'message': 'foo', 'user_input': 'y'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      answer = console_io.PromptContinue(message='foo')
      self.assertTrue(answer)

  def testJustPromptChoiceEvent(self):
    ce = self.CommandExecution(
        {'expect_prompt_choice': {'choices': ['a', 'b', 'c'],
                                  'message': 'foo', 'user_input': '2'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      answer = console_io.PromptChoice(['a', 'b', 'c'], message='foo')
      self.assertEqual(answer, 1)

  def testJustPromptResponseEvent(self):
    ce = self.CommandExecution(
        {'expect_prompt_response': {'message': 'foo', 'user_input': 'bar'}},
        {'expect_exit': {'code': 0}},)
    with self.Execute(ce):
      answer = console_io.PromptResponse(message='foo')
      self.assertEqual('bar', answer)

  def testOutputMixAndAggregation(self):
    ce = self.CommandExecution(
        {'expect_stdout': 'this'},
        {'expect_stderr': 'is'},
        {'expect_stdout': 'a scenario'},
        {'expect_stderr': 'test'},
        {'expect_exit': {'code': 0}},
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
    ce = self.CommandExecution({'expect_exit': {'code': 1, 'message': 'foo'}})
    with self.Execute(ce):
      calliope_exceptions._Exit(Exception('foo'))

  def testInput(self):
    ce = self.CommandExecution(
        {'user_input': ['y']},
        {'expect_exit': {'code': 0}},
    )
    with self.Execute(ce):
      result = console_io._GetInput()  # pylint:disable=protected-access
      self.assertEqual('y', result)

  def testApiCall(self):
    data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'foo': 'bar'},
                'body': {
                    'json': {'body': 'foo'}
                }
            },
            'expect_response': {
                'headers': {'status': '200'},
                'body': None,
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': ''
            }
        }}
    ce = self.CommandExecution(data, {'expect_exit': {'code': 0}})
    with self.Execute(ce):
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'', body)

    # Request assertion failure.
    with self.assertRaises(assertions.Error) as context:
      with self.Execute(ce):
        status, body = http.Http().request(
            'https://foo.com', method='POST', body='{"body": "foo1"}',
            headers={'foo': 'bar1'})
        self.assertEqual({'status': '200'}, status)
        self.assertEqual(b'', body)
    self.assertEqual(4, len(context.exception.failures))

    # Response assertion failure.
    data['api_call']['return_response']['headers']['status'] = '404'
    ce = self.CommandExecution(data, {'expect_exit': {'code': 0}})
    with self.assertRaises(assertions.Error) as context:
      with self.Execute(ce):
        status, body = http.Http().request(
            'https://example.com', method='GET', body='{"body": "foo"}',
            headers={'foo': 'bar'})
        self.assertEqual({'status': '200'}, status)
        self.assertEqual(b'', body)
    self.assertEqual(3, len(context.exception.failures))

  def testIgnoreApiCalls(self):
    request_mock = self.StartPatch('httplib2.Http.request')
    response = {'status': 'RUNNING', 'progress': '0'}
    request_mock.return_value = ({'status': '200'}, self.ToJson(response))

    ce = self.CommandExecution({'expect_stdout': 'foo'},
                               {'expect_exit': {'code': 0}},)
    with self.Execute(ce, ignore_api_calls=True):
      log.out.write('foo')
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('RUNNING', self.FromJson(body)['status'])
      self.assertEqual('0', self.FromJson(body)['progress'])

  def testRepeatableAPICall(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    running = {
        'api_call': {
            'repeatable': True,
            'optional': True,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'json': {'status': 'RUNNING'}},
            }
        }
    }
    done = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'json': {'status': 'DONE'}},
            }
        }
    }

    ce = self.CommandExecution(
        running, done, {'expect_exit': {'code': 0}})
    response = {'status': 'RUNNING', 'progress': '0'}
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE):
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('RUNNING', self.FromJson(body)['status'])
      self.assertEqual('0', self.FromJson(body)['progress'])

      response['progress'] = '50'
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('RUNNING', self.FromJson(body)['status'])
      self.assertEqual('50', self.FromJson(body)['progress'])

      response['status'] = 'DONE'
      response['progress'] = '100'
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('DONE', self.FromJson(body)['status'])
      self.assertEqual('100', self.FromJson(body)['progress'])

  def testOptionalAPICallRemote(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    first_event = {'expect_stderr': 'err'}
    optional_call = {
        'api_call': {
            'optional': True,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'text': 'PENDING'},
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'PENDING'
            }
        }
    }
    repeated_call = {
        'api_call': {
            'optional': True,
            'repeatable': True,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'text': 'RUNNING'},
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'RUNNING'
            }
        }
    }
    required_call = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'text': 'DONE'},
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'DONE'
            }
        }
    }
    ce = self.CommandExecution(
        first_event, optional_call, repeated_call, required_call,
        {'expect_exit': {'code': 0}})
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE):
      log.status.write('err')
      request_mock.return_value = ({'status': '200'}, b'RUNNING')
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'RUNNING', body)
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'RUNNING', body)
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'RUNNING', body)
      request_mock.return_value = ({'status': '200'}, b'DONE')
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'DONE', body)

  def testOptionalAPICallLocal(self):
    first_event = {'expect_stderr': 'err'}
    call1 = {
        'api_call': {
            'optional': True,
            'repeatable': False,
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'text': 'PENDING'},
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'PENDING'
            }
        }
    }
    call2 = {
        'api_call': {
            'optional': True,
            'expect_request': {
                'uri': 'https://foo.com',
                'method': 'GET',
                'body': None
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'foo'
            }
        }
    }
    call3 = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'text': 'DONE'},
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': 'DONE'
            }
        }
    }
    ce = self.CommandExecution(first_event, call1, call2, call3,
                               {'expect_exit': {'code': 0}})
    with self.Execute(ce, execution_mode=session.ExecutionMode.LOCAL):
      log.status.write('err')
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'PENDING', body)

      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'DONE', body)

  def testAPICallOperationLocal(self):
    op_body = {
        'name': 'operation-12345',
        'kind': 'foo#operation',
        'operationType': 'CREATE',
        'status': 'PENDING',
    }
    create_call = {
        'api_call': {
            'poll_operation': True,
            'expect_request': {
                'uri': 'https://example.com/create',
                'method': 'GET',
                'body': None
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': dict(op_body)
            }
        }
    }
    ce = self.CommandExecution(
        create_call,
        {'expect_stderr': 'Polling operation [operation-12345]\n'},
        {'expect_exit': {'code': 0}})

    rrr = reference_resolver.ResourceReferenceResolver()
    with self.Execute(ce, execution_mode=session.ExecutionMode.LOCAL, rrr=rrr):
      status, body = http.Http().request(
          'https://example.com/create', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      self.assertEqual(rrr._extracted_ids['operation'], 'operation-12345')
      log.status.Print('Polling operation [operation-12345]')

      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      op_body['status'] = 'RUNNING'
      self.assertEqual(op_body, self.FromJson(body))

      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      op_body['status'] = 'DONE'
      self.assertEqual(op_body, self.FromJson(body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

  def testAPICallOperation(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    op_body = {
        'name': 'operation-12345',
        'kind': 'foo#operation',
        'operationType': 'CREATE',
        'status': 'PENDING',
    }
    create_call = {
        'api_call': {
            'poll_operation': True,
            'expect_request': {
                'uri': 'https://example.com/create',
                'method': 'GET',
                'body': None
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': dict(op_body)
            }
        }
    }

    ce = self.CommandExecution(
        create_call,
        {'expect_stderr': 'Polling operation [operation-12345]\n'},
        {'expect_exit': {'code': 0}})

    rrr = reference_resolver.ResourceReferenceResolver()
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE, rrr=rrr):
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/create', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      self.assertEqual(rrr._extracted_ids['operation'], 'operation-12345')
      log.status.Print('Polling operation [operation-12345]')

      op_body['status'] = 'RUNNING'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))
      # Running again.
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      op_body['status'] = 'DONE'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))
      # Running again.
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

  def testAPICallOperationWithWait(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    op_body = {
        'name': 'operation-12345',
        'kind': 'foo#operation',
        'operationType': 'CREATE',
        'status': 'PENDING',
    }
    create_call = {
        'api_call': {
            'poll_operation': True,
            'expect_request': {
                'uri': 'https://example.com/create',
                'method': 'GET',
                'body': None
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': dict(op_body)
            }
        }
    }

    ce = self.CommandExecution(
        create_call,
        {'expect_stderr': 'Polling operation [operation-12345]\n'},
        {'expect_exit': {'code': 0}})

    rrr = reference_resolver.ResourceReferenceResolver()
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE, rrr=rrr):
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/create', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      self.assertEqual(rrr._extracted_ids['operation'], 'operation-12345')
      log.status.Print('Polling operation [operation-12345]')

      op_body['status'] = 'RUNNING'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345/wait', method='POST',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))
      # Running again.
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345/wait', method='POST',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      op_body['status'] = 'DONE'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345/wait', method='POST',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

  def testAPICallWithRefExtraction(self):
    call1 = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None,
            },
            'expect_response': {
                'extract_references': [
                    {'field': 'foo.bar', 'reference': 'one'},
                    {'field': 'a.b', 'reference': 'another'},
                ],
                'body': {'json': {}}
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': {'foo': {'bar': 'one_value'},
                         'a': {'b': 'another_value'}}
            }
        }
    }
    call2 = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com/$$one$$/$$another$$',
                'method': 'GET',
                'body': None,
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': ''
            }
        }
    }
    ce = self.CommandExecution(call1, call2, {'expect_exit': {'code': 0}})
    with self.Execute(ce):
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(
          {'foo': {'bar': 'one_value'}, 'a': {'b': 'another_value'}},
          json.loads(body.decode('utf8')))

      status, body = http.Http().request(
          'https://example.com/one_value/another_value', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'', body)

  def testAPICallResponsePayloadUpdates(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    request_mock.return_value = ({'status': '200'}, b'success')
    data = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'headers': {'foo': 'bar'},
                'body': {
                    'json': {'body': 'foo'}
                }
            },
            'return_response': {
                'headers': {'status': '404'},
                'body': 'error'
            }
        }
    }
    ce = self.CommandExecution(data, {'expect_exit': {'code': 0}})
    with self.Execute(ce, execution_mode=session.ExecutionMode.LOCAL,
                      update_modes=[]):
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      # We get the canned data, not the real API data (mocked out to 200)
      self.assertEqual({'status': '404'}, status)
      self.assertEqual(b'error', body)
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE,
                      update_modes=[updates.Mode.API_RESPONSE_PAYLOADS]):
      status, body = http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})
      # The "real" call is now made and the mock response is returned.
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(b'success', body)
    # Canned data is updated when in API_RESPONSE_PAYLOADS update mode.
    self.assertEqual(data['api_call']['return_response'],
                     {'headers': {'status': '200'}, 'body': 'success'})

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
        {'expect_file_written': {'path': 'foo.txt', 'contents': 'asdf'}},
        {'expect_prompt_continue': {'message': 'foo', 'user_input': 'y'}},
        {'expect_prompt_choice': {'choices': ['a', 'b', 'c'],
                                  'message': 'foo', 'user_input': '2'}},
        {'expect_progress_bar': {'message': 'foo'}},
        {'expect_progress_tracker': {'message': 'foo', 'status': 'SUCCESS'}},
        {'expect_stderr': 'Done'},
        {'expect_exit': {'code': 0}},
    )
    with self.Execute(ce):
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
      files.WriteFileContents('foo.txt', 'asdf')
      self.assertTrue(console_io.PromptContinue(message='foo'))
      self.assertEqual(
          console_io.PromptChoice(['a', 'b', 'c'], message='foo'), 1)
      log.status.write('{"ux": "PROGRESS_BAR", "message": "foo"}')
      log.status.write(
          '{"ux": "PROGRESS_TRACKER", "message": "foo", "status": "SUCCESS"}')
      log.status.write('Done')


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
         {'expect_stderr': 'this is stderr\nthis is more stderr\n'},
         {'expect_exit': {'code': 0}}],
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
    self.assertEqual([{'expect_exit': {'code': 0}}, {}, {}],
                     s.GetEventSequence())

  def testAddRemoveUpdateEvents(self):
    data = {'execute_command': {'command': '', 'events': [
        {'expect_stdout': 'foo'},
        {'expect_stderr': 'bar'},
        {'expect_prompt_continue': {'message': 'foo', 'user_input': 'y'}},
        {'expect_stdout': 'foo'},
        {'expect_stderr': 'bar'}]}}
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      log.out.write('new foo')
      log.status.write('new bar')
      console_io.PromptContinue(message='foo')
      log.status.write('extra status')
      log.out.write('foo')
    self.assertEqual(
        [{'expect_stdout': 'new foo'},
         {'expect_stderr': 'new bar'},
         {'expect_prompt_continue': {'message': 'foo', 'user_input': 'y'}},
         {'expect_stderr': 'extra status'},
         {'expect_stdout': 'foo'},
         {'expect_exit': {'code': 0}},
         {}],
        s.GetEventSequence())

  def testAddEventsAtLastKnownScenarioLocation(self):
    data_string = """\
'execute_command':
  'command': ''
  'events':
   - 'expect_stdout': 'foo'
    """
    data = yaml.load(data_string, round_trip=True, version=yaml.VERSION_1_2)
    ce = schema.CommandExecutionAction.FromData(data)
    with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                        updates.Mode.UX,
                                        updates.Mode.API_REQUESTS]) as s:
      log.out.write('foo\n')
      log.status.write('bar\n')
    # stdout, stderr, and exit event.
    self.assertEqual(3, len(s.GetEventSequence()))

  def testPauseError(self):
    ce = self.CommandExecution({'expect_stderr': 'foo'})
    with self.assertRaisesRegex(session.PauseError, 'expect_api_call'):
      with self.Execute(ce, update_modes=[updates.Mode.RESULT,
                                          updates.Mode.UX,
                                          updates.Mode.API_REQUESTS]) as s:
        http.Http().request(
            'https://example.com', method='GET', body='{"body": "foo"}',
            headers={'foo': 'bar'})

    expected = [
        {'api_call':
             {'expect_request':
                  {'body': {'json': {'body': 'foo'}}, 'headers': {},
                   'method': 'GET', 'uri': 'https://example.com'},
              'return_response': {'body': None, 'headers': {'status': '200'}}}},
        {'expect_stderr': 'foo'}]
    # Note that the expect_stderr is not deleted.
    actual = s.GetEventSequence()
    self.assertEqual(actual, expected)

  def testRepeatableAPICall(self):
    """Check that repeatable calls are automatically marked as such."""
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    running = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'json': {'status': 'RUNNING'}},
            }
        }
    }
    stderr_data = {'expect_stderr': 'bar'}
    done = {
        'api_call': {
            'expect_request': {
                'uri': 'https://example.com',
                'method': 'GET',
                'body': None
            },
            'expect_response': {
                'body': {'json': {'status': 'DONE'}},
            }
        }
    }

    ce = self.CommandExecution(
        running, stderr_data, done, {'expect_exit': {'code': 0}})
    response = {'status': 'RUNNING', 'progress': '0'}
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE,
                      update_modes=[updates.Mode.API_REQUESTS]):
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('RUNNING', self.FromJson(body)['status'])
      self.assertEqual('0', self.FromJson(body)['progress'])

      response['progress'] = '50'
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('RUNNING', self.FromJson(body)['status'])
      self.assertEqual('50', self.FromJson(body)['progress'])

      log.status.write('bar')

      response['status'] = 'DONE'
      response['progress'] = '100'
      request_mock.return_value = ({'status': '200'}, self.ToJson(response))
      status, body = http.Http().request(
          'https://example.com', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual('DONE', self.FromJson(body)['status'])
      self.assertEqual('100', self.FromJson(body)['progress'])

    self.assertEqual(running['api_call']['repeatable'], True)
    self.assertEqual(done['api_call'].get('repeatable'), None)

  def testAPICallGenerateOperationPolling(self):
    request_mock = self.StartObjectPatch(session.Session, '_MakeRealRequest')
    op_body = {
        'name': 'operation-12345',
        'kind': 'foo#operation',
        'operationType': 'CREATE',
        'status': 'PENDING',
    }
    create_call = {
        'api_call': {
            'poll_operation': True,
            'expect_request': {
                'uri': 'https://example.com/create',
                'method': 'GET',
                'headers': {},
                'body': None
            },
            'return_response': {
                'headers': {'status': '200'},
                'body': op_body
            }
        }
    }
    exit_call = {'expect_exit': {'code': 0}}

    ce = self.CommandExecution(exit_call)
    with self.Execute(ce, execution_mode=session.ExecutionMode.REMOTE,
                      update_modes=updates.Mode._All()) as s:
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/create', method='GET', body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      op_body['status'] = 'RUNNING'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))
      # Running again.
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

      op_body['status'] = 'DONE'
      request_mock.return_value = ({'status': '200'}, self.ToJson(op_body))
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))
      # Running again.
      status, body = http.Http().request(
          'https://example.com/operations/operation-12345', method='GET',
          body='', headers={})
      self.assertEqual({'status': '200'}, status)
      self.assertEqual(op_body, self.FromJson(body))

    # Original call should show pending as the response.
    op_body['status'] = 'PENDING'
    actual_events = s.GetEventSequence()
    self.assertEqual(2, len(actual_events))

    self.assertDictEqual(create_call, actual_events[0])
    self.assertEqual(exit_call, actual_events[1])


if __name__ == '__main__':
  test_case.main()
