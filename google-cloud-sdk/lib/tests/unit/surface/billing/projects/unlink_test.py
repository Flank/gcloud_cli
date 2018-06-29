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
"""Tests for surface.billing.projects.link ."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.billing import base

messages = core_apis.GetMessagesModule('cloudbilling', 'v1')


class AccountsProjectsUnLinkTest(base.BillingMockNoDisplayTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testUnlink(self):
    no_billing = messages.ProjectBillingInfo(
        billingAccountName=''
    )

    self.mocked_billing.projects.UpdateBillingInfo.Expect(
        messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name='projects/{project_id}'.format(
                project_id=base.PROJECTS[0].projectId,
            ),
            projectBillingInfo=no_billing,
        ),
        no_billing,
    )

    self.assertEqual(
        self.Run('billing projects unlink {project_id}'.format(
            project_id=base.PROJECTS[0].projectId,
        )),
        no_billing,
    )


if __name__ == '__main__':
  test_case.main()
