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
"""Tests the 'source repos set-iam-policy' command."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.source.repos import sourcerepo
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.source import base
import mock


class SetIamPolicyTest(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def testSetIamPolicyTest(self):
    policy_file = self.Touch(
        directory=self.temp_path, contents='{"etag": "BwVCYLHABdU="}')
    with mock.patch.object(
        sourcerepo.Source, 'SetIamPolicy', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'some_name',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      source_mock.return_value = '{"etag": "BwVCYLHABdU="}'
      self.RunSourceRepos(['set-iam-policy', 'some_name', policy_file])
      source_mock.assert_called_once_with(mock.ANY, res, mock.ANY)
      self.AssertOutputContains('\'{"etag": "BwVCYLHABdU="}\'\n')
      self.AssertErrContains('Updated IAM policy for repo [some_name].')

  def testSetIamPolicyURITest(self):
    policy_file = self.Touch(
        directory=self.temp_path, contents='{"etag": "BwVCYLHABdU="}')
    with mock.patch.object(
        sourcerepo.Source, 'SetIamPolicy', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'some_name',
          params={'projectsId': 'not{0}'.format(self.Project)},
          collection='sourcerepo.projects.repos')
      source_mock.return_value = '{"etag": "BwVCYLHABdU="}'
      uri = ('https://sourcerepo.googleapis.com/v1/projects/'
             'not{0}/repos/some_name').format(self.Project)
      self.RunSourceRepos(['set-iam-policy', uri, policy_file])
      source_mock.assert_called_once_with(mock.ANY, res, mock.ANY)
      self.AssertOutputContains('\'{"etag": "BwVCYLHABdU="}\'\n')

  def testSetIamPolicyFailureTest(self):
    policy_file = self.Touch(
        directory=self.temp_path, contents='{"etag": "BwVCYLHABdU="}')
    with mock.patch.object(
        sourcerepo.Source, 'SetIamPolicy', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(code=400)
      with self.assertRaises(c_exc.HttpException):
        self.RunSourceRepos(['set-iam-policy', 'some_name', policy_file])


if __name__ == '__main__':
  test_case.main()
