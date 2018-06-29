# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for genomics datasets get-iam-policy command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.genomics import base
from tests.lib.surface.genomics import test_data


@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
class GetIamPolicyTest(base.GenomicsUnitTest, test_case.WithOutputCapture):

  def testGetIamPolicy(self, track):
    self.track = track
    self.mocked_client.datasets.GetIamPolicy.Expect(
        request=self.messages.GenomicsDatasetsGetIamPolicyRequest(
            resource='datasets/1000'),
        response=test_data.TEST_IAM_POLICY,)

    self.assertEqual(test_data.TEST_IAM_POLICY,
                     self.RunGenomics(['datasets', 'get-iam-policy', '1000']))

  def testGetIamPolicyByResourceUri(self, track):
    self.track = track
    self.mocked_client.datasets.GetIamPolicy.Expect(
        request=self.messages.GenomicsDatasetsGetIamPolicyRequest(
            resource='datasets/1000'),
        response=test_data.TEST_IAM_POLICY,)

    response = self.RunGenomics(
        ['datasets', 'get-iam-policy',
         'https://genomics.googleapis.com/v1/datasets/1000'])

    self.assertEqual(test_data.TEST_IAM_POLICY, response)

  def testListCommandFilter(self, track):
    self.track = track
    self.mocked_client.datasets.GetIamPolicy.Expect(
        request=self.messages.GenomicsDatasetsGetIamPolicyRequest(
            resource='datasets/1000'),
        response=test_data.TEST_IAM_POLICY,)

    self.RunGenomics([
        'datasets',
        'get-iam-policy',
        'https://genomics.googleapis.com/v1/datasets/1000',
        '--flatten=bindings[].members',
        '--filter=bindings.role:roles/owner',
        '--format=value(bindings.members)',
    ])
    self.AssertOutputContains('user:test_owner@test.com')


if __name__ == '__main__':
  test_case.main()
