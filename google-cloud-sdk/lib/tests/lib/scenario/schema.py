# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Parses the scenario yaml test file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.scenario import assertions
from tests.lib.scenario import events as events_lib

import six


class Scenario(object):
  """Holds the entire scneario spec."""

  @classmethod
  def FromData(cls, data):
    """Build the object from spec data."""
    response_assertions = {
        key: assertions.ResponsePayloadAssertion(
            assertions.Context.Empty(
                custom_update_hook=_ResponseUpdateHook(response)),
            headers=response.get('headers', {'status': 200}),
            payload=response.get('body', ''))
        for key, response in six.iteritems(data['responses'])}
    return cls(
        [CommandExecution.FromData(c, response_assertions)
         for c in data.get('commands') or []],
        response_assertions
    )

  def __init__(self, command_executions, response_payloads):
    self.command_executions = command_executions
    self.response_payloads = response_payloads


def _ResponseUpdateHook(data):
  def _Update(actual):
    response, payload = actual
    data['headers'] = {
        key: value for key, value in sorted(six.iteritems(response))}
    data['body'] = payload

  return assertions.UpdateHook(_Update, assertions.UpdateMode.API_RESPONSES)


class CommandExecution(object):
  """Holds the spec for a single command execution."""

  @classmethod
  def FromData(cls, data, response_assertions):
    """Build the object from spec data."""

    event = []
    for e in data['events']:
      if 'request' in e:
        event.append(_BuildRequestEvent(e, response_assertions))
      elif 'stdout' in e:
        event.append(_BuildStdoutEvent(e))
      elif 'stderr' in e:
        event.append(_BuildStderrEvent(e))
      elif 'stdin' in e:
        event.append(_BuildStdinEvent(e))
      elif 'exit_code' in e:
        event.append(_BuildExitCodeEvent(e))

    return cls(
        data['command'],
        event,
        data['events']
    )

  def __init__(self, command, events, original_event_data):
    self.command = command
    self.events = events
    self.original_event_data = original_event_data


def _BuildExitCodeEvent(data):
  code = data.get('exit_code', 0)
  return events_lib.ExitEvent(
      assertions.ScalarAssertion(
          assertions.Context(data, 'exit_code', assertions.UpdateMode.RESULT),
          code),
      backing_data=data
  )


def _BuildStdoutEvent(data):
  return events_lib.StdoutEvent(
      assertions.ScalarAssertion(
          assertions.Context(data, 'stdout', assertions.UpdateMode.RESULT),
          data.get('stdout') or ''),
      backing_data=data
  )


def _BuildStderrEvent(data):
  return events_lib.StderrEvent(
      assertions.ScalarAssertion(
          assertions.Context(data, 'stderr', assertions.UpdateMode.UX),
          data.get('stderr') or ''),
      backing_data=data
  )


def _BuildStdinEvent(data):
  return events_lib.StdinEvent(
      data.get('stdin') or [],
      assertions.Context(data, 'stdin', assertions.UpdateMode.UX),
      backing_data=data
  )


def _BuildRequestEvent(data, response_assertions):
  """Builds a request event handler from yaml data."""
  request_data = data['request']
  uri_assertion = assertions.ScalarAssertion(
      assertions.Context(
          request_data, 'uri', assertions.UpdateMode.API_REQUESTS),
      request_data.get('uri', ''))

  method_assertion = assertions.ScalarAssertion(
      assertions.Context(
          request_data, 'method', assertions.UpdateMode.API_REQUESTS),
      request_data.get('method', 'GET'))

  header_assertion = assertions.DictAssertion(
      assertions.Context(
          request_data, 'headers', assertions.UpdateMode.API_REQUESTS))
  for header, value in six.iteritems(request_data.get('headers', {})):
    header_assertion.KeyEquals(header, value)

  body = request_data.get('body') or {}
  if 'json' not in body:
    body['json'] = {}
  payload_assertion = assertions.JsonAssertion(
      assertions.Context(
          body, 'json', assertions.UpdateMode.API_REQUESTS))
  if body['json'] is None:
    payload_assertion.Matches('', None)
  elif not body['json']:
    payload_assertion.Matches('', {})
  else:
    for field, struct in six.iteritems(body['json']):
      payload_assertion.Matches(field, struct)

  response_id = request_data['response_id']
  response_assertion = response_assertions[response_id]

  return events_lib.RequestEvent(
      uri_assertion, method_assertion, header_assertion, payload_assertion,
      response_assertion,
      backing_data=data
  )
