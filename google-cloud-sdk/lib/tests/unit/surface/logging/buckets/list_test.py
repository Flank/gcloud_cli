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

"""Tests of the 'buckets' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class BucketsListTestBase(base.LoggingTestBase):

  def SetUp(self):
    self._buckets = [
        self.msgs.LogBucket(
            name='first-bucket'),
        self.msgs.LogBucket(
            name='second-bucket')]

  def _setProjectBucketsListResponse(
      self, buckets, parent='projects/my-project/locations/my-location'):
    self.mock_client_v2.projects_locations_buckets.List.Expect(
        self.msgs.LoggingProjectsLocationsBucketsListRequest(
            parent=parent),
        self.msgs.ListBucketsResponse(buckets=buckets))


class ProjectBucketsListTest(BucketsListTestBase):

  def testList(self):
    self._setProjectBucketsListResponse(self._buckets)
    self.RunLogging('buckets list --location my-location',
                    calliope_base.ReleaseTrack.BETA)
    for bucket in self._buckets:
      self.AssertOutputContains(bucket.name)

  def testListLocationDefaulted(self):
    self._setProjectBucketsListResponse(
        self._buckets, 'projects/my-project/locations/-')
    self.RunLogging('buckets list', calliope_base.ReleaseTrack.BETA)
    for bucket in self._buckets:
      self.AssertOutputContains(bucket.name)

  def testListLimit(self):
    self._setProjectBucketsListResponse(self._buckets)
    self.RunLogging('buckets list --location=my-location --limit 1',
                    calliope_base.ReleaseTrack.BETA)
    self.AssertOutputContains(self._buckets[0].name)
    self.AssertOutputNotContains(self._buckets[1].name)

  def testListNoPerms(self):
    self.mock_client_v2.projects_locations_buckets.List.Expect(
        self.msgs.LoggingProjectsLocationsBucketsListRequest(
            parent='projects/my-project/locations/my-location'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('buckets list --location=my-location',
                         calliope_base.ReleaseTrack.BETA)

  def testListNoProject(self):
    self.RunWithoutProject('buckets list', calliope_base.ReleaseTrack.BETA)

  def testListNoAuth(self):
    self.RunWithoutAuth('buckets list', calliope_base.ReleaseTrack.BETA)


if __name__ == '__main__':
  test_case.main()
