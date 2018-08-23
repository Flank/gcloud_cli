# -*- coding: utf-8 -*- #
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
"""Test of the 'source delete' command."""

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


class DeleteTest(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def testDeleteSuccessQuiet(self):
    res = resources.REGISTRY.Parse(
        'some_name',
        params={'projectsId': self.Project},
        collection='sourcerepo.projects.repos')
    with mock.patch.object(
        sourcerepo.Source, 'DeleteRepo', autospec=True) as source_mock:
      self.RunSourceRepos(['delete', 'some_name', '--quiet'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrEquals('Deleted [some_name].\n')
      self.AssertOutputEquals('')

  def testDeleteSuccessPromptYes(self):
    res = resources.REGISTRY.Parse(
        'some_name',
        params={'projectsId': self.Project},
        collection='sourcerepo.projects.repos')
    with mock.patch.object(
        sourcerepo.Source, 'DeleteRepo', autospec=True) as source_mock:
      self.WriteInput(('y'))
      self.RunSourceRepos(['delete', 'some_name'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Deleted [some_name].')

  def testDeleteSuccessPromptNo(self):
    with mock.patch.object(
        sourcerepo.Source, 'DeleteRepo', autospec=True) as source_mock:
      self.WriteInput(('n'))
      self.RunSourceRepos(['delete', 'some_name'])
      self.assertEqual(0, source_mock.call_count)

  def testDeleteFailure(self):
    with mock.patch.object(
        sourcerepo.Source, 'DeleteRepo', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(code=400)
      with self.assertRaises(c_exc.HttpException):
        self.RunSourceRepos(['delete', 'some_name', '--quiet'])


if __name__ == '__main__':
  test_case.main()
