# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Test of the 'source create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.source import base
import mock

NAME_64 = 'abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789'
LONG_NAME = NAME_64 + '_' + NAME_64


class CreateTest(base.SourceSdkTest, sdk_test_base.WithOutputCapture):

  def testCreateSuccess(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'somename',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      self.RunSourceRepos(['create', 'somename'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [somename].')
      self.AssertErrContains('You may be billed for this repository')

  def testCreateSuccessFormatJson(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'somename',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      messages = apis.GetMessagesModule('sourcerepo', 'v1')
      repo = messages.Repo(name=res.RelativeName(), size=1, url='https://')
      source_mock.return_value = repo
      self.RunSourceRepos(['create', 'somename', '--format=json'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [somename].')
      self.AssertOutputMatches(
          '{{\n"name": "{0}",\n"size": "1",\n"url": "https://"\n}}'.format(
              res.RelativeName()),
          normalize_space=True)

  def testCreateSuccessHyphen(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'some-name',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      self.RunSourceRepos(['create', 'some-name'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [some-name].')

  def testCreateSuccessUnderscore(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          'some_name',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')
      self.RunSourceRepos(['create', 'some_name'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [some_name].')

  def testCreateSuccessSlash(self):
    res = resources.REGISTRY.Parse(
        'some/name',
        params={'projectsId': self.Project},
        collection='sourcerepo.projects.repos')
    res = resources.REGISTRY.Parse(
        'some/name',
        params={'projectsId': self.Project},
        collection='sourcerepo.projects.repos')
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      self.RunSourceRepos(['create', 'some/name'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [some/name].\n')
      self.AssertErrContains(
          'You may be billed for this repository. See'
          ' https://cloud.google.com/source-repositories/docs/pricing'
          ' for details.\n')

  def testCreateSuccessURI(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      uri = ('https://sourcerepo.googleapis.com/v1/projects/'
             'differentproject/repos/somename')
      res = resources.REGISTRY.Parse(
          uri,
          params={'projectsId': 'differentproject'},
          collection='sourcerepo.projects.repos')

      self.RunSourceRepos(['create', uri])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [somename].')

  def testCreateSuccessURIWithSlash(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      uri = ('https://sourcerepo.googleapis.com/v1/projects/'
             'differentproject/repos/some/name')
      res = resources.REGISTRY.Parse(
          uri,
          params={'projectsId': 'differentproject'},
          collection='sourcerepo.projects.repos')

      self.RunSourceRepos(['create', uri])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [some/name].')

  def testCreateFailurePermissionDenied(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(code=403)

      with self.AssertRaisesHttpExceptionRegexp(r'Permission denied'):
        self.RunSourceRepos(['create', 'some-name'])

  def testCreateFailureHyphenOnly(self):
    with mock.patch.object(sourcerepo.Source, 'CreateRepo', autospec=True):
      with self.AssertRaisesExceptionRegexp(Exception, 'Bad value'):
        self.RunSourceRepos(['create', '-'])

  def testCreateSuccessUnderscoreOnly(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          '_',
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')

      self.RunSourceRepos(['create', '_'])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [_].')

  def testCreateSuccessLongName(self):
    almost_too_long = LONG_NAME[0:128]
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      res = resources.REGISTRY.Parse(
          almost_too_long,
          params={'projectsId': self.Project},
          collection='sourcerepo.projects.repos')

      self.RunSourceRepos(['create', almost_too_long])
      source_mock.assert_called_once_with(mock.ANY, res)
      self.AssertErrContains('Created [%s].' % almost_too_long)

  def testCreateFailureTooLong(self):
    with mock.patch.object(sourcerepo.Source, 'CreateRepo', autospec=True):
      with self.AssertRaisesExceptionRegexp(Exception, 'Bad value'):
        self.RunSourceRepos(['create', LONG_NAME])
        self.AssertErrNotContains('enable at')

  def testCreateFailureBilling(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(
          code=403, message='Cloud Billing Account is disabled.')
      with self.AssertRaisesHttpExceptionRegexp(
          r'Cloud Billing Account is disabled.'.format(normalize_space=True)):
        self.RunSourceRepos(['create', 'somename'])
        self.AssertErrNotContains('enable at')

  def testCreateFailureAlreadyExists(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(code=409)
      with self.AssertRaisesHttpExceptionRegexp(
          r'Resource already exists'.format(normalize_space=True)):
        self.RunSourceRepos(['create', 'somename'])
        self.AssertErrNotContains('enable at')

  def testCreateFailureApiNotEnabled(self):
    with mock.patch.object(
        sourcerepo.Source, 'CreateRepo', autospec=True) as source_mock:
      source_mock.side_effect = http_error.MakeHttpError(
          code=403, message=(
              'Cloud Source Repositories API is not enabled. '
              'Please enable the API on the Google Cloud console.'))
      with self.AssertRaisesHttpExceptionRegexp(
          r'is not enabled'.format(normalize_space=True)):
        self.RunSourceRepos(['create', 'somename'])
        self.AssertErrContains('enable at')


if __name__ == '__main__':
  test_case.main()
