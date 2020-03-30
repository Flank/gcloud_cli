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
"""E2E tests for Access Approval."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.access_approval import base


class AccessApprovalE2ETest(base.AccessApprovalE2ETestBase):
  """E2E tests for access approval."""

  def testGetSettings_axtNotEnabled(self):

    # The default project used for gcloud e2e tests doesn't have access
    # transparency enabled and the Get Settings api is supposed to throw an
    # error in that case. This could actually be a common scenario for a
    # first-time user of the API so we have test to check that.
    with self.AssertRaisesHttpExceptionRegexp('.*FAILED_PRECONDITION.*'):
      self.Run('access-approval settings get')

  def testEnable(self):
    self.Run('access-approval settings update --project=aa-gcloud-e2e-test '
             '--enrolled_services=all')
    self.AssertOutputContains('enrolledServices')

  def testList(self):
    self.Run('access-approval requests list --project=aa-gcloud-e2e-test')
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_case.main()
