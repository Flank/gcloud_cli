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


class BucketsCreateTest(base.LoggingTestBase):

  def testCreateSuccess(self):
    expected_bucket = self.msgs.LogBucket(
        retentionDays=2, displayName='display_name', description='description')
    self.mock_client_v2.projects_locations_buckets.Create.Expect(
        self.msgs.LoggingProjectsLocationsBucketsCreateRequest(
            bucketId='pierogie',
            parent='projects/my-project/locations/global',
            logBucket=expected_bucket),
        expected_bucket)
    self.RunLogging(
        'buckets create pierogie --location=global --retention-days=2 '
        '--display-name=display_name --description=description',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoPerms(self):
    expected_bucket = self.msgs.LogBucket(retentionDays=2)
    self.mock_client_v2.projects_locations_buckets.Create.Expect(
        self.msgs.LoggingProjectsLocationsBucketsCreateRequest(
            bucketId='pierogie',
            parent='projects/my-project/locations/global',
            logBucket=expected_bucket),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'buckets create pierogie --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoLocation(self):
    with self.AssertRaisesArgumentError():
      self.RunLogging(
          'buckets create pierogie --retention-days=2',
          calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoProject(self):
    self.RunWithoutProject(
        'buckets create pierogie --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)

  def testCreateNoAuth(self):
    self.RunWithoutAuth(
        'buckets create pierogie --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
