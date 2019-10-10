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
from tests.lib import test_case


class EnvVarsTest(test_case.TestCase):
  """Test environment variable api utility functions.
  """

  def testGetFunctionEnvVarsAsDictNone(self):
    messages = api_util.GetApiMessagesModule()
    function = messages.CloudFunction()
    actual = env_vars.GetFunctionEnvVarsAsDict(function)
    self.assertEqual({}, actual)

  def testGetFunctionEnvVarsAsDict(self):
    expected = {
        'FOO': 'BAR',
        'BAZ': 'BOO',
    }

    messages = api_util.GetApiMessagesModule()
    env_vars_class = messages.CloudFunction.EnvironmentVariablesValue
    function = messages.CloudFunction()
    function.environmentVariables = (
        env_vars_class(additionalProperties=[
            env_vars_class.AdditionalProperty(key='BAZ', value='BOO'),
            env_vars_class.AdditionalProperty(key='FOO', value='BAR'),
        ])
    )

    actual = env_vars.GetFunctionEnvVarsAsDict(function)
    self.assertEqual(expected, actual)

  def testDictToEnvVarsPropertyNone(self):
    actual = env_vars.DictToEnvVarsProperty(None)
    self.assertEqual(None, actual)

  def testDictToEnvVarsProperty(self):
    messages = api_util.GetApiMessagesModule()
    env_vars_class = messages.CloudFunction.EnvironmentVariablesValue
    expected = (
        env_vars_class(additionalProperties=[
            env_vars_class.AdditionalProperty(key='BAZ', value='BOO'),
            env_vars_class.AdditionalProperty(key='FOO', value='BAR'),
        ])
    )

    env_vars_dict = {
        'FOO': 'BAR',
        'BAZ': 'BOO',
    }
    actual = env_vars.DictToEnvVarsProperty(env_vars_dict)
    self.assertEqual(expected, actual)

if __name__ == '__main__':
  test_case.main()
