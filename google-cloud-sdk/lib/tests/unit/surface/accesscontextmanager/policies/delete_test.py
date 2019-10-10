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
"""Tests for `gcloud access-context-manager policies delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class PoliciesDeleteTestGA(accesscontextmanager.Base):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def testDelete(self):
    self.SetUpForTrack(self.track)

    request_type = self.messages.AccesscontextmanagerAccessPoliciesDeleteRequest
    self.client.accessPolicies.Delete.Expect(
        request_type(name='accessPolicies/MY_POLICY'),
        self.messages.Operation(name='operations/my-op', done=False))

    self.Run('access-context-manager policies delete --quiet MY_POLICY')


class PoliciesDeleteTestBeta(PoliciesDeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class PoliciesDeleteTestAlpha(PoliciesDeleteTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
