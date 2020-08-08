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
"""Defines a scenario session that runs a sequence of commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import enum
import json
import os
import re
import sys
import tempfile

from apitools.base.py import batch
from apitools.base.py import http_wrapper

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from tests.lib.scenario import assertions
from tests.lib.scenario import events as events_lib
from tests.lib.scenario import reference_resolver

import httplib2
import mock

_UX_TYPES = [ux.name for ux in console_io.UXElementType]
_UX_RE = re.compile(r'^{{\"ux\": \"({})\"'.format('|'.join(_UX_TYPES)))


class Error(Exception):
  """General exception for the module."""
  pass


class PauseError(Error):
  """Exception for when we pause the scenario so the user can enter more input."""
  pass


class ExecutionMode(enum.Enum):
  """Represents what mode the tests are being run in.

  Tests can declare that they work in LOCAL, REMOTE (which implies they can run
  in LOCAL mode as well) or BOTH mode.

  When running in LOCAL mode, all tests are
  run in LOCAL mode (even those that can be run in REMOTE mode) and no real API
  calls are made.

  In REMOTE mode, those tests that can be run as REMOTE tests
  will be (making real requests), while those that only work in LOCAL mode will
  continue to run as LOCAL tests.

  The BOTH mode will attempt a test in both REMOTE and LOCAL modes. If a test
  can only be run in LOCAL mode, it will still only be run in LOCAL mode.
  """
  LOCAL = 0
  REMOTE = 1
  BOTH = 2


class StreamMocker(object):

  def __init__(self, stdout_reader, stderr_reader, stdin_writer):
    self.stdout_reader = stdout_reader
    self.stderr_reader = stderr_reader
    self.stdin_writer = stdin_writer


class Session(object):
  """Runs a scenario session and checks assertions."""

  DONE = object()

  def __init__(self,
               events_generator,
               failures,
               stream_mocker,
               execution_mode,
               ignore_api_calls,
               resource_ref_resolver,
               action_location=None,
               debug=False):
    self._processed_events = []
    self.__next_event = None
    self._events_generator = events_generator
    self._processing_batch_request = False

    self._failures = failures
    self._stream_mocker = stream_mocker
    self._execution_mode = execution_mode
    self._ignore_api_calls = ignore_api_calls
    self._action_location = action_location
    self._resource_ref_resolver = resource_ref_resolver
    self._debug = debug

    self._user_input_already_given = False
    self._exit_was_handled = False

    self._orig_request_method = httplib2.Http.request
    self._request_patch = mock.patch.object(
        httplib2.Http,
        'request',
        autospec=True,
        side_effect=self._HandleRequest)
    # pylint:disable=protected-access
    self._orig_batch_request_method = batch.BatchHttpRequest._Execute
    self._batch_request_patch = mock.patch.object(
        batch.BatchHttpRequest,
        '_Execute',
        autospec=True,
        side_effect=self._HandleBatchRequest)

    self._orig_stdout_write = sys.stdout.write
    self._captured_stdout = ''
    self._stdout_patch = mock.patch.object(
        sys.stdout, 'write', autospec=True, side_effect=self._HandleStdout)

    self._orig_stderr_write = sys.stderr.write
    self._captured_stderr = ''
    self._stderr_patch = mock.patch.object(
        sys.stderr, 'write', autospec=True, side_effect=self._HandleStderr)

    self._orig_file_writer = files.FileWriter
    self._file_writer_patch = mock.patch.object(
        files, 'FileWriter', autospec=True, side_effect=self._HandleFileWrite)
    self._orig_binary_file_writer = files.BinaryFileWriter
    self._binary_file_writer_patch = mock.patch.object(
        files, 'BinaryFileWriter',
        autospec=True, side_effect=self._HandleBinaryFileWrite)

    self._orig_input = console_io._GetInput
    self._stdin_patch = mock.patch.object(
        console_io, '_GetInput',
        autospec=True, side_effect=self._HandleUserInput)

    self._exit_patch = mock.patch.object(
        calliope_exceptions, '_Exit',
        side_effect=self._HandleExit)
    # We don't do any handling here, we just don't want the error message to
    # get logged.
    self._log_error_patch = mock.patch.object(calliope_exceptions,
                                              '_LogKnownError')

  def _Debug(self, msg, *args):
    if not self._debug:
      return
    sys.__stderr__.write(msg.format(*args) + '\n')

  def _Handle(self, event, *args, **kwargs):
    self._failures.AddAll(event.Handle(*args, **kwargs))

  @property
  def _next_event(self):
    """Gets the event that is queued to be used next.

    All of this is basically to ensure the events are loaded from the generator
    as late as possible. The loading of some events depend on things from
    previous event executions.

    Returns:
      Event, The next event or None if there are no more events.
    """
    if self.__next_event is None:
      try:
        self.__next_event = next(self._events_generator)
      except StopIteration:
        self.__next_event = Session.DONE
    if self.__next_event == Session.DONE:
      return None
    return self.__next_event

  @property
  def _last_event(self):
    """Gets the event that was last processed."""
    if self._processed_events:
      return self._processed_events[-1]
    return None

  def _ConsumeEvent(self):
    """Moves the next event to the list of processed events."""
    current_event = self.__next_event
    self._InsertEvent(self.__next_event)
    self.__next_event = None
    return current_event

  def _InsertEvent(self, event):
    """Inserts a new event at the end of the processed list."""
    self._processed_events.append(event)

  def _GetOrCreateNextEvent(self, expected_type):
    """Gets the next event or creates a new one if the next one doesn't match.

    Args:
      expected_type: events_lib.Event, The type of event that should be next.

    Returns:
      events_lib.Event: The event to use.
    """
    self._Debug('Looking for event of type: [{}]', expected_type)

    # Throw out any optional api_call events that were not used.
    if expected_type != events_lib.EventType.API_CALL:
      while (self._next_event and
             self._next_event.EventType() == events_lib.EventType.API_CALL and
             self._next_event.IsOptional()):
        self._ConsumeEvent()

    # If API calls are being ignored, we never intercept those events. Just
    # ignore any api_call events we find in the stream.
    if self._ignore_api_calls:
      while (self._next_event and
             self._next_event.EventType() == events_lib.EventType.API_CALL):
        self._ConsumeEvent()

    if self._next_event and self._next_event.EventType() == expected_type:
      self._Debug('  Found matching event: [{}]', self._next_event)
      return self._ConsumeEvent()

    # No more events or the wrong event type.
    if self._next_event:
      location = self._next_event.UpdateContext().Location()
      self._Debug('  Found wrong type: [{}] at [{}]',
                  self._next_event.EventType(), location)
    elif self._last_event:
      location = self._last_event.UpdateContext().Location()
    else:
      location = self._action_location

    current_event = expected_type.Impl().ForMissing(location)
    self._Debug('  Inserting missing event')
    self._InsertEvent(current_event)
    return current_event

  def _HandleRequest(self, self_, *args, **kwargs):
    """Mock http request function."""
    request = events_lib.Request.FromRequestArgs(*args, **kwargs)
    if self._processing_batch_request:
      # When in batch mode, effectively unmock the http request method because
      # we are intercepting elsewhere.
      return self._MakeRealRequest(self_, *args, **kwargs).ToTransportResponse()

    self._ProcessStdout()
    self._ProcessStderr()

    # These modes have a bunch in common, but it is clearer to split them than
    # have a bunch of if/else switches.
    if self._execution_mode == ExecutionMode.LOCAL:
      return self._HandleRequestLocal(request).ToTransportResponse()

    # For remote mode, make the actual call and then process the result.
    response = self._MakeRealRequest(self_, *args, **kwargs)
    return self._HandleRequestRemote(request, response).ToTransportResponse()

  def _MakeRealRequest(self, self_, *args, **kwargs):
    """Convenience for mocking during testing."""
    transport_response = self._orig_request_method(self_, *args, **kwargs)
    return events_lib.Response.FromTransportResponse(transport_response)

  def _HandleBatchRequest(self, self_, *args, **kwargs):
    """Mock apitools batch request.

    Batch requests are difficult to deal with so instead of saving them as a
    batch we intercept the call and split the batch out into its constituent
    calls for the purposes of the scenario.

    Args:
      self_: The apitools BatchRequest object this is mocked into.
      *args: Arguments to the underlying method.
      **kwargs: Arguments to the underlying method.
    """
    self._ProcessStdout()
    self._ProcessStderr()

    self._processing_batch_request = True
    try:
      # In local mode we don't have to make any calls or execute the batch
      # since we already have the canned data to return.
      if self._execution_mode == ExecutionMode.LOCAL:
        # Reach into the batch request and pull out the individual requests.
        # pylint: disable=protected-access, This isn't great because we are
        # reaching deeply into apitools, but since this is only part of a
        # testing framework, it's OK.
        for key, request_response in sorted(
            self_._BatchHttpRequest__request_response_handlers.items()):
          # request_response has the form (request, response, handler)
          apitools_request = request_response[0]
          request = events_lib.Request.FromApitoolsRequest(apitools_request)
          # Handle each request in the batch as if it was called directly.
          response = self._HandleRequestLocal(request)
          headers = response.headers.copy()
          headers['status'] = response.status
          body = response.body

          # Construct and save the batch response for this request based on the
          # canned data we have saved.
          response = http_wrapper.Response(headers, body,
                                           self_._BatchHttpRequest__batch_url)
          # Save the responses into to the tuple stored in the batch request
          # object. This code is the same as in BatchHttpRequest object
          # so the end result is a properly mocked out batch request.
          self_._BatchHttpRequest__request_response_handlers[key] = (
              self_._BatchHttpRequest__request_response_handlers[key]._replace(
                  response=response))
      else:
        # In remote mode, we actually want to make the real call. Call the
        # underlying request method to execute the batch.
        self._orig_batch_request_method(self_, *args, **kwargs)
        # At this point, the batch request has already saved the individual
        # responses back into the data structure with each request.
        # pylint: disable=protected-access
        for key, request_response in sorted(
            self_._BatchHttpRequest__request_response_handlers.items()):
          # Pull out all the individual request/responses and process them
          # as if they were called individually.
          apitools_request, apitools_response = (request_response[0],
                                                 request_response[1])
          self._HandleRequestRemote(
              events_lib.Request.FromApitoolsRequest(apitools_request),
              events_lib.Response.FromApitoolsResponse(apitools_response))
    finally:
      self._processing_batch_request = False

  def _GetOperationIfPollingRequest(self, request):
    for e in self._processed_events:
      if e.EventType() == events_lib.EventType.API_CALL:
        op = e.GetMatchingOperationForRequest(request)
        if op:
          return op
    return None

  def _HandleRequestLocal(self, request):
    """Handle a local request by using canned response data."""
    self._Debug('Handling API request: [{}]', request.uri)

    # This is a polling request for an operation we got back previously. Have
    # the operation generate a fake response.
    op = self._GetOperationIfPollingRequest(request)
    if op:
      return op.Respond()

    # Find the correct event to use and validate the request assertions.
    current_event, failures = self._HandleRequestHelper(request, None)
    self._failures.AddAll(failures)
    # Use canned response data or pause if no response is registered.
    if current_event.UpdateContext().WasMissing():
      raise PauseError(
          'Pausing execution so API response can be added to expect_api_call '
          'at location: {}'.format(current_event.UpdateContext().Location()))

    response = current_event.GetResponse()
    # Validate the response assertions now that we have a response.
    self._failures.AddAll(
        current_event.HandleResponse(response, self._resource_ref_resolver))
    return response

  def _HandleRequestRemote(self, request, response):
    """Handle a remote request by making a real API call."""
    self._Debug('Handling API request: [{}]', request.uri)
    self._Debug('  Method: [{}]', request.method)
    self._Debug('  Body: [{}]', request.body)
    self._Debug('  Response Body: [{}]', response.body)

    # This is a polling request for an operation we got back previously. No
    # need to do any more validation, just return the real API response.
    op = self._GetOperationIfPollingRequest(request)
    if op:
      return response

    event, failures = self._HandleRequestHelper(request, response)
    self._failures.AddAll(failures)
    # Update the canned response data.
    if self._failures.ShouldUpdateResponsePayloads():
      self._failures.AddAll(event.UpdateResponsePayload(response))
    return response

  def _HandleRequestHelper(self, request, response):
    """Helper to figure out which event to use for the call."""
    if (self._last_event and
        self._last_event.EventType() == events_lib.EventType.API_CALL and
        self._last_event.CanBeRepeated()):
      # The last event was an api_call. Attempt to reuse it if it matches.
      failures = self._GetApiCallFailures(
          self._last_event, request, response, dry_run=True)
      if not failures or self._last_event.MatchesPreviousCall(
          request, response):
        self._Debug('Found matching repeatable event for [{}]', request.uri)
        self._last_event.MarkRepeated()
        failures.extend(self._last_event.CheckRepeatable())
        return (self._last_event, failures)
      else:
        self._Debug('No matching repeatable event for [{}]', request.uri)

    # No matching repeatable event, get a new one.
    current_event = self._GetOrCreateNextEvent(events_lib.EventType.API_CALL)
    failures = self._GetApiCallFailures(
        current_event, request, response, dry_run=True)
    while failures and current_event.IsOptional():
      # If the request and response assertions don't exactly match, and if the
      # current event is optional, just skip it and use the next event to
      # process this request.
      self._Debug('Skipping optional api_call event: [{}]', current_event)
      current_event = self._GetOrCreateNextEvent(events_lib.EventType.API_CALL)
      failures = self._GetApiCallFailures(
          current_event, request, response, dry_run=True)

    failures = self._GetApiCallFailures(
        current_event, request, response, dry_run=False)
    current_event.MarkCalledWith(request, response)
    return (current_event, failures)

  def _GetApiCallFailures(self, event, request, response, dry_run):
    """Gets assertion failures for a given request/response."""
    failures = []
    # Validate the request assertions.
    failures.extend(event.Handle(request, dry_run))
    # Validate the response assertions only if we are in REMOTE mode and we have
    # a response to validate.
    if response is not None:
      generate_extras = not dry_run
      failures.extend(
          event.HandleResponse(response, self._resource_ref_resolver, dry_run,
                               generate_extras))
    return failures

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
    current_event = self._GetOrCreateNextEvent(ux_type)
    self._Handle(current_event, ux_json_data)

    if ux_type.HasUserInput():
      self._stream_mocker.stdin_writer(current_event.UserInput())
      self._user_input_already_given = True

  def _ProcessStdout(self):
    if not self._captured_stdout:
      return
    current_event = self._GetOrCreateNextEvent(events_lib.EventType.STDOUT)
    self._Handle(current_event, self._captured_stdout)
    self._captured_stdout = ''

  def _ProcessStderr(self):
    if not self._captured_stderr:
      return
    current_event = self._GetOrCreateNextEvent(events_lib.EventType.STDERR)
    self._Handle(current_event, self._captured_stderr)
    self._captured_stderr = ''

  def _HandleFileWrite(self,
                       path,
                       private=False,
                       append=False,
                       create_path=False):
    return self._HandleFileWriteImpl(
        False, path, private=private, append=append, create_path=create_path)

  def _HandleBinaryFileWrite(self, path, private=False, create_path=False):
    return self._HandleFileWriteImpl(
        True, path, private=private, append=False, create_path=create_path)

  @contextlib.contextmanager
  def _HandleFileWriteImpl(self,
                           is_binary,
                           path,
                           private=False,
                           append=False,
                           create_path=False):
    """Intercept calls to write files."""
    abs_path = os.path.abspath(path)

    cwd = os.path.abspath(os.getcwd())
    config_dir = os.path.abspath(config.Paths().global_config_dir)
    home_dir = os.path.abspath(files.GetHomeDir())
    is_known_location = (
        abs_path.startswith(cwd) or abs_path.startswith(home_dir) or
        abs_path.startswith(config_dir))
    # We have to do this because under tests, all the above are actually under
    # the temp directory because they are mocked out.
    temp_dir = os.path.abspath(tempfile.gettempdir())
    is_temp = abs_path.startswith(temp_dir) and not is_known_location
    is_compute_ssh_hosts_file = path.endswith(
        os.path.join('.ssh', 'google_compute_known_hosts'))
    is_null_device = (path == os.devnull)

    if not (is_known_location or is_temp or is_compute_ssh_hosts_file or
            is_null_device):
      raise Error('Command is attempting to write file outside of current '
                  'working directory: [{}]'.format(abs_path))

    # Pass through the write like normal
    if is_binary:
      with self._orig_binary_file_writer(
          path, private=private, create_path=create_path) as fw:
        yield fw
    else:
      with self._orig_file_writer(
          path, private=private, append=append, create_path=create_path) as fw:
        yield fw

    # After they close it, capture what happened.
    if abs_path.startswith(config_dir) or is_temp:
      # Ignore any files written to config or tmp for assertion purposes.
      return

    current_event = self._GetOrCreateNextEvent(
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

      current_event = self._GetOrCreateNextEvent(
          events_lib.EventType.USER_INPUT)

      lines = current_event.Lines()
      if lines:
        self._stream_mocker.stdin_writer(*lines)
      self._Handle(current_event)

    return self._orig_input()

  def _HandleExit(self, exc):
    self._ProcessStdout()
    self._ProcessStderr()

    current_event = self._GetOrCreateNextEvent(events_lib.EventType.EXIT)
    self._Handle(current_event, exc)
    self._exit_was_handled = True

  def __enter__(self):
    self._stdout_patch.start()
    self._stderr_patch.start()
    self._stdin_patch.start()
    if not self._ignore_api_calls:
      self._request_patch.start()
      self._batch_request_patch.start()
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
    if not self._ignore_api_calls:
      self._request_patch.stop()
      self._batch_request_patch.stop()
    self._file_writer_patch.stop()
    self._binary_file_writer_patch.stop()
    self._exit_patch.stop()
    self._log_error_patch.stop()

    # TODO(b/116717592): Refactor context manager top properly handle crashes.
    error_handled = False  # surpress error propagation
    if not self._exit_was_handled and not (exc_val and isinstance(
        exc_val, (Error, reference_resolver.Error, events_lib.Error))):
      # If we get here, there is either no exception or it is not an exception
      # type known to calliope (it would be a crash), since that would have been
      # handled by a intercepted call to _Handlexit already.
      # Framework errors should not be handled here as they represent errors in
      # the test, not in the running command.
      self._HandleExit(exc_val)
      error_handled = True

    # Consume the rest of events so they get into the processed events stream.
    # If there is no exception, the additional events were not used and should
    # be failures.
    while self._next_event:
      if exc_type is None:
        self._failures.Add(
            assertions.Failure.ForExtraAssertion(
                self._next_event.UpdateContext()))
      self._ConsumeEvent()
    return error_handled

  def GetEventSequence(self):
    return [
        event.UpdateContext().BackingData()
        for event in self._processed_events
        if event is not None
    ]
