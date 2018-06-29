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


"""Defines the different types of scenario event handlers."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
from collections import OrderedDict
import json
import enum


from googlecloudsdk.core.util import http_encoding
from tests.lib.scenario import assertions
from tests.lib.scenario import updates

import httplib2
import six
from six.moves import urllib


class Event(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for all events."""

  def __init__(self, update_context):
    self._update_context = update_context

  @classmethod
  def EventType(cls):
    return None

  def UpdateContext(self):
    return self._update_context

  @abc.abstractmethod
  def Handle(self, *args, **kwargs):
    return []


class _SingleValueEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """Base class for all event types that just check a single value."""

  @classmethod
  def _Build(cls, backing_data, field, default=None, was_missing=False,
             location=None):
    value = backing_data.get(field, default)
    if value is None:
      value = ''
    update_context = updates.Context(
        backing_data, field, cls.EventType().UpdateMode(),
        was_missing=was_missing, location=location)
    return cls(update_context, assertions.EqualsAssertion(value))

  def __init__(self, update_context, assertion):
    super(_SingleValueEvent, self).__init__(update_context)
    self._assertion = assertion

  def Handle(self, value):
    return self._assertion.Check(self._update_context, value)


class StdoutEvent(_SingleValueEvent):
  """Checks that the captured stdout matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDOUT

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stdout')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build({}, 'expect_stdout', was_missing=True, location=location)


class StderrEvent(_SingleValueEvent):
  """Checks that the captured stderr matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.STDERR

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_stderr')

  @classmethod
  def ForMissing(cls, location):
    return cls._Build({}, 'expect_stderr', was_missing=True, location=location)


class ExitEvent(_SingleValueEvent):
  """Checks that the command exit code matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.EXIT

  @classmethod
  def FromData(cls, backing_data):
    return cls._Build(backing_data, 'expect_exit_code', default=0)

  @classmethod
  def ForMissing(cls, location):
    return cls._Build(
        {}, 'expect_exit_code', default='', was_missing=True, location=location)


class UserInputEvent(Event):
  """Provides user input to a prompt."""

  @classmethod
  def EventType(cls):
    return EventType.USER_INPUT

  @classmethod
  def FromData(cls, backing_data):
    return cls(
        updates.Context(
            backing_data, 'user_input', cls.EventType().UpdateMode()),
        backing_data.get('user_input') or [])

  @classmethod
  def ForMissing(cls, location):
    update_context = updates.Context(
        {}, 'user_input', cls.EventType().UpdateMode(), was_missing=True,
        location=location)
    return cls(update_context, [])

  def __init__(self, update_context, lines):
    super(UserInputEvent, self).__init__(update_context)
    self._lines = lines

  def Lines(self):
    return self._lines

  def Handle(self):
    """Handle the event.

    A user input event is a little different from the others because it is not
    an assertion. Basically, if there are lines registered, there is no failure
    because it provides the input and execution moves on. If there are no lines,
    then the prompt cannot be answered and it is an error.

    Returns:
      [Failure], The failures or []
    """
    if self._lines:
      return []
    return [assertions.Failure.ForGeneric(
        self._update_context, title='Missing user input event')]


def _AddAssertion(assertion, key, value):
  """Adds an additional assertion to a DictAssertion for a given key."""
  if not isinstance(value, dict):
    return assertion.Equals(key, value)
  elif 'equals' in value:
    return assertion.Equals(key, value['equals'])
  elif 'matches' in value:
    return assertion.Matches(key, value['matches'])
  elif 'is_none' in value:
    return assertion.IsNone(key, value['is_none'])
  elif 'in' in value:
    return assertion.In(key, value['in'])
  # This should never happen for things that pass schema validation.
  raise ValueError('Assertion type is invalid.')


class ApiCallEvent(Event):
  """Checks that the API request matches an expected request."""

  class ResponsePayload(object):
    """Encapsulates the data of a response payload."""

    def __init__(self, headers, payload):
      self._headers = headers
      if isinstance(payload, dict):
        payload = json.dumps(payload)
      payload = payload or ''
      self._payload = http_encoding.Encode(payload)

    def Respond(self):
      return (httplib2.Response(self._headers), self._payload)

  @classmethod
  def EventType(cls):
    return EventType.API_CALL

  @classmethod
  def FromData(cls, backing_data):
    """Builds a request event handler from yaml data."""
    call_data = backing_data['api_call']
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode())

    request_data = call_data['expect_request']

    uri_assertion = assertions.EqualsAssertion(request_data.get('uri', ''))
    method_assertion = assertions.EqualsAssertion(
        request_data.get('method', 'GET'))
    header_assertion = assertions.DictAssertion()
    for header, value in six.iteritems(request_data.get('headers', {})):
      _AddAssertion(header_assertion, header, value)

    body_data = request_data.get('body')
    payload_assertion = assertions.JsonAssertion()
    if body_data is None or isinstance(body_data, six.string_types):
      payload_assertion.Matches('', body_data)
    elif not body_data:
      # It's an explicitly provided empty dict.
      payload_assertion.Matches('', {})
    else:
      for field, struct in six.iteritems(body_data):
        payload_assertion.Matches(field, struct)

    response = call_data.get('return_response') or {}

    response_payload = ApiCallEvent.ResponsePayload(
        headers=response.get('headers', {'status': '200'}),
        payload=response.get('body', ''))

    return cls(
        update_context, uri_assertion, method_assertion, header_assertion,
        payload_assertion, response_payload)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {'api_call':
                    {'expect_request': {'headers': {}, 'body': None},
                     'return_response':
                     {'headers': {'status': '200'}, 'body': ''}}}
    update_context = updates.Context(
        backing_data, 'api_call', cls.EventType().UpdateMode(),
        was_missing=True, location=location)
    response = backing_data['api_call']['return_response']

    return cls(
        update_context,
        assertions.EqualsAssertion(''),
        assertions.EqualsAssertion(''),
        assertions.DictAssertion(),
        assertions.JsonAssertion().Matches('', None),
        ApiCallEvent.ResponsePayload(headers=response['headers'],
                                     payload=response['body']))

  def __init__(self, update_context, uri_assertion, method_assertion,
               headers_assertion, payload_assertion, response_payload):
    super(ApiCallEvent, self).__init__(update_context)
    self._uri_assertion = uri_assertion
    self._method_assertion = method_assertion
    self._headers_assertion = headers_assertion
    # TODO(b/78588819): This is probably not what we want. We probably want to
    # force the user to assert a specific payload.
    self._payload_assertion = payload_assertion
    self._response_payload = response_payload

  def _OrderedUri(self, uri):
    """Sorts URI params to ensure they are always processed in same order."""
    url_parts = urllib.parse.urlsplit(uri)
    params = urllib.parse.parse_qs(url_parts.query)
    ordered_query_params = OrderedDict(sorted(six.iteritems(params)))
    url_parts = list(url_parts)
    # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
    url_parts[3] = urllib.parse.urlencode(ordered_query_params, doseq=True)
    # pylint:disable=too-many-function-args, This is just bogus.
    return urllib.parse.urlunsplit(url_parts)

  def Handle(self, uri, method, headers, body):
    failures = []
    uri = self._OrderedUri(uri)
    failures.extend(
        self._uri_assertion.Check(
            self._update_context.ForKey('expect_request.uri'), uri))
    failures.extend(
        self._method_assertion.Check(
            self._update_context.ForKey('expect_request.method'), method))
    failures.extend(
        self._headers_assertion.Check(
            self._update_context.ForKey('expect_request.headers'),
            {http_encoding.Decode(h): http_encoding.Decode(v)
             for h, v in six.iteritems(headers)}))
    failures.extend(
        self._payload_assertion.Check(
            self._update_context.ForKey('expect_request.body'), body))
    return failures

  def HandleResponse(self, real_response):
    def _ResponseUpdateHook(context, actual):
      data = context.BackingData()
      response, payload = actual
      data['return_response']['headers'] = {
          key: value for key, value in sorted(six.iteritems(response))}
      data['return_response']['body'] = payload

    update_context = self._update_context.ForKey(
        'return_response',
        update_mode=assertions.updates.Mode.API_RESPONSES,
        custom_update_hook=_ResponseUpdateHook)

    # TODO(b/78588819): Add support for real response assertions.
    response_assertion = assertions.ResponsePayloadAssertion()
    return response_assertion.Check(update_context, real_response)

  def Respond(self):
    return self._response_payload.Respond()


class ProgressBarEvent(Event):
  """Checks that the Progress Bar Event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_BAR

  @classmethod
  def FromData(cls, backing_data):
    ux_data = backing_data['expect_progress_bar']
    update_context = updates.Context(
        backing_data, 'expect_progress_bar', cls.EventType().UpdateMode())
    message_assertion = assertions.EqualsAssertion(ux_data.get('message', ''))
    return cls(update_context, message_assertion)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {'expect_progress_bar': {'message': ''}}
    update_context = updates.Context(
        backing_data, 'expect_progress_bar', cls.EventType().UpdateMode(),
        was_missing=True, location=location)

    return cls(update_context, assertions.EqualsAssertion(''))

  def __init__(self, update_context, message_assertion):
    super(ProgressBarEvent, self).__init__(update_context)
    self._message_assertion = message_assertion

  def Handle(self, message):
    failures = []
    failures.extend(
        self._message_assertion.Check(
            self._update_context.ForKey('message'), message))
    return failures


class ProgressTrackerEvent(Event):
  """Checks that the tracker event (from stderr) matches a given value."""

  @classmethod
  def EventType(cls):
    return EventType.PROGRESS_TRACKER

  @classmethod
  def FromData(cls, backing_data):
    ux_data = backing_data['expect_progress_tracker']
    update_context = updates.Context(
        backing_data, 'expect_progress_tracker', cls.EventType().UpdateMode())
    message_assertion = assertions.EqualsAssertion(ux_data.get('message', ''))
    status_assertion = assertions.EqualsAssertion(ux_data.get('status', ''))
    return cls(update_context, message_assertion, status_assertion)

  @classmethod
  def ForMissing(cls, location):
    backing_data = {'expect_progress_tracker': {'message': '', 'status': ''}}
    update_context = updates.Context(
        backing_data, 'expect_progress_tracker', cls.EventType().UpdateMode(),
        was_missing=True, location=location)

    return cls(update_context,
               assertions.EqualsAssertion(''),
               assertions.EqualsAssertion(''))

  def __init__(self, update_context, message_assertion, status_assertion):
    super(ProgressTrackerEvent, self).__init__(update_context)
    self._message_assertion = message_assertion
    self._status_assertion = status_assertion

  def Handle(self, message, status):
    failures = []
    failures.extend(
        self._message_assertion.Check(
            self._update_context.ForKey('message'), message))
    failures.extend(
        self._status_assertion.Check(
            self._update_context.ForKey('status'), status))
    return failures


class EventType(enum.Enum):
  """Describes the set of events we can handle as part of a scenario."""
  STDOUT = (StdoutEvent, assertions.updates.Mode.RESULT)
  STDERR = (StderrEvent, assertions.updates.Mode.UX)
  USER_INPUT = (UserInputEvent, assertions.updates.Mode.UX)
  API_CALL = (ApiCallEvent, assertions.updates.Mode.API_REQUESTS)
  EXIT = (ExitEvent, assertions.updates.Mode.RESULT)
  PROGRESS_BAR = (ProgressBarEvent, assertions.updates.Mode.UX)
  PROGRESS_TRACKER = (ProgressTrackerEvent, assertions.updates.Mode.UX)

  def __init__(self, impl, update_mode):
    self._impl = impl
    self._update_mode = update_mode

  def Impl(self):
    return self._impl

  def UpdateMode(self):
    return self._update_mode


