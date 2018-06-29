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

import abc
import io
import os
import sys

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import pkg_resources
from tests.lib.scenario import assertions
from tests.lib.scenario import events
from tests.lib.scenario import session
from tests.lib.scenario import updates

import jsonschema
import six


_SCENARIO_SCHEMA_FILE_NAME = 'scenario_schema.yaml'
_SCENARIO_SCHEMA_PATH = (os.path.join(os.path.dirname(__file__),
                                      _SCENARIO_SCHEMA_FILE_NAME))


class Error(Exception):
  """Base exception for the module."""
  pass


class ScenarioContext(object):
  """A holder for things from a test_base that the scenario needs to run.

  Attributes:
    full_spec_path: str, The absolute path to the file that the spec was loaded
      from.
    spec_data: The parsed spec data.
    update_modes: [updates.Mode], The list of enabled update modes for this
      scenario run.
    stream_mocker: session.StreamMocker, The holder for mock streams to event
      handling.
    command_executor: f([str]), The function to call to execute a command.
  """

  def __init__(self, full_spec_path, spec_data, update_modes, stream_mocker,
               command_executor):
    self.full_spec_path = full_spec_path
    self.spec_data = spec_data
    self.update_modes = update_modes
    self.stream_mocker = stream_mocker
    self.command_executor = command_executor


class Scenario(object):
  """Holds the entire scenario spec."""

  @classmethod
  def FromData(cls, data):
    """Build the object from spec data."""

    scenario_actions = []
    for a in data.get('actions') or []:
      if 'set_property' in a:
        scenario_actions.append(SetPropertyAction.FromData(a))
      elif 'execute_command' in a:
        scenario_actions.append(CommandExecutionAction.FromData(a))
      else:
        # This will never happen if schema passes validation.
        raise ValueError('Unknown action type: {}'.format(a))

    return cls(
        title=data.get('title'),
        description=data.get('description'),
        actions=scenario_actions,
    )

  def __init__(self, title, description, actions):
    self.title = title
    self.description = description
    self.actions = actions


class Action(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for all actions."""

  @abc.abstractmethod
  def Execute(self, scenario_context):
    pass


class SetPropertyAction(Action):
  """Action that sets properties."""

  @classmethod
  def FromData(cls, data):
    return cls(data.get('set_property', {}))

  def __init__(self, props):
    self.properties = props

  def Execute(self, scenario_context):
    del scenario_context
    for p, v in six.iteritems(self.properties):
      properties.FromString(p).Set(v)


class CommandExecutionAction(Action):
  """Action that runs a command and validates assertions about its execution."""

  @classmethod
  def FromData(cls, data):
    """Build the object from spec data."""
    command_execution_data = data.get('execute_command')

    command_events = []
    for e in command_execution_data.get('events') or []:
      if 'api_call' in e:
        command_events.append(events.ApiCallEvent.FromData(e))
      elif 'expect_stdout' in e:
        command_events.append(events.StdoutEvent.FromData(e))
      elif 'expect_stderr' in e:
        command_events.append(events.StderrEvent.FromData(e))
      elif 'user_input' in e:
        command_events.append(events.UserInputEvent.FromData(e))
      elif 'expect_exit_code' in e:
        command_events.append(events.ExitEvent.FromData(e))
      elif 'expect_progress_bar' in e:
        command_events.append(events.ProgressBarEvent.FromData(e))
      elif 'expect_progress_tracker' in e:
        command_events.append(events.ProgressTrackerEvent.FromData(e))
      else:
        # This will never happen if schema passes validation.
        raise ValueError('Unknown event type: {}'.format(e))

    return cls(
        command_execution_data['command'],
        command_events,
        command_execution_data,
    )

  def __init__(self, command, command_events, original_event_data):
    self.command = command
    self.events = command_events
    self._original_data = original_event_data

  def Execute(self, scenario_context):
    update_modes = scenario_context.update_modes
    stream_mocker = scenario_context.stream_mocker

    event_data = None
    try:
      with assertions.FailureCollector(update_modes=update_modes) as failures:
        with session.Session(self.events, failures, stream_mocker) as s:
          code = 0
          try:
            # TODO(b/78588819): Fix the error handling here. We want the later
            # assertions to trigger even if there are errors here, but we also
            # need to make sure we do all the updates correctly.
            scenario_context.command_executor(self.command)
          except exceptions.Error:
            code = 1

          s.HandleExit(code)
          event_data = s.GetEventSequence()
    finally:
      # Update spec file
      if update_modes or (update_modes is None and updates.Mode.Current()):
        if event_data is not None:
          self._SetEventData(scenario_context, event_data)

    remaining_stdin = sys.stdin.read()
    if remaining_stdin:
      raise Error('Not all stdin was consumed: [{}]'.format(remaining_stdin))

  def _SetEventData(self, scenario_context, new_event_data):
    event_data = [e for e in new_event_data if e]
    self._original_data['events'] = event_data
    with io.open(scenario_context.full_spec_path, 'wt') as f:
      yaml.dump(scenario_context.spec_data, f, round_trip=True)


class Validator(object):
  """Validates an individual scenario instance."""

  def __init__(self, test_data):
    self.schema = yaml.load(pkg_resources.GetResourceFromFile(
        _SCENARIO_SCHEMA_PATH))
    self.test_data = test_data

  def ValidateSchema(self):
    """Validate scenario against scenario language schema."""
    try:
      jsonschema.validate(self.test_data, self.schema)
      return True
    except jsonschema.exceptions.ValidationError as ve:
      sys.__stderr__.write(
          'ERROR: Schema validation failed: {}\n\n'.format(ve))

      if ve.cause:
        additional_exception = 'Root Exception: {}'.format(ve.cause)
      else:
        additional_exception = ''

      root_error = ve.context[-1]
      error_path = ''.join(
          ('[{}]'.format(elem) for elem in root_error.absolute_path))

      sys.__stderr__.write(
          'Additional Details:\n'
          'Error Message: {msg}\n\n'
          'Failing Validation Schema: {schema}\n\n'
          'Failing Element: {instance}\n\n'
          'Failing Element Path: {path}\n\n'
          '{additional_cause}\n'.format(
              msg=root_error.message,
              instance=root_error.instance,
              schema=root_error.schema,
              path=error_path,
              additional_cause=additional_exception))
      return False

  def Validate(self):
    return self.ValidateSchema()
