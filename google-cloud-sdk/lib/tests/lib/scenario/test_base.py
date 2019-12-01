# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""A base class for scenario tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import OrderedDict
import functools
import inspect
import json
import re
import subprocess
import sys

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry
from tests.lib import cli_test_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.scenario import assertions
from tests.lib.scenario import schema
from tests.lib.scenario import session

from ruamel.yaml import comments
import six

_RESTRICTION_ARG_COUNT = 1
_SKIP_ARG_COUNT = 2


def _GetMethodArgs(method):
  """Returns a list of the arguments in a method's signature."""
  if six.PY2:
    return inspect.getargspec(method).args  # getargspec is deprecated in PY3.
  else:
    return inspect.getfullargspec(method).args


def BuildFilterDecorator(filters_data, execution_mode):
  """Constructs an appropriate decorator from the filters provided.

  The result of this function will be used to decorate the test in the
  scenario. If the scenario file contains no filters, then this will simply
  return the identity function. Otherwise, this will return a decorator function
  equivalent to applying all the filters provided. In other words:

    # YAML
    title: Test Something
    filters:
      SkipOnWindows:
        reason: Failing
        bug: b/12345
      RunOnlyOnPy2
        reason: Deprecated feature
    ...

  is equivalent to:

    # Python
    @test_case.Filters.RunOnlyOnPy2('Deprecated feature')
    @test_case.Filters.SkipOnWindows('Failing', 'b/12345')
    class TestSomething():
      ...

  Args:
    filters_data: yaml.comments.CommentedMap, The parsed YAML filters data.
    execution_mode: session.ExecutionMode, The mode the test is running in.

  Returns:
    Function with which to decorate the scenario test, formed by successively
    applying each filter specified.
  """
  filters_data = filters_data or {}
  filters = []

  for filter_name, filter_data in six.iteritems(filters_data):
    decorator = getattr(test_case.Filters, filter_name)
    decorator_args = _GetMethodArgs(decorator)
    if len(decorator_args) == _RESTRICTION_ARG_COUNT:
      filters.append(decorator(filter_data['reason']))
    elif len(decorator_args) == _SKIP_ARG_COUNT:
      if (execution_mode != session.ExecutionMode.LOCAL or
          filter_data.get('locally')):
        filters.append(decorator(filter_data['reason'], filter_data['bug']))
    else:
      # This should never happen unless one of the filters' signatures changes.
      raise ValueError(
          'Invalid filter method. Expected 1 or 2 positional args, found {}: '
          '[{}].'.format(len(decorator_args), ', '.join(decorator_args)))

  if not filters:
    return lambda x: x
  return functools.reduce(lambda f1, f2: f2(f1), filters)


def CreateStreamMocker(test_base_instance):
  """Make a stream mocker that points to the given test base instance."""

  def _GetStdout():
    data = test_base_instance.GetOutput()
    test_base_instance.ClearOutput()
    return data

  def _GetStderr():
    data = test_base_instance.GetErr()
    test_base_instance.ClearErr()
    return data

  def _WriteStdin(*lines):
    test_base_instance.WriteInput(*lines)

  return session.StreamMocker(_GetStdout, _GetStderr, _WriteStdin)


class ScenarioTestBase(cli_test_base.CliTestBase, sdk_test_base.WithTempCWD):
  """A base class for all scenario tests."""

  def RunScenario(self, spec_path, track, execution_mode, update_modes,
                  debug=False):
    full_spec_path = sdk_test_base.SdkBase.Resource(spec_path)
    spec_data = yaml.load_path(
        full_spec_path, round_trip=True, version=yaml.VERSION_1_2)
    validator = schema.Validator(spec_data)
    try:
      validator.Validate()
    except schema.ValidationError as e:
      self.fail(e)

    spec = schema.Scenario.FromData(spec_data)

    self.track = track
    stream_mocker = CreateStreamMocker(self)

    scenario_context = schema.ScenarioContext(
        spec_path, full_spec_path, spec_data, track, execution_mode,
        update_modes, stream_mocker, self.Run, debug)
    if execution_mode == session.ExecutionMode.LOCAL:
      self.StartObjectPatch(retry, '_SleepMs')

    actions = spec.LoadActions()
    for a in actions:
      try:
        a.Execute(scenario_context)
      except assertions.Error:
        if execution_mode == session.ExecutionMode.REMOTE:
          for c in actions:
            # Iterates over the remaining actions because it is a generator.
            c.ExecuteCleanup(scenario_context)
        # Continue raising the original error.
        raise

    if update_modes:
      spec.UpdateSummary(scenario_context)


# pylint: disable=protected-access, This is really dirty stuff, but it's ok,
# (see class comment).
class Interceptor(sdk_test_base.SdkBase):
  """A temporary helper shim to convert existing Python tests to scenarios.

  There is nothing best practice about any of the code in here, but this it not
  actually used as part of tests. It is only a helper to help people manually
  convert existing tests into scenario yaml files. Each test class becomes a
  scenario file, with each test corresponding to a command_execution event
  in the scenario.

  The basic usage is:
    - On the test class you want to convert, extend this class (in addition
      to whatever is there already). For apitools unit tests, use the
      ApiToolsInterceptor below.
    - Remove any release track paramterization.
    - Run the test

  For each test class you modify, a new YAML file will be generated next to
  the Python module.

  This tool does not necessarily capture everything about the test, and you
  should manually edit the test for correctness, but also to ensure that it
  makes sense as a scenario.

  After the test is generated, run the scenario update tool to have it fill in
  the rest of the information. In cases were data is missing, commands might
  error out that you don't intend to (and the assertions will be replaced with
  error assertions). It is recommended that you snapshot the generated file
  before you run the update tool, so you can see the diff after the update to
  make sure it makes sense.

  You should also rename the file, the scenario title, and the comments to
  describe what it is actually doing.
  """
  SCENARIO_DATA = OrderedDict()
  PATH = None

  @staticmethod
  def SetUpClass():
    data = Interceptor.SCENARIO_DATA
    data['title'] = ''
    data['actions'] = []

  def SetUp(self):
    class_name = self.__class__.__name__
    path_parts = self.__module__.split('.')
    # Trim off leading 'googlecloudsdk' and the name of the test file itself
    Interceptor.PATH = (
        self.Resource(*path_parts[1:]) + '.' + class_name + '.scenario.yaml')
    Interceptor.SCENARIO_DATA['title'] = class_name

    self.current_action = None
    self.file_replacements = {}
    self.ref_replacements = {}

    # Intercept command execution so we know what command was run.
    original_run = cli_test_base.CliTestBase.Run
    def InterceptRun(self_, cmd, *args, **kwargs):
      """An override for when self.Run() gets called."""
      self._StartNewCommandExecution()
      command = cmd
      if yaml.list_like(command) or isinstance(command, tuple):
        command = ' '.join(command)
      command = re.sub(r'\s+', ' ', command)
      command = command.replace('\n', ' ').strip()
      for full_path, name in self.file_replacements.items():
        command = command.replace(full_path, name)
      for name, ref in self.ref_replacements.items():
        command = command.replace(name, ref)

      if self.current_action['execute_command']['command']:
        raise ValueError('This test already ran a command')
      self.current_action['execute_command']['command'] = command
      # Add the name of the test as a comment above the action.
      self.current_action['execute_command'].yaml_set_comment_before_after_key(
          'command', before=self._testMethodName, indent=4)
      return original_run.__call__(self_, cmd, *args, **kwargs)
    self.StartObjectPatch(cli_test_base.CliTestBase, 'Run', autospec=True,
                          side_effect=InterceptRun)

    # Intercept file touch to set up files for test input.
    original_touch = test_case.Base.Touch
    def InterceptTouch(self_, directory, name=None, contents='',
                       makedirs=False):
      """An override for when self.Touch() gets called."""
      Interceptor.SCENARIO_DATA['actions'].append({
          'write_file': OrderedDict([('path', name), ('contents', contents)])})
      full_path = original_touch.__call__(
          self_, directory, name, contents, makedirs)
      # Tests need to operate on the full path name, but in the scenario we
      # assume relative paths to CWD. Save the mapping of full path to name so
      # we can sanitize the command arguments later.
      self.file_replacements[full_path] = name
      return full_path
    self.StartObjectPatch(test_case.Base, 'Touch', autospec=True,
                          side_effect=InterceptTouch)

    real_resource_name_generator = e2e_utils.GetResourceNameGenerator
    def InterceptResourceNameGenerator(*args, **kwargs):
      """An override for the e2e resource name generator."""
      prefix = kwargs.get('prefix')
      if prefix is None and args:
        prefix = args[0]
      real_generator = real_resource_name_generator(*args, **kwargs)
      index = 0

      while True:
        index = index + 1
        ref = (prefix if prefix else 'resource') + str(index)
        new_name = next(real_generator)
        self.ref_replacements[new_name] = '$$' + ref + '$$'

        Interceptor.SCENARIO_DATA['actions'].append({
            'generate_resource_id': OrderedDict([
                ('reference', ref),
                ('prefix', prefix)])})
        yield new_name

    self.StartObjectPatch(e2e_utils, 'GetResourceNameGenerator', autospec=True,
                          side_effect=InterceptResourceNameGenerator)

    original_popen = subprocess.Popen
    def InterceptPopen(*args, **kwargs):
      if not (isinstance(args[0], six.string_types) and
              args[0].startswith('uname')):
        # Python runs uname on startup and we don't want to capture that.
        Interceptor.SCENARIO_DATA['actions'].append({
            'execute_binary': OrderedDict([('args', args[0])])})
      return  original_popen.__call__(*args, **kwargs)
    self.StartObjectPatch(subprocess, 'Popen', autospec=True,
                          side_effect=InterceptPopen)

  def _StartNewCommandExecution(self):
    if self.current_action:
      yaml.convert_to_block_text(self.current_action)
      Interceptor.SCENARIO_DATA['actions'].append(self.current_action)
    self.current_action = {'execute_command': comments.CommentedMap(
        [('command', ''), ('events', [])])}

  def TearDown(self):
    self._StartNewCommandExecution()

  @staticmethod
  def TearDownClass():
    # Write the entire scenario file when the entire test class is done.
    yaml.convert_to_block_text(Interceptor.SCENARIO_DATA)
    data = yaml.dump(Interceptor.SCENARIO_DATA, round_trip=True)
    sys.__stderr__.write(data.encode('utf-8') if six.PY2 else data)
    files.WriteFileContents(Interceptor.PATH, data)


class ApiToolsInterceptor(Interceptor):
  """Interceptor that also populates mock responses for calls to apitools mocks.
  """

  def SetUp(self):
    # Intercept apitools mock requests/responses.
    original_call = mock._MockedMethod.__call__
    def InterceptAPI(self_, request, *args, **kwargs):
      """An override for when a apitools mocked method gets called."""
      data = OrderedDict(
          [('api_call', OrderedDict(
              [('expect_request', OrderedDict(
                  [('uri', ''), ('method', ''), ('body', None)])),
               ('return_response', OrderedDict(
                   [('headers', {'status': '200'}), ('body', None)]))]))])

      request_field = self_.method_config().request_field
      request_body = json.loads(encoding.MessageToJson(request))[request_field]

      data['api_call']['expect_request']['body'] = request_body
      try:
        response = original_call.__call__(self_, request, *args, **kwargs)
      except apitools_exceptions.HttpError as e:
        # Test was returning an http error.
        data['api_call']['return_response']['headers'] = {
            'status': e.response['status'], 'reason': e.response['reason']}
        data['api_call']['return_response']['body'] = json.loads(e.content)
        raise
      else:
        # Test returned a non-error response payload.
        response_body = json.loads(encoding.MessageToJson(response))
        data['api_call']['return_response']['body'] = response_body
        return response
      finally:
        self.current_action['execute_command']['events'].append(data)
    self.StartObjectPatch(
        mock._MockedMethod, '__call__', autospec=True, side_effect=InterceptAPI)


def main():
  return cli_test_base.main()
