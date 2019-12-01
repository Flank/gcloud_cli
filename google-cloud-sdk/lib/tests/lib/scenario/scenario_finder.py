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

"""Utility to locate scenario tests that exist in the surface test tree."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import yaml
import tests
import tests.e2e.surface
from tests.lib import sdk_test_base
import tests.unit.surface


class ScenarioConfig(object):

  def __init__(self, name, resource_path, tracks, filter_data):
    self.name = name
    self.resource_path = resource_path
    self.tracks = tracks
    self.filter_data = filter_data

  def __str__(self):
    return self.resource_path


def FindScenarioTests(prefixes=None):
  """Locate all the scenario tests that exist in the surface unit test tree.

  Args:
    prefixes: [str], An optional list of module prefixes to filter to
      (ex. unit.surface.iot.registries).

  Returns:
    ([ScenarioConfig], [ScenarioConfig]), The unit and e2e scenario tests
    configurations that were found.
  """
  unit_scenarios = _Find(
      prefixes, os.path.dirname(tests.unit.surface.__file__))
  e2e_scenarios = _Find(
      prefixes, os.path.dirname(tests.e2e.surface.__file__))
  return unit_scenarios, e2e_scenarios


def _Find(prefixes, scenario_root):
  """Find scenarios that match the given prefixes and execution mode."""
  module_root = os.path.dirname(tests.__file__)
  code_root = os.path.dirname(module_root)

  scenarios = []
  for root, _, files in os.walk(scenario_root):
    for f in files:
      if f.endswith('scenario.yaml'):
        file_path = os.path.join(root, f)
        name = (file_path[len(scenario_root) + 1:]
                .replace('.scenario.yaml', '')
                .replace('\\', '/'))
        if _MatchesPrefix(prefixes, file_path[len(module_root) + 1:]):
          resource_path = file_path[len(code_root) + 1:]
          spec_data = LoadYAMLFile(resource_path)
          tracks = GetTracks(spec_data)
          scenarios.append(ScenarioConfig(
              name, resource_path, tracks, spec_data.get('filters')))
  return scenarios


def _MatchesPrefix(prefixes, relative_path):
  if not prefixes:
    return True
  module_path = relative_path.replace('/', '.').replace('\\', '.')
  for prefix in prefixes:
    if module_path.startswith(prefix):
      return True
  return False


def LoadYAMLFile(path):
  full_path = sdk_test_base.SdkBase.Resource(path)
  return yaml.load_path(full_path, round_trip=True, version=yaml.VERSION_1_2)


def GetTracks(spec_data):
  return ([calliope_base.ReleaseTrack.FromId(t)
           for t in spec_data.get('release_tracks') or ['GA']])
