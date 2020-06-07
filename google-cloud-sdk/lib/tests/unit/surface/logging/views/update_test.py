# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Tests of the 'views update' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class ViewsUpdateTest(base.LoggingTestBase):

  def testUpdateSuccess(self):
    expected_view = self.msgs.LogView(filter='my-filter')
    self.mock_client_v2.projects_locations_buckets_views.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket/'
            'views/my-view',
            updateMask='filter',
            logView=expected_view),
        expected_view)
    self.RunLogging(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateSuccessAllProperties(self):
    expected_view = self.msgs.LogView(
        filter='my-filter', description='description')
    self.mock_client_v2.projects_locations_buckets_views.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket/'
            'views/my-view',
            updateMask='filter,description', logView=expected_view),
        expected_view)
    self.RunLogging(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter=my-filter --description=description',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateSuccessAllDefaultProperties(self):
    expected_view = self.msgs.LogView(filter='', description='')
    self.mock_client_v2.projects_locations_buckets_views.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket/'
            'views/my-view',
            updateMask='filter,description', logView=expected_view),
        expected_view)
    self.RunLogging(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter= --description=',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateMissingRequiredFlag(self):
    with self.AssertRaisesExceptionRegexp(exceptions.MinimumArgumentException,
                                          r'Please specify.*'):
      self.RunLogging(
          'views update my-view --bucket=my-bucket --location=global',
          calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoPerms(self):
    expected_view = self.msgs.LogView(filter='my-filter')
    self.mock_client_v2.projects_locations_buckets_views.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket/'
            'views/my-view',
            updateMask='filter',
            logView=expected_view),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoProject(self):
    self.RunWithoutProject(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoAuth(self):
    self.RunWithoutAuth(
        'views update my-view --bucket=my-bucket --location=global '
        '--log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

if __name__ == '__main__':
  test_case.main()
