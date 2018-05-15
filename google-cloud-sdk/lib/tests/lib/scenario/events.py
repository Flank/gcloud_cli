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
import enum
from tests.lib.scenario import assertions

import six


class Event(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for all events."""

  def __init__(self, event_type, backing_data=None):
    self._event_type = event_type
    self._backing_data = backing_data

  def EventType(self):
    return self._event_type

  def BackingData(self):
    return self._backing_data

  def Location(self):
    return assertions.Context(
        self._backing_data, None, assertions.UpdateMode.NONE).Location()

  @abc.abstractmethod
  def Handle(self, *args, **kwargs):
    pass


class _SingleValueEvent(six.with_metaclass(abc.ABCMeta, Event)):
  """Base class for all event types that just check a single value."""

  def __init__(self, event_type, assertion, backing_data=None):
    super(_SingleValueEvent, self).__init__(event_type, backing_data)
    self._assertion = assertion

  def Handle(self, failures, value):
    self._assertion.Check(failures, value)


class StdoutEvent(_SingleValueEvent):
  """Checks that the captured stdout matches a given value."""

  @classmethod
  def ForMissing(cls, next_event):
    backing_data = {}
    location = next_event.Location() if next_event else None

    return cls(
        assertions.ScalarAssertion(
            assertions.Context(
                backing_data, 'stdout', assertions.UpdateMode.RESULT,
                was_missing=True, location=location),
            ''),
        backing_data)

  def __init__(self, assertion, backing_data=None):
    super(StdoutEvent, self).__init__(EventType.STDOUT, assertion, backing_data)


class StderrEvent(_SingleValueEvent):
  """Checks that the captured stderr matches a given value."""

  @classmethod
  def ForMissing(cls, next_event):
    backing_data = {}
    location = next_event.Location() if next_event else None

    return cls(
        assertions.ScalarAssertion(
            assertions.Context(
                backing_data, 'stderr', assertions.UpdateMode.UX,
                was_missing=True, location=location),
            ''),
        backing_data)

  def __init__(self, assertion, backing_data=None):
    super(StderrEvent, self).__init__(EventType.STDERR, assertion, backing_data)


class ExitEvent(_SingleValueEvent):
  """Checks that the command exit code matches a given value."""

  @classmethod
  def ForMissing(cls, next_event):
    backing_data = {}
    location = next_event.Location() if next_event else None

    return cls(
        assertions.ScalarAssertion(
            assertions.Context(
                backing_data, 'exit_code', assertions.UpdateMode.RESULT,
                was_missing=True, location=location),
            ''),
        backing_data)

  def __init__(self, assertion, backing_data=None):
    super(ExitEvent, self).__init__(EventType.EXIT, assertion, backing_data)


class StdinEvent(Event):
  """Provides user input to a prompt."""

  @classmethod
  def ForMissing(cls, next_event):
    backing_data = {}
    location = next_event.Location() if next_event else None
    return cls(
        [],
        assertions.Context(
            backing_data, 'stdin', assertions.UpdateMode.UX,
            was_missing=True, location=location),
        backing_data)

  def __init__(self, lines, context, backing_data=None):
    super(StdinEvent, self).__init__(EventType.STDIN, backing_data)
    self._lines = lines
    self._context = context

  def Lines(self):
    return self._lines

  def Handle(self, failures):
    if self._lines:
      return
    failures.Add(
        assertions.Failure.ForScalar(
            self._context, [], [],
            msg='The command required user input that was not provided.'))


class RequestEvent(Event):
  """Checks that the API request matches an expected request."""

  @classmethod
  def ForMissing(cls, next_event):
    body_data = {}
    request_data = {'body': body_data}
    backing_data = {'request': request_data}
    location = next_event.Location() if next_event else None

    return cls(
        assertions.ScalarAssertion(
            assertions.Context(
                request_data, 'uri', assertions.UpdateMode.API_REQUESTS,
                was_missing=True, location=location),
            ''),
        assertions.ScalarAssertion(
            assertions.Context(
                request_data, 'method', assertions.UpdateMode.API_REQUESTS,
                was_missing=True, location=location),
            ''),
        assertions.DictAssertion(
            assertions.Context(
                request_data, 'headers', assertions.UpdateMode.API_REQUESTS,
                was_missing=True, location=location),
            is_bytes=True),
        assertions.ScalarAssertion(
            assertions.Context(
                body_data, 'json', assertions.UpdateMode.API_REQUESTS,
                was_missing=True, location=location),
            ''),
        assertions.ResponsePayloadAssertion(assertions.Context.Empty()),
        backing_data)

  def __init__(self, uri_assertion, method_assertion, headers_assertion,
               payload_assertion, response_assertion, backing_data=None):
    super(RequestEvent, self).__init__(EventType.REQUEST, backing_data)
    self._uri_assertion = uri_assertion
    self._method_assertion = method_assertion
    self._headers_assertion = headers_assertion
    # TODO(b/78588819): This is probably not what we want. We probably want to
    # force the user to assert a specific payload.
    self._payload_assertion = payload_assertion
    self._response_assertion = response_assertion

  def Handle(self, failures, uri, method, headers, body):
    self._uri_assertion.Check(failures, uri)
    self._method_assertion.Check(failures, method)
    self._headers_assertion.Check(failures, headers)
    self._payload_assertion.Check(failures, body)

  def Response(self):
    return self._response_assertion


class EventType(enum.Enum):
  """Describes the set of events we can handle as part of a scenario."""
  STDOUT = (StdoutEvent)
  STDERR = (StderrEvent)
  STDIN = (StdinEvent)
  REQUEST = (RequestEvent)
  EXIT = (ExitEvent)

  def __init__(self, impl):
    self._impl = impl

  def Impl(self):
    return self._impl
