# -*- coding: utf-8 -*- #
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
"""Tests the 'source repo get-iam-policy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.source import base
import mock

# TODO(b/63649781): test on a mocked IAM policy object, not a fake JSON string


class GetIamPolicyTest(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def testGetIamPolicyTest(self):
    with mock.patch.object(
        sourcerepo.Source, 'GetIamPolicy', autospec=True) as source_mock:
      source_mock.return_value = '{"etag": "BwVCYLHABdU="}'
      self.RunSourceRepos(['get-iam-policy', 'some_name'])
      res = resources.REGISTRY.Parse(
          'some_name',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      self.assertEqual(source_mock.call_count, 1)
      called_res = source_mock.call_args[0][1]
      self.assertEqual(res.RelativeName(), called_res.RelativeName())
      self.AssertOutputContains('\'{"etag": "BwVCYLHABdU="}\'\n')

  def testListCommandFilter(self):
    with mock.patch.object(
        sourcerepo.Source, 'GetIamPolicy', autospec=True) as source_mock:
      source_mock.return_value = {
          'bindings': [
              {
                  'members': ['user:user1@foo.com', 'user:user2@bar.com'],
                  'role': 'roles/owner',
              },
              {
                  'members': ['serviceAccount:admin@foobar.com'],
                  'role': 'roles/storage.objectAdmin',
              },
          ],
          'etag':
              'BwVUBekJB3w=',
          'version':
              1,
      }
      self.RunSourceRepos([
          'get-iam-policy',
          'some_name',
          '--flatten=bindings[].members',
          '--filter=bindings.role:roles/owner',
          '--format=table[no-heading](bindings.members:sort=1)',
      ])
      self.AssertOutputEquals('user:user1@foo.com\nuser:user2@bar.com\n')

  def testGetIamPolicyURITest(self):
    with mock.patch.object(
        sourcerepo.Source, 'GetIamPolicy', autospec=True) as source_mock:
      source_mock.return_value = '{"etag": "BwVCYLHABdU="}'
      uri = ('https://sourcerepo.googleapis.com/v1/projects/'
             'differentproject/repos/some_name')
      self.RunSourceRepos(['get-iam-policy', uri])
      res = resources.REGISTRY.Parse(
          'some_name',
          params={'projectsId': 'differentproject'},
          collection='sourcerepo.projects.repos')
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertOutputContains('\'{"etag": "BwVCYLHABdU="}\'\n')

  def testGetIamPolicyFailure(self):
    with mock.patch.object(
        sourcerepo.Source, 'GetIamPolicy', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(code=400)
      with self.assertRaises(c_exc.HttpException):
        self.RunSourceRepos(['get-iam-policy', 'some_name'])


if __name__ == '__main__':
  test_case.main()
