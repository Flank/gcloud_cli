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

"""Tests for gcloud app describe."""


from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions as app_exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import api_test_util


class DescribeAppTest(api_test_util.ApiTestBase):

  def testDescribe_NoProject(self):
    """Test `gcloud app describe` raises informative error if no project found.
    """
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app describe')

  def testDescribe(self):
    """Test `gcloud app describe` basic output."""
    properties.VALUES.core.project.Set(self.Project())
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app describe')
    self.AssertOutputEquals('codeBucket: {0}-staging.appspot.com\n'
                            'defaultHostname: {0}.appspot.com\n'
                            'gcrDomain: us.gcr.io\n'
                            'id: {0}\n'
                            'name: apps/{0}\n'
                            'servingStatus: SERVING\n'.format(self.Project()),
                            normalize_space=True)

  def testDescribe_NoApp(self):
    """Test `gcloud app describe` raises informative error if no app found."""
    properties.VALUES.core.project.Set(self.Project())
    self.ExpectGetApplicationRequest(
        self.Project(),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            details=http_error.ExampleErrorDetails()))
    missing_app_regex = (r'The current Google Cloud project \[{}\] '
                         'does not contain an App Engine application. Use '
                         '`gcloud app create` to initialize an App Engine '
                         'application within the project.'
                         .format(self.Project()))
    with self.assertRaisesRegex(app_exceptions.MissingApplicationError,
                                missing_app_regex):
      self.Run('app describe')


class BetaDescribeAppTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('appengine',
                                                'v1beta')
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('appengine', 'v1beta'),
        real_client=core_apis.GetClientInstance(
            'appengine', 'v1beta', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def testDescribeBeta(self):
    """Test `gcloud beta app describe` basic output."""
    properties.VALUES.core.project.Set(self.Project())
    self.ExpectGetApplicationRequest(self.Project(),
                                     split_health_checks=True,
                                     track=self.track)
    self.Run('app describe', base.ReleaseTrack.BETA)
    self.AssertOutputEquals('codeBucket: {0}-staging.appspot.com\n'
                            'defaultHostname: {0}.appspot.com\n'
                            'featureSettings:\n'
                            '    splitHealthChecks: true\n'
                            'gcrDomain: us.gcr.io\n'
                            'id: {0}\n'
                            'name: apps/{0}\n'
                            'servingStatus: SERVING\n'.format(self.Project()),
                            normalize_space=True)

if __name__ == '__main__':
  test_case.main()
