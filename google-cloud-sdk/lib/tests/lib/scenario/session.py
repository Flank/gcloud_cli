# -*- coding: utf-8 -*- #
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

import contextlib
import json
import os
import re
import sys
import enum

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib.scenario import assertions
from tests.lib.scenario import events as events_lib

import httplib2
import mock

_UX_TYPES = [ux.name for ux in console_io.UXElementType]
_UX_RE = re.compile(r'^{{\"ux\": \"({})\"'.format('|'.join(_UX_TYPES)))


class Error(Exception):
  """General exception for the module."""
  pass


class PauseError(Error):
  """Exception for when we pause the scenario so the user can enter more input.
  """
  pass


class ExecutionMode(enum.Enum):
  """Represents what mode the tests are being run in.

  Tests can declare that they work in LOCAL mode or REMOTE mode (which implies
  they can run in LOCAL mode as well). When running in LOCAL mode, all tests are
  run in LOCAL mode (even those that can be run in REMOTE mode) and no real API
  calls are made. In REMOTE mode, those tests that can be run as REMOTE tests
  will be (making real requests), while those that only work in LOCAL mode will
  continue to run as LOCAL tests.
  """
  LOCAL = 0
  REMOTE = 1


class StreamMocker(object):

  def __init__(self, stdout_reader, stderr_reader, stdin_writer):
    self.stdout_reader = stdout_reader
    self.stderr_reader = stderr_reader
    self.stdin_writer = stdin_writer


class Session(object):
  """Runs a scenario session and checks assertions."""

  def __init__(self, events_generator, failures, stream_mocker, execution_mode,
               resource_ref_resolver, action_location=None):
    self._events = []
    self._events_generator = events_generator
    self._LoadNextEvent()

    self._last_repeatable_api_call_event = None

    self._failures = failures
    self._stream_mocker = stream_mocker
    self._execution_mode = execution_mode
    self._action_location = action_location
    self._resource_ref_resolver = resource_ref_resolver

    self._user_input_already_given = False
    self._exit_was_handled = False

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

    self._orig_file_writer = files.FileWriter
    self._file_writer_patch = mock.patch.object(
        files, 'FileWriter', side_effect=self._HandleFileWrite)
    self._orig_binary_file_writer = files.BinaryFileWriter
    self._binary_file_writer_patch = mock.patch.object(
        files, 'BinaryFileWriter', side_effect=self._HandleBinaryFileWrite)

    self._orig_input = console_io._GetInput
    self._stdin_patch = mock.patch.object(
        console_io, '_GetInput', side_effect=self._HandleUserInput)

    self._exit_patch = mock.patch.object(
        calliope_exceptions, '_Exit', side_effect=self._HandleExit)
    # We don't do any handling here, we just don't want the error message to
    # get logged.
    self._log_error_patch = mock.patch.object(
        calliope_exceptions, '_LogKnownError')

  def _Handle(self, event, *args, **kwargs):
    self._failures.AddAll(event.Handle(*args, **kwargs))

  def _LoadNextEvent(self):
    try:
      self._events.append(next(self._events_generator))
    except StopIteration:
      self._events.append(None)

  def _CurrentEvent(self):
    return self._events[-1]

  def _InsertEvent(self, event):
    self._events.insert(-1, event)

  def _GetOrCreateCurrentEvent(self, expected_type, advance=True):
    """Gets the next matching event from the event stream.

    If there are no more events or if the next event is not of the requested
    type, a new evernt is generated to match and inserted into the stream.

    Args:
      expected_type: events_lib.Event, The type of event that should be next.
      advance: bool, If true, the next event is returned and a new event is
        taken off the queue. If false, we don't advance the queue because we are
        going to do it manually later. When getting the next event, it is
        generated at that time (because events is a generator). Sometimes we
        need to delay the loading of the next event until the previous is
        completely finished, because its execution affects the loading of the
        next event.

    Returns:
      events_lib.Event, the event to use.
    """
    current_event = self._CurrentEvent()
    if not current_event or current_event.EventType() != expected_type:
      if current_event:
        location = current_event.UpdateContext().Location()
      elif len(self._events) > 1:
        e = self._events[-2]
        location = e.UpdateContext().Location() if e else self._action_location
      else:
        location = self._action_location

      current_event = expected_type.Impl().ForMissing(location)
      self._InsertEvent(current_event)
    elif advance:
      self._LoadNextEvent()
    return current_event

  def _GetLastRepeatableAPICallOrNext(self, uri, method, body, response):
    """For an API call, get either the previous or next event.

    If an api_call declares that it can be repeated, we are allowed to reuse it
    multiple times. This is useful for operation polling where there are many
    of the same request. We only return the previously used event if the request
    and response are a verbatim match.

    Args:
      uri: str, The URI being requested.
      method: str, The HTTP method being used in the request.
      body: str, The body of the request.
      response: str, The real response returned by the server.

    Returns:
       (APICallEvent, bool): The event to use and whether the processing of the
       event should trigger the event to be consumed. If reusing an old event,
       we shouldn't consume the next event in the sequence. If we are using a
       new event, we have to move on after we a done.
    """
    if self._last_repeatable_api_call_event:
      if self._last_repeatable_api_call_event.Matches(
          uri, method, body, response):
        # Event matches, reuse the same event for the new call.
        self._last_repeatable_api_call_event.MarkRepeated()
        return (self._last_repeatable_api_call_event.Event(), False)
      else:
        # Not a match, we have moved on to a new api call, don't try to use the
        # old one again.
        self._failures.AddAll(self._last_repeatable_api_call_event.Check())
        self._last_repeatable_api_call_event = None

    # Get a new event to use for this request.
    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.API_CALL, advance=False)
    self._last_repeatable_api_call_event = events_lib.RepeatableAPICall(
        uri, method, body, current_event, response)
    return (current_event, True)

  def _HandleRequest(self, uri, method, body, headers, *args, **kwargs):
    """Mock http request function."""
    self._ProcessStdout()
    self._ProcessStderr()

    # These modes have a bunch in common, but it is clearer to split them than
    # have a bunch of if/else switches.
    if self._execution_mode == ExecutionMode.LOCAL:
      return self._HandleRequestLocal(uri, method, body, headers)
    return self._HandleRequestRemote(
        uri, method, body, headers, *args, **kwargs)

  def _HandleRequestLocal(self, uri, method, body, headers):
    """Handle a local request by using canned response data."""
    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.API_CALL, advance=False)

    # Validate the request assertions.
    self._Handle(current_event, uri, method, headers, body)

    # Use canned response data or pause if no response is registered.
    if current_event.UpdateContext().WasMissing():
      raise PauseError(
          'Pausing execution so API response can be added to expect_api_call '
          'at location: {}'.format(current_event.UpdateContext().Location()))
    response = current_event.GetResponsePayload()

    # Validate the response assertions.
    self._failures.AddAll(current_event.HandleResponse(
        response[0], response[1], self._resource_ref_resolver))

    self._LoadNextEvent()
    return response

  def _HandleRequestRemote(self, uri, method, body, headers, *args, **kwargs):
    """Handle a remote request by making a real API call."""
    response = self._orig_request_method(
        self._real_http_client, uri, method, body, headers, *args, **kwargs)

    (current_event, should_advance) = self._GetLastRepeatableAPICallOrNext(
        uri, method, body, response)

    # Validate the request assertions.
    self._Handle(current_event, uri, method, headers, body)

    # Update the canned response data.
    if self._failures.ShouldUpdateResponsePayloads():
      self._failures.AddAll(current_event.UpdateResponsePayload(*response))

    # Validate the response assertions.
    self._failures.AddAll(current_event.HandleResponse(
        response[0], response[1], self._resource_ref_resolver))

    if should_advance:
      self._LoadNextEvent()
    return response

  def _HandleStdout(self, *args, **kwargs):
    self._ProcessStderr()

    self._orig_stdout_write(*args, **kwargs)
    self._captured_stdout += self._stream_mocker.stdout_reader()

  def _HandleStderr(self, *args, **kwargs):
    """Handler stderr events."""
    self._ProcessStdout()

    self._orig_stderr_write(*args, **kwargs)
    next_stderr_item = self._stream_mocker.stderr_reader()

    ux_event = self._ParseUxEvent(next_stderr_item)
    if ux_event:
      # if the next stderr event is a ux event,
      # immediately process the current stderr stream
      self._ProcessStderr()
      self._HandleUxEvent(ux_event)
    else:
      self._captured_stderr += next_stderr_item

  def _ParseUxEvent(self, stderr_content):
    """Check if given stderr_content matches UX known event and try to parse."""
    if _UX_RE.match(stderr_content):
      try:
        parsed_event_json = json.loads(stderr_content)
        return parsed_event_json
      except ValueError as err:
        raise Error('Unparseable UX Event [{}]: {}'.format(stderr_content, err))

    return None

  def _HandleUxEvent(self, ux_json_data):
    """Handle UX Events."""
    ux_type = events_lib.EventType[ux_json_data['ux']]
    current_event = self._GetOrCreateCurrentEvent(ux_type)
    self._Handle(current_event, ux_json_data)

    if ux_type.HasUserInput():
      self._stream_mocker.stdin_writer(current_event.UserInput())
      self._user_input_already_given = True

  def _ProcessStdout(self):
    if not self._captured_stdout:
      return
    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.STDOUT)
    self._Handle(current_event, self._captured_stdout)
    self._captured_stdout = ''

  def _ProcessStderr(self):
    if not self._captured_stderr:
      return
    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.STDERR)
    self._Handle(current_event, self._captured_stderr)
    self._captured_stderr = ''

  def _HandleFileWrite(self, path, private=False, append=False):
    return self._HandleFileWriteImpl(
        False, path, private=private, append=append)

  def _HandleBinaryFileWrite(self, path, private=False):
    return self._HandleFileWriteImpl(True, path, private=private, append=False)

  @contextlib.contextmanager
  def _HandleFileWriteImpl(self, is_binary, path, private=False, append=False):
    """Intercept calls to write files."""
    abs_path = os.path.abspath(path)
    config_dir = os.path.abspath(config.Paths().global_config_dir)
    home_dir = os.path.abspath(os.path.expanduser('~'))
    if not (abs_path.startswith(os.path.abspath(os.getcwd())) or
            abs_path.startswith(home_dir) or
            abs_path.startswith(config_dir)):
      raise Error('Command is attempting to write file outside of current '
                  'working directory: [{}]'.format(abs_path))

    # Pass through the write like normal
    if is_binary:
      with self._orig_binary_file_writer(path, private=private) as fw:
        yield fw
    else:
      with self._orig_file_writer(path, private=private, append=append) as fw:
        yield fw

    # After they close it, capture what happened.
    if abs_path.startswith(config_dir):
      # Ignore any files written to config for assertion purposes.
      return

    current_event = self._GetOrCreateCurrentEvent(
        events_lib.EventType.FILE_WRITTEN)
    if is_binary:
      contents = files.ReadBinaryFileContents(path)
    else:
      contents = files.ReadFileContents(path)

    if abs_path.startswith(home_dir):
      path = '~' + abs_path[len(home_dir):]

    self._Handle(current_event, path, contents, private)

  def _HandleUserInput(self):
    """Mock stdin input() function."""
    if self._user_input_already_given:
      # User input has already been given as part of a prompt assertion.
      self._user_input_already_given = False
    else:
      self._ProcessStdout()
      self._ProcessStderr()

      current_event = self._GetOrCreateCurrentEvent(
          events_lib.EventType.USER_INPUT)

      lines = current_event.Lines()
      if lines:
        self._stream_mocker.stdin_writer(*lines)
      self._Handle(current_event)

    return self._orig_input()

  def _HandleExit(self, exc):
    self._ProcessStdout()
    self._ProcessStderr()

    current_event = self._GetOrCreateCurrentEvent(events_lib.EventType.EXIT)
    self._Handle(current_event, exc)
    self._exit_was_handled = True

  def __enter__(self):
    self._stdout_patch.start()
    self._stderr_patch.start()
    self._stdin_patch.start()
    self._request_patch.start()
    self._file_writer_patch.start()
    self._binary_file_writer_patch.start()
    self._exit_patch.start()
    self._log_error_patch.start()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._ProcessStdout()
    self._ProcessStderr()
    self._stdout_patch.stop()
    self._stderr_patch.stop()
    self._stdin_patch.stop()
    self._request_patch.stop()
    self._file_writer_patch.stop()
    self._binary_file_writer_patch.stop()
    self._exit_patch.stop()
    self._log_error_patch.stop()

    if not self._exit_was_handled and not (
        exc_val and isinstance(exc_val, Error)):
      # If we get here, there is either no exception or it is not an exception
      # type known to calliope (it would be a crash), since that would have been
      # handled by a intercepted call to _HandleError already.
      # Framework errors should not be handled here as they represent errors in
      # the test, not in the running command.
      self._HandleExit(exc_val)

    # Create failures for extra assertions that did not get triggered.
    if exc_type is None:
      event = self._CurrentEvent()
      while event:
        self._failures.Add(
            assertions.Failure.ForExtraAssertion(event.UpdateContext()))
        self._LoadNextEvent()
        event = self._CurrentEvent()

  def GetEventSequence(self):
    return [event.UpdateContext().BackingData()
            for event in self._events if event is not None]
