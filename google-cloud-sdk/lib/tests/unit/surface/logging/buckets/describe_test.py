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


class ProjectBucketsGetTest(base.LoggingTestBase):

  def testGet(self):
    test_bucket = self.msgs.LogBucket(
        name='projects/my-project/locations/global/buckets/my-bucket')
    self.mock_client_v2.projects_locations_buckets.Get.Expect(
        self.msgs.LoggingProjectsLocationsBucketsGetRequest(
            name='projects/my-project/locations/global/buckets/my-bucket'),
        test_bucket)
    self.RunLogging('buckets describe my-bucket --location global',
                    calliope_base.ReleaseTrack.ALPHA)
    self.AssertOutputContains(test_bucket.name)

  def testGetFolder(self):
    test_bucket = self.msgs.LogBucket(
        name='folders/123/locations/global/buckets/my-bucket')
    self.mock_client_v2.projects_locations_buckets.Get.Expect(
        self.msgs.LoggingProjectsLocationsBucketsGetRequest(
            name='folders/123/locations/global/buckets/my-bucket'),
        test_bucket)
    self.RunLogging('buckets describe my-bucket --location global --folder 123',
                    calliope_base.ReleaseTrack.ALPHA)
    self.AssertOutputContains(test_bucket.name)

  def testGetNoPerms(self):
    self.mock_client_v2.projects_locations_buckets.Get.Expect(
        self.msgs.LoggingProjectsLocationsBucketsGetRequest(
            name='projects/my-project/locations/global/buckets/my-bucket'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'buckets describe my-bucket --location global',
        calliope_base.ReleaseTrack.ALPHA)

  def testGetNoProject(self):
    self.RunWithoutProject(
        'buckets describe my-bucket --location global',
        calliope_base.ReleaseTrack.ALPHA)

  def testGetNoAuth(self):
    self.RunWithoutAuth(
        'buckets describe my-bucket --location global',
        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
