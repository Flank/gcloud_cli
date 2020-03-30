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

"""Tests of the 'views' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class ViewsListTestBase(base.LoggingTestBase):

  def SetUp(self):
    self._views = [
        self.msgs.LogView(
            name='first-view'),
        self.msgs.LogView(
            name='second-view')]

  def _setProjectViewsListResponse(
      self, views,
      parent='projects/my-project/locations/my-location/buckets/my-bucket'):
    self.mock_client_v2.projects_locations_buckets_views.List.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsListRequest(
            parent=parent),
        self.msgs.ListViewsResponse(views=views))


class ProjectViewsListTest(ViewsListTestBase):

  def testList(self):
    self._setProjectViewsListResponse(self._views)
    self.RunLogging('views list --location=my-location --bucket=my-bucket',
                    calliope_base.ReleaseTrack.ALPHA)
    for view in self._views:
      self.AssertOutputContains(view.name)

  def testListLimit(self):
    self._setProjectViewsListResponse(self._views)
    self.RunLogging(
        'views list --location=my-location --bucket=my-bucket --limit=1',
        calliope_base.ReleaseTrack.ALPHA)
    self.AssertOutputContains(self._views[0].name)
    self.AssertOutputNotContains(self._views[1].name)

  def testListNoPerms(self):
    self.mock_client_v2.projects_locations_buckets_views.List.Expect(
        self.msgs.LoggingProjectsLocationsBucketsViewsListRequest(
            parent='projects/my-project/locations/my-location/'
            'buckets/my-bucket'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('views list --location=my-location --bucket=my-bucket',
                         calliope_base.ReleaseTrack.ALPHA)

  def testListNoProject(self):
    self.RunWithoutProject(
        'views list --location=my-location --bucket=-my-bucket',
        calliope_base.ReleaseTrack.ALPHA)

  def testListNoAuth(self):
    self.RunWithoutAuth(
        'views list --location=my-location --bucket=-my-bucket',
        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
