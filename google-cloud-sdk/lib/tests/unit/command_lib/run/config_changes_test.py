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
"""Tests for config_changes.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run import config_changes
from tests.lib import test_case
import mock


class ConfigChangesTest(test_case.TestCase):

  def SetUp(self):
    self.config = mock.Mock()
    self.config.env_vars = {'k1': 'v1', 'k2': 'v2'}
    self.metadata = mock.Mock()

  def testEnvUpdate(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'})
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(
        self.config.env_vars, {'k1': 'x1', 'k2': 'v2', 'k3': 'v3'})

  def testEnvRemove(self):
    env_change = config_changes.EnvVarChanges(env_vars_to_remove=['k1'])
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(self.config.env_vars, {'k2': 'v2'})

  def testEnvUpdateRemove(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        env_vars_to_remove=['k1'])
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(
        self.config.env_vars, {'k1': 'x1', 'k2': 'v2', 'k3': 'v3'})

  def testEnvSet(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        clear_others=True)
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(self.config.env_vars, {'k1': 'x1', 'k3': 'v3'})

# TODO(b/112157693): Add tests for ConcurrencyChanges and ResourceChanges.
