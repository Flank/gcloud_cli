# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import results_bucket
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.android import unit_base


class ResultsBucketOpsTests(unit_base.AndroidMockClientTest):
  """Unit tests for test/lib/results_bucket.py.

  Note: integration tests for this class are in integration/bucket_test.py.
  """

  def testResultsBucketOps_ConstructGcsResultsRoot(self):
    bucket_ops = self._CreateBucketOps('gatorade')
    self.assertEqual(bucket_ops.gcs_results_root,
                     'gs://gatorade/2015-02-24_12:13:14.567890_ABCD/')

  def testResultsBucketOps_ConstructGcsResultsUrl(self):
    bucket_ops = self._CreateBucketOps('gatorade')
    self.assertEqual(
        bucket_ops._gcs_results_url,
        'https://console.developers.google.com/storage/browser/gatorade/'
        '2015-02-24_12:13:14.567890_ABCD/')

  def testResultsBucketOps_GetDefaultBucket_GetsHttp404Error(self):
    request = (
        self.toolresults_msgs.ToolresultsProjectsInitializeSettingsRequest(
            projectId=self.PROJECT_ID))
    self.tr_client.projects.InitializeSettings.Expect(
        request=request,
        exception=test_utils.MakeHttpError(
            'borked', 'Simulated failure to get default bucket.'))

    with self.assertRaises(exceptions.HttpException) as e:
      self._CreateBucketOps(None)

    msg = str(e.exception)
    self.assertIn('Http error while trying to fetch the default', msg)
    self.assertIn('Simulated failure to get default bucket', msg)

  def testResultsBucketOps_GetDefaultBucket_GetsHttp403Error(self):
    request = (
        self.toolresults_msgs.ToolresultsProjectsInitializeSettingsRequest(
            projectId=self.PROJECT_ID))
    self.tr_client.projects.InitializeSettings.Expect(
        request=request,
        exception=test_utils.MakeHttpError('choked', 'Bucket access denied',
                                           403))

    with self.assertRaises(exceptions.HttpException) as e:
      self._CreateBucketOps(None)

    msg = str(e.exception)
    self.assertIn('403: Bucket access denied', msg)
    self.assertIn('billing enabled', msg)

  def testResultsBucketOps_GetDefaultBucket_Succeeds(self):
    request = (
        self.toolresults_msgs.ToolresultsProjectsInitializeSettingsRequest(
            projectId=self.PROJECT_ID))
    self.tr_client.projects.InitializeSettings.Expect(
        request=request,
        response=self.toolresults_msgs.ProjectSettings(defaultBucket='pail'))

    bucket_ops = self._CreateBucketOps(None)

    self.assertEqual(bucket_ops.gcs_results_root,
                     'gs://pail/2015-02-24_12:13:14.567890_ABCD/')

  def _CreateBucketOps(self, bucket_name):
    if bucket_name:
      self._ExpectBucketsGet(bucket_name)
    return results_bucket.ResultsBucketOps(
        self.PROJECT_ID, bucket_name, '2015-02-24_12:13:14.567890_ABCD',
        self.tr_client, self.toolresults_msgs, self.storage_client)

  def _ExpectBucketsGet(self, bucket_name):
    get_req = self.storage_msgs.StorageBucketsGetRequest(bucket=bucket_name)
    get_resp = self.storage_msgs.Bucket()
    self.storage_client.buckets.Get.Expect(request=get_req, response=get_resp)


if __name__ == '__main__':
  test_case.main()
