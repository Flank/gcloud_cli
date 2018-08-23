# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the project-info set-usage-bucket subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


messages = core_apis.GetMessagesModule('compute', 'v1')


class ProjectInfoSetUsageBucketTest(test_base.BaseTest):

  def testClearAndPrefix(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--prefix\] cannot be specified when unsetting the usage bucket.'):
      self.Run("""
          compute project-info set-usage-bucket
            --no-bucket
            --prefix my-prefix
          """)

    self.CheckRequests()

  def testBucketIsRequired(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute project-info set-usage-bucket
          """)

    self.CheckRequests()
    self.AssertErrContains('Exactly one of (--bucket | --no-bucket)'
                           ' must be specified.')

  def testClear(self):
    self.Run("""compute project-info set-usage-bucket --no-bucket""")

    self.CheckRequests(
        [(self.compute_v1.projects,
          'SetUsageExportBucket',
          messages.ComputeProjectsSetUsageExportBucketRequest(
              project='my-project',
              usageExportLocation=messages.UsageExportLocation()
          ))],
    )

  def testWithHttpsBucketUri(self):
    self.Run("""
        compute project-info set-usage-bucket
          --bucket https://www.googleapis.com/storage/v1/b/31dd
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'SetUsageExportBucket',
          messages.ComputeProjectsSetUsageExportBucketRequest(
              project='my-project',
              usageExportLocation=messages.UsageExportLocation(
                  bucketName='https://www.googleapis.com/storage/v1/b/31dd')
          ))],
    )

  def testWithGsBucketUri(self):
    self.Run("""
        compute project-info set-usage-bucket
          --bucket gs://31dd
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'SetUsageExportBucket',
          messages.ComputeProjectsSetUsageExportBucketRequest(
              project='my-project',
              usageExportLocation=messages.UsageExportLocation(
                  bucketName='https://www.googleapis.com/storage/v1/b/31dd')
          ))],
    )

  def testWithPrefix(self):
    self.Run("""
        compute project-info set-usage-bucket
          --bucket https://www.googleapis.com/storage/v1/b/31dd
          --prefix my-prefix
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'SetUsageExportBucket',
          messages.ComputeProjectsSetUsageExportBucketRequest(
              project='my-project',
              usageExportLocation=messages.UsageExportLocation(
                  bucketName='https://www.googleapis.com/storage/v1/b/31dd',
                  reportNamePrefix='my-prefix')
          ))],
    )


if __name__ == '__main__':
  test_case.main()
