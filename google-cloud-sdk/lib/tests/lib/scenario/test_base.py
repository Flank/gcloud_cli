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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.scenario import schema
from tests.lib.scenario import session
from tests.lib.scenario import updates


class _LocalOnly(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  pass


class _MakeAPICalls(e2e_base.WithServiceAuth):

  def SetUp(self):
    properties.VALUES.core.project.Set('cloudsdktest')


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


def LoadTracksFromFile(spec_path):
  full_spec_path = sdk_test_base.SdkBase.Resource(spec_path)
  spec_data = yaml.load_path(full_spec_path, round_trip=True)
  return [calliope_base.ReleaseTrack.FromId(t)
          for t in spec_data.get('release_tracks') or ['GA']]


class ScenarioTestBase(
    _MakeAPICalls if updates.Mode.MakesApiCalls() else _LocalOnly):
  """A base class for all scenario tests."""

  def RunScenario(self, spec_path, track, update_modes=None):
    full_spec_path = sdk_test_base.SdkBase.Resource(spec_path)
    spec_data = yaml.load_path(full_spec_path, round_trip=True)
    validator = schema.Validator(spec_data)
    self.assertTrue(validator.Validate())

    spec = schema.Scenario.FromData(spec_data)

    self.track = track
    stream_mocker = CreateStreamMocker(self)

    scenario_context = schema.ScenarioContext(
        full_spec_path, spec_data, update_modes, stream_mocker, self.Run)

    for a in spec.actions:
      a.Execute(scenario_context)


def main():
  return cli_test_base.main()
