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
"""Tests for the commitments list command."""
import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from tests.lib.surface.compute import test_base
import mock


class CommitmentsListTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.SelectApi('v1')
    lister_patcher = mock.patch.object(lister, 'GetRegionalResourcesDicts',
                                       autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = [
        encoding.MessageToDict(self.messages.Commitment(
            name='pledge',
            plan=self.messages.Commitment.PlanValueValuesEnum.TWELVE_MONTH,
            region='{}/projects/my-project/regions/us-central1-a'.format(
                self.compute_uri),
            endTimestamp='2012-12-31T12:00:00.0Z',
            status=self.messages.Commitment.StatusValueValuesEnum.EXPIRED,
            resources=[
                self.messages.ResourceCommitment(
                    amount=500,
                    type=(self.messages.ResourceCommitment.
                          TypeValueValuesEnum.VCPU),
                ),
                self.messages.ResourceCommitment(
                    amount=12,
                    type=(self.messages.ResourceCommitment.
                          TypeValueValuesEnum.MEMORY),
                ),
            ],
        ))]

  def testTableOutput(self):
    self.Run('compute commitments list')
    # TODO(b/36019833): change expectation to
    # self.mock_get_regional_resources.assert_called_once_with
    # (there is a problem with matching  service).
    self.mock_get_regional_resources.assert_called()
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   REGION        END_TIMESTAMP          STATUS
            pledge us-central1-a 2012-12-31T12:00:00.0Z EXPIRED
            """), normalize_space=True)
