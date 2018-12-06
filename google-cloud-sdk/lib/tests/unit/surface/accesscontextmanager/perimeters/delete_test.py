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
"""Tests for `gcloud access-context-manager perimeters delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class PerimetersDeleteTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectDelete(self, perimeter, policy):
    perimeter_name = 'accessPolicies/{}/servicePerimeters/{}'.format(
        policy, perimeter)
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersDeleteRequest)
    self.client.accessPolicies_servicePerimeters.Delete.Expect(
        request_type(name=perimeter_name),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')

  def testDelete_MissingRequired(self):
    self.SetUpForTrack(self.track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager perimeters delete --policy my_policy')

  def testDelete_Prompt(self):
    self.SetUpForTrack(self.track)
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run(
          'access-context-manager perimeters delete my_perimeter '
          '--policy my_policy'
      )

  def testDelete(self):
    self.SetUpForTrack(self.track)
    self._ExpectDelete('my_perimeter', 'my_policy')

    self.Run(
        'access-context-manager perimeters delete my_perimeter --policy '
        'my_policy --quiet')

    self.AssertOutputEquals('')

  def testDelete_PolicyFromProperty(self):
    self.SetUpForTrack(self.track)
    policy = 'my_acm_policy'
    properties.VALUES.access_context_manager.policy.Set(policy)
    self._ExpectDelete('my_perimeter', policy)

    self.Run('access-context-manager perimeters delete my_perimeter --quiet')

    self.AssertOutputEquals('')


class PerimetersDeleteTestAlpha(PerimetersDeleteTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
