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

"""A base class for scenario tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.scenario import assertions
from tests.lib.scenario import schema
from tests.lib.scenario import session


class _LocalOnly(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  pass


class _MakeAPICalls(e2e_base.WithServiceAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set('cloudsdktest')


class ScenarioTestBase(
    _MakeAPICalls if assertions.UpdateMode.MakesApiCalls() else _LocalOnly):
  """A base class for all scenario tests."""

  def _GetStdout(self):
    data = self.GetOutput()
    self.ClearOutput()
    return data

  def _GetStderr(self):
    data = self.GetErr()
    self.ClearErr()
    return data

  def _WriteStdin(self, *lines):
    self.WriteInput(*lines)

  def RunScenario(self, spec_path, update_modes=None):
    full_spec_path = self.Resource(spec_path)
    spec_data = yaml.load_path(full_spec_path, round_trip=True)
    spec = schema.Scenario.FromData(spec_data)

    stream_mocker = session.StreamMocker(
        self._GetStdout, self._GetStderr, self._WriteStdin)

    for ce in spec.command_executions:
      # Set up test data input files
      # TODO(b/78588819): Support input files.

      event_data = []
      try:
        with assertions.FailureCollector(update_modes=update_modes) as failures:
          with session.Session(
              ce.events, failures, update_modes=update_modes,
              stream_mocker=stream_mocker) as s:
            code = 0
            try:
              # TODO(b/78588819): Fix the error handling here. We want the later
              # assertions to trigger even if there are errors here, but we also
              # need to make sure we do all the updates correctly.
              self.Run(ce.command)
            except exceptions.Error:
              code = 1

            s.HandleExit(code)
            event_data = s.GetEventSequence()
      finally:
        # Update spec file
        if update_modes or (
            update_modes is None and assertions.UpdateMode.Current()):
          if event_data:
            ce.original_event_data[:] = event_data
          with io.open(full_spec_path, 'wt') as f:
            yaml.dump(spec_data, f, round_trip=True)

      remaining_stdin = self.stdin.read()
      if remaining_stdin:
        self.fail('Not all stdin was consumed: [{}]'.format(remaining_stdin))


def main():
  return cli_test_base.main()
