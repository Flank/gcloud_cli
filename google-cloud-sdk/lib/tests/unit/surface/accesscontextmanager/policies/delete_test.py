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
"""Tests for `gcloud access-context-manager policies delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class PoliciesDeleteTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _MakePolicy(self, policy_id, parent=None):
    return self.messages.AccessPolicy(
        name='accessPolicies/{}'.format(policy_id),
        parent=parent,
        title='My Policy')

  def _ExpectDelete(self, policy):
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesDeleteRequest
    self.client.accessPolicies.Delete.Expect(request_type(name=policy.name),
                                             policy)

  def testDelete(self, track):
    self.SetUpForTrack(track)

    organization_id = '12345'
    policy = self._MakePolicy('MY_POLICY',
                              parent='organizations/' + organization_id)
    self._ExpectDelete(policy)

    self.Run('access-context-manager policies delete --quiet MY_POLICY')


if __name__ == '__main__':
  test_case.main()
