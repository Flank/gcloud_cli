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
"""Tests for cloudbuild api_lib util functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from tests.lib import sdk_test_base
from tests.lib import test_case


class FieldMappingTest(sdk_test_base.WithTempCWD):
  """Test the ability to normalize config field names.
  """

  def testSnakeToCamelString(self):
    cases = [
        ('_', '_'),
        ('__', '__'),
        ('wait_for', 'waitFor'),
        ('foozleBop', 'foozleBop'),
        ('_xyz', '_xyz'),
        ('__xyz', '__xyz'),
        ('a__b', 'aB'),
    ]
    for input_string, expected in cases:
      self.assertEqual(
          cloudbuild_util.SnakeToCamelString(input_string), expected)

  def testSnakeToCamel(self):
    cases = [
        ({'wait_for': ['x', 'y', 'z']},
         {'waitFor': ['x', 'y', 'z']}),
        ({'super_duper': {'wait_for': ['x', 'y', 'z']}},
         {'superDuper': {'waitFor': ['x', 'y', 'z']}}),
        ({'super_list': [{'wait_for': ['x', 'y', 'z']}]},
         {'superList': [{'waitFor': ['x', 'y', 'z']}]}),
        # If the key is 'secret_env' the value is not transformed, while other
        # keys, and the key itself, are transformed.
        ({'camel_me': '', 'secret_env': {'FOO_BAR': 'asdf'}},
         {'camelMe': '', 'secretEnv': {'FOO_BAR': 'asdf'}}),
        # If the key is 'secretEnv' the value is not transformed.
        ({'secretEnv': {'FOO_BAR': 'asdf'}},
         {'secretEnv': {'FOO_BAR': 'asdf'}}),
        # Ensure the skip param works inside lists.
        ([{'secretEnv': {'FOO_BAR': 'asdf'}}],
         [{'secretEnv': {'FOO_BAR': 'asdf'}}]),
        # Ensure the skip param works inside dict values.
        ({'dummy': {'secretEnv': {'FOO_BAR': 'asdf'}}},
         {'dummy': {'secretEnv': {'FOO_BAR': 'asdf'}}}),
    ]
    for input_string, expected in cases:
      self.assertEqual(
          cloudbuild_util.SnakeToCamel(
              input_string, skip=['secretEnv', 'secret_env']), expected)

  def testMessageToFieldPaths_EmptyMessage(self):
    messages = cloudbuild_util.GetMessagesModuleAlpha()

    self.assertEqual(
        len(cloudbuild_util.MessageToFieldPaths(messages.WorkerPool())),
        0)

  def testMessageToFieldPaths_WorkerPool(self):
    messages = cloudbuild_util.GetMessagesModuleAlpha()

    wp = messages.WorkerPool()
    wp.name = 'name'
    wp.networkConfig = messages.NetworkConfig()
    wp.networkConfig.peeredNetwork = 'network'
    wp.region = 'region'
    worker_config = messages.WorkerConfig()
    worker_config.machineType = 'machine_type'
    worker_config.diskSizeGb = 100
    wp.workerConfig = worker_config

    self.assertEqual(
        set(cloudbuild_util.MessageToFieldPaths(wp)),
        set([
            'name', 'network_config.peered_network', 'region',
            'worker_config.machine_type', 'worker_config.disk_size_gb'
        ]))


if __name__ == '__main__':
  test_case.main()
