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

"""Unit tests for api_lib/functions/env_vars.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions import env_vars
from googlecloudsdk.api_lib.functions import util as api_util
from tests.lib import parameterized
from tests.lib import test_case


class EnvVarsTest(parameterized.TestCase):
  """Test environment variable api utility functions.
  """

  _BUILD_ENV_VARS_TYPE_CLASS = api_util.GetApiMessagesModule(
  ).CloudFunction.BuildEnvironmentVariablesValue
  _ENV_VARS_TYPE_CLASS = api_util.GetApiMessagesModule(
  ).CloudFunction.EnvironmentVariablesValue

  def testGetEnvVarsAsDict_BuildEnvVar_None(self):
    messages = api_util.GetApiMessagesModule()
    function = messages.CloudFunction()
    actual = env_vars.GetEnvVarsAsDict(function.buildEnvironmentVariables)
    self.assertEqual({}, actual)

  def testGetEnvVarsAsDict_EnvVar_None(self):
    messages = api_util.GetApiMessagesModule()
    function = messages.CloudFunction()
    actual = env_vars.GetEnvVarsAsDict(function.environmentVariables)
    self.assertEqual({}, actual)

  def testGetEnvVarsAsDict_BuildEnvVar(self):
    expected = {
        'FOO': 'BAR',
        'BAZ': 'BOO',
    }

    messages = api_util.GetApiMessagesModule()
    env_vars_class = self._BUILD_ENV_VARS_TYPE_CLASS
    function = messages.CloudFunction()
    function.buildEnvironmentVariables = (
        env_vars_class(additionalProperties=[
            env_vars_class.AdditionalProperty(key='BAZ', value='BOO'),
            env_vars_class.AdditionalProperty(key='FOO', value='BAR'),
        ]))

    actual = env_vars.GetEnvVarsAsDict(function.buildEnvironmentVariables)
    self.assertEqual(expected, actual)

  def testGetEnvVarsAsDict_EnvVar(self):
    expected = {
        'FOO': 'BAR',
        'BAZ': 'BOO',
    }

    messages = api_util.GetApiMessagesModule()
    env_vars_class = self._ENV_VARS_TYPE_CLASS
    function = messages.CloudFunction()
    function.environmentVariables = (
        env_vars_class(additionalProperties=[
            env_vars_class.AdditionalProperty(key='BAZ', value='BOO'),
            env_vars_class.AdditionalProperty(key='FOO', value='BAR'),
        ])
    )

    actual = env_vars.GetEnvVarsAsDict(function.environmentVariables)
    self.assertEqual(expected, actual)

  @parameterized.parameters((_BUILD_ENV_VARS_TYPE_CLASS),
                            (_ENV_VARS_TYPE_CLASS))
  def testDictToEnvVarsPropertyNone(self, env_vars_type_class):
    actual = env_vars.DictToEnvVarsProperty(env_vars_type_class, None)
    self.assertIsNone(actual)

  @parameterized.parameters((_BUILD_ENV_VARS_TYPE_CLASS),
                            (_ENV_VARS_TYPE_CLASS))
  def testDictToEnvVarsProperty(self, env_vars_type_class):
    expected = (
        env_vars_type_class(additionalProperties=[
            env_vars_type_class.AdditionalProperty(key='BAZ', value='BOO'),
            env_vars_type_class.AdditionalProperty(key='FOO', value='BAR'),
        ]))

    env_vars_dict = {
        'FOO': 'BAR',
        'BAZ': 'BOO',
    }
    actual = env_vars.DictToEnvVarsProperty(env_vars_type_class, env_vars_dict)
    self.assertEqual(expected, actual)

if __name__ == '__main__':
  test_case.main()
