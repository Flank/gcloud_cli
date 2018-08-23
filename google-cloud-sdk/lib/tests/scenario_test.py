# -*- coding: utf-8 -*- #
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

"""A stub to help with running scenarios in an IDE.

By default, this runs all scenario tests that exist. Put a prefix in the
variable below to restrict the run to only a specific set of tests. Paths are
relative to the tests/scenario/ directory.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from tests.lib import e2e_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib.scenario import scenario_finder
from tests.lib.scenario import session
from tests.lib.scenario import test_base
from tests.lib.scenario import updates


SCENARIO_PREFIXES = os.environ.get(
    'CLOUDSDK_SCENARIO_TESTING_PREFIXES', '').split(' ')
EXECUTION_MODE = session.ExecutionMode[
    os.environ.get('CLOUDSDK_SCENARIO_TESTING_EXECUTION_MODE') or 'REMOTE']
UPDATE_MODES = updates.Mode.FromEnv()


# Uncomment these lines to override the values.
# SCENARIO_PREFIXES = ['e2e.surface.sql']
# EXECUTION_MODE = session.ExecutionMode.REMOTE
# UPDATE_MODES = [
#   updates.Mode.UX,
#   updates.Mode.RESULT,
#   updates.Mode.API_REQUESTS,
#   updates.Mode.API_RESPONSE_PAYLOADS,
# ]


class _GlobalDataHolder(object):
  """A global data holder for the auto-generated tests.

  This is not best practice, but is the only reasonable way we can have a test
  generated for each scenario we want to validate. The general approach is
  to search the scenario tree for all tests and compile a list of all those that
  exist while this module is being loaded. That allows us to use that list
  as the seed to parameterize the test in the next class.

  We can't do this during test run time, because once tests are running, pytest
  has already loaded the test suite and further modifying it does not have any
  effect. It must be modified during module load time.
  """

  def __init__(self):
    self.unit_scenarios, self.e2e_scenarios = (
        scenario_finder.FindScenarioTests(SCENARIO_PREFIXES))
    if not (self.unit_scenarios or self.e2e_scenarios):
      sys.__stderr__.write(
          'ERROR: No scenarios found matching the given prefix\n')
      sys.exit(1)
    else:
      sys.__stderr__.write('Execution Mode: [{}]\n'.format(EXECUTION_MODE.name))
      sys.__stderr__.write('Update Mode: [{}]\n'.format(
          ', '.join([str(m) for m in UPDATE_MODES])))
      sys.__stderr__.write('Found UNIT Scenarios:\n')
      for s in self.unit_scenarios:
        sys.__stderr__.write('\t{}\n'.format(s))
      sys.__stderr__.write(
          'Found E2E Scenarios (Running as {}):\n'.format(EXECUTION_MODE.name))
      for s in self.e2e_scenarios:
        sys.__stderr__.write('\t{}\n'.format(s))

  def TestParamsUnit(self):
    # Unit tests always run as LOCAL no matter what mode is requested.
    return self._TestParams(self.unit_scenarios)

  def TestParamsE2EAsUnit(self):
    # If LOCAL is requested, run all e2e tests as LOCAL tests.
    if EXECUTION_MODE == session.ExecutionMode.LOCAL:
      return self._TestParams(self.e2e_scenarios)
    # Otherwise they will be run as REMOTE tests instead.
    return []

  def TestParamsE2E(self):
    # If REMOTE is requested, run all e2e tests as REMOTE tests.
    if EXECUTION_MODE == session.ExecutionMode.REMOTE:
      return self._TestParams(self.e2e_scenarios)
    # Otherwise they will be run as LOCAL tests instead.
    return []

  def _TestParams(self, configs):
    """Generates parameterized test params for all the discovered scenarios."""
    tests = []
    for config in configs:
      for track in config.tracks:
        test_name = '_' + config.name + '/' + track.id.title()
        tests.append((test_name, config.resource_path, track))
    return tests


DATA = _GlobalDataHolder()


class Unit(test_base.ScenarioTestBase,
           sdk_test_base.WithFakeAuth,
           parameterized.TestCase):
  """Unit tests all go here (unit tests cannot be run as REMOTE)."""

  @parameterized.named_parameters(
      DATA.TestParamsUnit() or [('_NoOp', None, None)])
  def test(self, spec_path, track):
    if spec_path:
      self.RunScenario(spec_path, track, session.ExecutionMode.LOCAL,
                       UPDATE_MODES)


class E2ELocal(test_base.ScenarioTestBase,
               sdk_test_base.WithFakeAuth,
               parameterized.TestCase):
  """Tests that can be run REMOTE go here when LOCAL mode is requested."""

  def Project(self):
    # pylint:disable=protected-access
    return e2e_base._TEST_CONFIG['property_overrides']['project']

  @parameterized.named_parameters(
      DATA.TestParamsE2EAsUnit() or [('_NoOp', None, None)])
  def test(self, spec_path, track):
    if spec_path:
      self.RunScenario(spec_path, track, session.ExecutionMode.LOCAL,
                       UPDATE_MODES)


class E2ERemote(test_base.ScenarioTestBase,
                e2e_base.WithServiceAuth,
                parameterized.TestCase):
  """Tests that can be run REMOTE go here when REMOTE mode is requested."""

  @parameterized.named_parameters(
      DATA.TestParamsE2E() or [('_NoOp', None, None)])
  def test(self, spec_path, track):
    if spec_path:
      self.RunScenario(spec_path, track, session.ExecutionMode.REMOTE,
                       UPDATE_MODES)


if __name__ == '__main__':
  test_base.main()
