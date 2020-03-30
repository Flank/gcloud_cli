# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the 'memberships delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.hub.memberships import base


class DeleteTest(base.MembershipsTestBase):
  """gcloud GA track using GKE Hub API."""

  # TODO(b/116715821): add more negative tests.
  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectDeleteCalls(self, membership, asynchronous=False):
    # First time still pending.
    operation = self._MakeOperation()
    self.ExpectDeleteMembership(membership, operation)
    if asynchronous:
      return
    self.ExpectGetOperation(operation)
    # Second time succeed.
    operation = self._MakeOperation(done=True)
    self.ExpectGetOperation(operation)

  def testDeleteDefaults(self):
    membership = self._MakeMembership()
    self._ExpectDeleteCalls(membership)

    self.WriteInput('y')
    self._RunMembershipCommand(['delete', self.MEMBERSHIP_NAME])


class DeleteTestBeta(DeleteTest):
  """gcloud Beta track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DeleteTestAlpha(DeleteTestBeta):
  """gcloud Alpha track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
