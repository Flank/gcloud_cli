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
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

from tests.lib import parameterized
from tests.lib.scenario import assertions
from tests.lib.scenario import test_base
import tests.scenario


SCENARIO_PREFIXES = os.environ.get(
    'CLOUDSDK_SCENARIO_TESTING_PREFIXES', ''.split(','))
UPDATE_MODES = None  # Will default to environment.


# Uncomment these lines to override the values.
# SCENARIO_PREFIXES = ['iot/']
# UPDATE_MODES = [
#    assertions.UpdateMode.UX,
#    assertions.UpdateMode.RESULT,
#    assertions.UpdateMode.API_REQUESTS,
#    assertions.UpdateMode.API_RESPONSES,
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
  SCENARIOS = []
  scenario_root = os.path.dirname(tests.scenario.__file__)
  prefix_len = len(scenario_root)
  for root, _, files in os.walk(scenario_root):
    for f in files:
      if f.endswith('scenario.yaml'):
        file_path = os.path.join(root, f)
        relative_path = file_path[prefix_len + 1:]
        if not SCENARIO_PREFIXES:
          SCENARIOS.append(relative_path)
        else:
          for prefix in SCENARIO_PREFIXES:
            if relative_path.startswith(prefix):
              SCENARIOS.append(relative_path)
  if not SCENARIOS:
    print('ERROR: No scenarios found matching the given prefix')
    sys.exit(1)
  else:
    print('Found Scenarios:')
    for s in SCENARIOS:
      print('\t%s' % s)
    print('Update Mode: [%s]' %
          ', '.join([str(m) for m in assertions.UpdateMode.Current()]))


class ScenarioRunner(test_base.ScenarioTestBase, parameterized.TestCase):

  @parameterized.named_parameters(
      [('_' + path.replace('.scenario.yaml', '').title(), path)
       for path in _GlobalDataHolder.SCENARIOS])
  def test(self, path):
    scenario_file = self.Resource('tests/scenario/' + path)
    self.RunScenario(scenario_file, update_modes=UPDATE_MODES)


if __name__ == '__main__':
  test_base.main()
