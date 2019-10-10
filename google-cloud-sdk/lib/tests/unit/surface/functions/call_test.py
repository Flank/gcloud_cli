# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests of the 'call' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.functions import base


class FunctionsCallTest(base.FunctionsTestBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def testCall(self):
    call_response = self.messages.CallFunctionResponse(
        executionId='e-id-1',
        result='some--result')
    test_name = 'projects/{0}/locations/us-central1/functions/my-test'.format(
        self.Project())
    self.mock_client.projects_locations_functions.Call.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCallRequest(
            name=test_name,
            callFunctionRequest=self.messages.CallFunctionRequest(
                data='"some--data"')),
        call_response)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions call my-test --data=\'"some--data"\'')
    self.assertEqual(result, call_response)

  def testGetNoAuth(self):
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_AUTH_REGEXP):
      self.Run('functions call my-test')

  def testDatavalidation(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--data\]. Is not a valid JSON.'):
      self.Run('functions call my-test --data="not-json"')


class FunctionsGetWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testGetNoProject(self):
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_PROJECT_RESOURCE_ARG_REGEXP):
      self.Run('functions call my-test')

if __name__ == '__main__':
  test_case.main()
