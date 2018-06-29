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

"""Utility to locate scenario tests that exist in the surface test tree."""

from __future__ import absolute_import
from __future__ import unicode_literals

import os

import tests.unit.surface


def FindScenarioTests(prefixes=None):
  """Locate all the scenario tests that exist in the surface unit test tree.

  Args:
    prefixes: [str], An optional list of prefixes to filter to. These prefixes
      are from the root of the surface directory (ex iot/registries/).

  Returns:
    [str], The list of paths relative to the tests/unit/surface/ directory
    for all the matching scenario tests.
  """
  scenarios = []
  scenario_root = os.path.dirname(tests.unit.surface.__file__)
  prefix_len = len(scenario_root)
  for root, _, files in os.walk(scenario_root):
    for f in files:
      if f.endswith('scenario.yaml'):
        file_path = os.path.join(root, f)
        relative_path = file_path[prefix_len + 1:]
        if not prefixes:
          scenarios.append(relative_path)
        else:
          for prefix in prefixes:
            if relative_path.startswith(prefix):
              scenarios.append(relative_path)
  return scenarios
