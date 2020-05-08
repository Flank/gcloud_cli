# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager perimeters dry-run enforce-all`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class DryRunEnforceAllTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectCommit(self, policy, etag):
    policy_name = 'accessPolicies/{}'.format(policy)
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersCommitRequest)
    commit_req = self.messages.CommitServicePerimetersRequest(etag=etag)
    self.client.accessPolicies_servicePerimeters.Commit.Expect(
        request_type(
            parent=policy_name, commitServicePerimetersRequest=commit_req),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')

  def testEnforceAll_noEtag(self):
    self.SetUpForAPI(self.api_version)
    self._ExpectCommit('123', None)

    self.Run('access-context-manager perimeters dry-run enforce-all'
             '   --policy 123')

  def testEnforceAll_withEtag(self):
    self.SetUpForAPI(self.api_version)
    self._ExpectCommit('123', '32322646464')

    self.Run('access-context-manager perimeters dry-run enforce-all'
             '   --policy 123 --etag 32322646464')


class DryRunEnforceAllTestAlpha(DryRunEnforceAllTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
