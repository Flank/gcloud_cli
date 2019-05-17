# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.

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
"""Tests for the ML Engine jobs command_lib utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.command_lib.ml_engine import versions_util
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class ParseVersionTestGA(base.MlGaPlatformTestBase):

  _VERSION_URL = ('https://ml.googleapis.com/v1/projects/other-project/'
                  'models/other-model/versions/other-version')

  def testParseVersion(self):
    version_ref = versions_util.ParseVersion('model', 'version')
    self.assertEqual(version_ref.projectsId, self.Project())
    self.assertEqual(version_ref.modelsId, 'model')
    self.assertEqual(version_ref.versionsId, 'version')
    self.assertEqual(version_ref.Name(), 'version')
    self.assertEqual(
        version_ref.RelativeName(),
        'projects/{}/models/model/versions/version'.format(self.Project()))

  def testParseVersion_Url(self):
    version_ref = versions_util.ParseVersion('model', self._VERSION_URL)
    self.assertEqual(version_ref.projectsId, 'other-project')
    self.assertEqual(version_ref.modelsId, 'other-model')
    self.assertEqual(version_ref.versionsId, 'other-version')
    self.assertEqual(version_ref.Name(), 'other-version')
    self.assertEqual(
        version_ref.RelativeName(),
        'projects/other-project/models/other-model/versions/other-version')
    self.assertEqual(version_ref.SelfLink(), self._VERSION_URL)


class ParseVersionTestBeta(base.MlBetaPlatformTestBase, ParseVersionTestGA):
  pass


class WaitForOpMaybeTestBase(object):

  def _MakeOp(self, done=True, response=None):
    return self.msgs.GoogleLongrunningOperation(
        name='projects/{}/operations/operation'.format(self.Project()),
        done=done,
        response=response)

  def SetUp(self):
    self.operations_client = operations.OperationsClient(self.API_VERSION)
    self.operation_get_request = self.msgs.MlProjectsOperationsGetRequest(
        name='projects/{}/operations/operation'.format(self.Project()))
    self.StartObjectPatch(time, 'sleep')

  def testWaitForOpMaybe_Async(self):
    op = self._MakeOp(done=False)

    result = versions_util.WaitForOpMaybe(self.operations_client, op,
                                          asyncronous=True)

    self.assertIs(result, op)
    self.AssertErrEquals('')

  def testWaitForOpMaybe_SyncDone(self):
    response = self.msgs.GoogleLongrunningOperation.ResponseValue()
    op = self._MakeOp(done=True, response=response)

    result = versions_util.WaitForOpMaybe(self.operations_client, op)

    self.assertIs(result, response)
    self.AssertErrNotContains('Waiting for operation [operation]...')

  def testWaitForOpMaybe_SyncRepeated(self):
    response = self.msgs.GoogleLongrunningOperation.ResponseValue()
    ops = [
        self._MakeOp(done=False, response=None),
        self._MakeOp(done=False, response=None),
        self._MakeOp(done=True, response=response)
    ]
    self.client.projects_operations.Get.Expect(
        self.operation_get_request, ops[1])
    self.client.projects_operations.Get.Expect(
        self.operation_get_request, ops[2])

    result = versions_util.WaitForOpMaybe(self.operations_client, ops[0])

    self.assertIs(result, response)
    self.AssertErrContains('Waiting for operation [operation]')


class WaitForOpMaybeGaTest(WaitForOpMaybeTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(WaitForOpMaybeGaTest, self).SetUp()


class WaitForOpMaybeBetaTest(WaitForOpMaybeTestBase,
                             base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(WaitForOpMaybeBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
