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

"""Tests for genomics datasets set-iam-policy command."""

from __future__ import absolute_import
from __future__ import unicode_literals
import pickle

from tests.lib import test_case
from tests.lib.surface.genomics import base
from tests.lib.surface.genomics import test_data


class AddIamPolicyBindingTest(base.GenomicsUnitTest):

  def testAddIamPolicyBinding(self):
    new_policy = pickle.loads(pickle.dumps(test_data.TEST_IAM_POLICY))
    new_policy.bindings[1].members.append('user:editor@test.com')

    self.mocked_client.datasets.GetIamPolicy.Expect(
        self.messages.GenomicsDatasetsGetIamPolicyRequest(
            resource='datasets/1000',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        pickle.loads(pickle.dumps(test_data.TEST_IAM_POLICY)))
    self.mocked_client.datasets.SetIamPolicy.Expect(
        self.messages.GenomicsDatasetsSetIamPolicyRequest(
            resource='datasets/1000',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(policy=
                                                                  new_policy)),
        new_policy)

    response = self.RunGenomics(
        ['datasets', 'add-iam-policy-binding', '1000',
         '--role', 'roles/editor',
         '--member', 'user:editor@test.com'])
    self.assertEqual(response, new_policy)

  def testAddIamPolicyBindingByResourceUri(self):
    new_policy = pickle.loads(pickle.dumps(test_data.TEST_IAM_POLICY))
    new_policy.bindings[1].members.append('user:editor@test.com')

    self.mocked_client.datasets.GetIamPolicy.Expect(
        self.messages.GenomicsDatasetsGetIamPolicyRequest(
            resource='datasets/1000',
            getIamPolicyRequest=self.messages.GetIamPolicyRequest()),
        pickle.loads(pickle.dumps(test_data.TEST_IAM_POLICY)))
    self.mocked_client.datasets.SetIamPolicy.Expect(
        self.messages.GenomicsDatasetsSetIamPolicyRequest(
            resource='datasets/1000',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(policy=
                                                                  new_policy)),
        new_policy)

    response = self.RunGenomics(
        ['datasets', 'add-iam-policy-binding',
         'https://genomics.googleapis.com/v1/datasets/1000',
         '--role', 'roles/editor',
         '--member', 'user:editor@test.com'])
    self.assertEqual(response, new_policy)


if __name__ == '__main__':
  test_case.main()
