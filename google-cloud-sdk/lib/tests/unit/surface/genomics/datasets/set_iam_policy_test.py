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

from apitools.base.py import encoding

from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base
from tests.lib.surface.genomics import test_data


class SetIamPolicyTest(base.GenomicsUnitTest):

  def testSetIamPolicy(self):
    json = encoding.MessageToJson(test_data.TEST_IAM_POLICY)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    self.mocked_client.datasets.SetIamPolicy.Expect(
        self.messages.GenomicsDatasetsSetIamPolicyRequest(
            resource='datasets/1000',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=test_data.TEST_IAM_POLICY)),
        test_data.TEST_IAM_POLICY)
    response = self.RunGenomics(
        ['datasets', 'set-iam-policy', '1000', temp_file])
    self.assertEqual(response, test_data.TEST_IAM_POLICY)
    self.AssertErrContains('Updated IAM policy for dataset [1000].')

  def testSetIamPolicyByResourceUri(self):
    json = encoding.MessageToJson(test_data.TEST_IAM_POLICY)
    temp_file = self.Touch(self.temp_path, 'good.json', contents=json)

    self.mocked_client.datasets.SetIamPolicy.Expect(
        self.messages.GenomicsDatasetsSetIamPolicyRequest(
            resource='datasets/1000',
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=test_data.TEST_IAM_POLICY)),
        test_data.TEST_IAM_POLICY)
    response = self.RunGenomics(
        ['datasets', 'set-iam-policy',
         'https://genomics.googleapis.com/v1/datasets/1000', temp_file])
    self.assertEqual(response, test_data.TEST_IAM_POLICY)

  def testBadJsonOrYamlSetIamPolicyProject(self):
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.assertRaises(exceptions.Error):
      self.RunGenomics(['datasets', 'set-iam-policy', '1000', temp_file])

  def testBadJsonSetIamPolicyProject(self):
    file_path = '/some/bad/path/to/non/existent/file'
    self.assertRaisesRegex(
        exceptions.Error,
        r'Failed to load YAML from \[{0}\]'.format(file_path),
        self.RunGenomics, ['datasets', 'set-iam-policy', '1000', file_path])


if __name__ == '__main__':
  test_case.main()
