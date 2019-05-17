# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Test of the 'memberships update' command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.memberships import base


class UpdateTestAlpha(base.MembershipsTestBase):
  """gcloud Alpha track using GKE Hub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectUpdateCalls(self, update, mask, asynchronous=False):
    operation = self._MakeOperation()
    self.ExpectUpdateMembership(update, mask, operation)
    if asynchronous:
      return
    self.ExpectGetOperation(operation)
    operation = self._MakeOperation(done=True)
    self.ExpectGetOperation(operation)
    result = copy.deepcopy(update)
    result.name = self.MEMBERSHIP_NAME
    self.ExpectGetMembership(result)

  def testUpdateDescription(self):
    description = 'my-new-membership'
    updated_membership = self._MakeMembership(description=description)
    self._ExpectUpdateCalls(updated_membership, 'description')

    self.WriteInput('y')
    self._RunMembershipCommand(
        ['update', self.MEMBERSHIP_NAME, '--description', description])


if __name__ == '__main__':
  test_case.main()
