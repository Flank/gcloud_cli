# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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

"""Tests of the 'buckets update' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class BucketsUpdateTest(base.LoggingTestBase):

  def testUpdateSuccess(self):
    expected_bucket = self.msgs.LogBucket(retentionDays=2)
    self.mock_client_v2.projects_locations_buckets.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket',
            updateMask='retention_days',
            logBucket=expected_bucket),
        expected_bucket)
    self.RunLogging(
        'buckets update my-bucket --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateSuccessAllProperties(self):
    expected_bucket = self.msgs.LogBucket(
        retentionDays=2, description='description',
        displayName='displayName')
    self.mock_client_v2.projects_locations_buckets.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket',
            updateMask='retention_days,display_name,description',
            logBucket=expected_bucket),
        expected_bucket)
    self.RunLogging(
        'buckets update my-bucket --location=global --retention-days=2 '
        '--description=description --display-name=displayName',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateSuccessAllDefaultProperties(self):
    expected_bucket = self.msgs.LogBucket(
        retentionDays=0, description='',
        displayName='')
    self.mock_client_v2.projects_locations_buckets.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket',
            updateMask='retention_days,display_name,description',
            logBucket=expected_bucket),
        expected_bucket)
    self.RunLogging(
        'buckets update my-bucket --location=global --retention-days=0 '
        '--description= --display-name=',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateMissingRequiredFlag(self):
    with self.AssertRaisesExceptionRegexp(exceptions.MinimumArgumentException,
                                          r'Please specify.*'):
      self.RunLogging(
          'buckets update my-bucket --location=global',
          calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoPerms(self):
    expected_bucket = self.msgs.LogBucket(retentionDays=2)
    self.mock_client_v2.projects_locations_buckets.Patch.Expect(
        self.msgs.LoggingProjectsLocationsBucketsPatchRequest(
            name='projects/my-project/locations/global/buckets/my-bucket',
            updateMask='retention_days',
            logBucket=expected_bucket),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms(
        'buckets update my-bucket --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoProject(self):
    self.RunWithoutProject(
        'buckets update my-bucket --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)

  def testUpdateNoAuth(self):
    self.RunWithoutAuth(
        'buckets update my-bucket --location=global --retention-days=2',
        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
