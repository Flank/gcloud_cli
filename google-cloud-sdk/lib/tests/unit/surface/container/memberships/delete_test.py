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
"""Tests for 'membership delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.memberships import base


class DeleteTestAlpha(base.MembershipsTestBase):
  """gcloud Alpha track using gkehub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

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


if __name__ == '__main__':
  test_case.main()
