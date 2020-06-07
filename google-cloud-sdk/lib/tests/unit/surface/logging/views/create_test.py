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

"""Tests of the 'buckets create' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class ViewsCreateTest(base.LoggingTestBase):

  def testCreateSuccess(self):
    expected_view = self.msgs.LogView(
        filter='my-filter', description='description')
    self.mock_client_v2.projects_locations_buckets_views.Create.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsCreateRequest(
            viewId='my-view',
            parent='projects/my-project/locations/global/buckets/my-bucket',
            logView=expected_view),
        expected_view)
    self.RunLogging(
        'views create my-view --location=global --description=description '
        '--bucket=my-bucket --log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoPerms(self):
    expected_view = self.msgs.LogView(
        filter='my-filter', description='description')
    self.mock_client_v2.projects_locations_buckets_views.Create.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsCreateRequest(
            viewId='my-view',
            parent='projects/my-project/locations/global/buckets/my-bucket',
            logView=expected_view),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'views create my-view --location=global --description=description '
        '--bucket=my-bucket --log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoLocation(self):
    with self.AssertRaisesArgumentError():
      self.RunLogging(
          'views create my-view --description=description '
          '--log-filter=my-filter',
          calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoProject(self):
    self.RunWithoutProject(
        'views create my-view --location=global --description=description '
        '--bucket=my-bucket --log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoAuth(self):
    self.RunWithoutAuth(
        'views create my-view --location=global --description=description '
        '--bucket=my-bucket --log-filter=my-filter',
        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
