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


"""Defines a scenario session that runs a sequence of commands."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re
import sys

from googlecloudsdk.core import http
from googlecloudsdk.core.console import console_io
from tests.lib.scenario import assertions
from tests.lib.scenario import events as events_lib

import httplib2
import mock

_UX_TYPES = [ux.name for ux in console_io.UXElementType]
_UX_RE = re.compile(r'^{{\"ux\": \"({})\"'.format('|'.join(_UX_TYPES)))


class Error(Exception):
  """General exception for the module."""
  pass


class StreamMocker(object):

  def __init__(self, stdout_reader, stderr_reader, stdin_writer):
    self.stdout_reader = stdout_reader
    self.stderr_reader = stderr_reader
    self.stdin_writer = stdin_writer


class Session(object):
  """Runs a scenario session and checks assertions."""

  def __init__(self, events, failures, stream_mocker):
    self._events = events
    self._current_event_index = 0
    self._failures = failures
    self._stream_mocker = stream_mocker
    if self._events:
      self._last_known_location = self._events[-1].UpdateContext().Location()
    else:
      self._last_known_location = None

    # pylint:disable=protected-access
    self._real_http_client = http._CreateRawHttpClient()
    self._orig_request_method = httplib2.Http.request
    self._request_patch = mock.patch.object(
        httplib2.Http, 'request', side_effect=self._HandleRequest)

    self._orig_stdout_write = sys.stdout.write
    self._captured_stdout = ''
    self._stdout_patch = mock.patch.object(
        sys.stdout, 'write', side_effect=self._HandleStdout)

    self._orig_stderr_write = sys.stderr.write
    self._captured_stderr = ''
    self._stderr_patch = mock.patch.object(
        sys.stderr, 'write', side_effect=self._HandleStderr)

    self._orig_input = console_io._GetInput
    self._stdin_patch = mock.patch.object(
        console_io, '_GetInput', side_effect=self._HandleUserInput)

  def _Handle(self, event, *args, **kwargs):
    self._failures.AddAll(event.Handle(*args, **kwargs))

  def _CurrentEvent(self):
    if self._current_event_index >= len(self._events):
      return None
    current_event = self._events[self._current_event_index]

    return current_event

  def LastKnownScenarioLocation(self):
    """Return the last known event location in provided scenario."""
    return self._last_known_location

  def _InsertEvent(self, event):
    self._events.insert(self._current_event_index, event)

  def _GetOrCreateCurrentEvent(self, expected_type):
    current_event = self._CurrentEvent()
    if not current_event or current_event.EventType() != expected_type:

      location = (current_event.UpdateContext().Location() if current_event
                  else self._last_known_location)

      current_event = expected_type.Impl().ForMissing(location)
      self._InsertEvent(current_event)
    return current_event

  def _HandleRequest(self, uri, method, body, headers, *args, **kwargs):
    """Mock http request function."""
    self._ProcessStdout()
    self._ProcessStderr()

    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.API_CALL)
    self._current_event_index += 1
    self._Handle(current_event, uri, method, headers, body)

    # Perform actual requests only if we are updating API responses.
    if self._failures.ShouldMakeRequests():
      real_response = self._orig_request_method(
          self._real_http_client, uri, method, body, headers, *args, **kwargs)
      self._failures.AddAll(current_event.HandleResponse(real_response))
      return real_response

    return current_event.Respond()

  def _HandleStdout(self, *args, **kwargs):
    self._ProcessStderr()

    self._orig_stdout_write(*args, **kwargs)
    self._captured_stdout += self._stream_mocker.stdout_reader()
    self._GetOrCreateCurrentEvent(events_lib.EventType.STDOUT)

  def _HandleStderr(self, *args, **kwargs):
    """Handler stderr events."""
    self._ProcessStdout()

    self._orig_stderr_write(*args, **kwargs)
    next_stderr_item = self._stream_mocker.stderr_reader()

    ux_event = self._ParseUxEvent(next_stderr_item)
    if ux_event:
      # if the next stderr event is a ux event,
      # immedately process the current stderr stream
      self._ProcessStderr()
      self._HandleUxEvent(ux_event)
    else:
      self._captured_stderr += next_stderr_item
      self._GetOrCreateCurrentEvent(events_lib.EventType.STDERR)

  def _ProcessStdout(self):
    if not self._captured_stdout:
      return

    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.STDOUT)
    self._current_event_index += 1
    self._Handle(current_event, self._captured_stdout)
    self._captured_stdout = ''

  def _ProcessStderr(self):
    if not self._captured_stderr:
      return

    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.STDERR)
    self._current_event_index += 1
    self._Handle(current_event, self._captured_stderr)
    self._captured_stderr = ''

  def _HandleUserInput(self):
    """Mock stdin input() function."""
    self._ProcessStdout()
    self._ProcessStderr()

    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.USER_INPUT)
    self._current_event_index += 1

    lines = current_event.Lines()
    if lines:
      self._stream_mocker.stdin_writer(*lines)
    self._Handle(current_event)

    return self._orig_input()

  def HandleExit(self, exit_code):
    self._ProcessStdout()
    self._ProcessStderr()

    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.EXIT)
    self._current_event_index += 1
    self._Handle(current_event, exit_code)

  def __enter__(self):
    self._stdout_patch.start()
    self._stderr_patch.start()
    self._stdin_patch.start()
    self._request_patch.start()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._ProcessStdout()
    self._ProcessStderr()
    self._stdout_patch.stop()
    self._stderr_patch.stop()
    self._stdin_patch.stop()
    self._request_patch.stop()

    # Create failures for extra assertions that did not get triggered.
    if exc_type is None:
      event = self._CurrentEvent()
      while event:
        self._failures.Add(
            assertions.Failure.ForExtraAssertion(event.UpdateContext()))
        self._current_event_index += 1
        event = self._CurrentEvent()

  def GetEventSequence(self):
    return [event.UpdateContext().BackingData() for event in self._events]

  def _HandleUxEvent(self, ux_json_data):
    """Handle UX Events."""
    ux_type = events_lib.EventType[ux_json_data['ux']]

    if ux_type == events_lib.EventType.PROGRESS_TRACKER:
      self._ProcessProgressTracker(ux_json_data)

    elif ux_type == events_lib.EventType.PROGRESS_BAR:
      self._ProcessProgressBar(ux_json_data)

    else:
      raise ValueError(ux_json_data)

  def _ParseUxEvent(self, stderr_content):
    """Check if given stderr_content matches UX known event and try to parse."""
    if _UX_RE.match(stderr_content):
      try:
        parsed_event_json = json.loads(stderr_content)
        return parsed_event_json
      except ValueError as err:
        raise Error('Unparseable UX Event [{}]: {}'.format(stderr_content, err))

    return None

  def _ProcessProgressTracker(self, tracker_data):
    """Process ProgressTracker UX Event from stderr."""
    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.PROGRESS_TRACKER)
    self._current_event_index += 1
    self._Handle(current_event, tracker_data['message'], tracker_data['status'])

  def _ProcessProgressBar(self, progress_bar_data):
    """Process ProgressBar UX Event from stderr."""
    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.PROGRESS_BAR)
    self._current_event_index += 1
    self._Handle(current_event, progress_bar_data['message'])

