# Lint as: python3
# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Base class for gcloud storage surface e2e tests.

Similar to gsutil/gslib/tests/testcase/integration_testcase.py
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
from apitools.base.py import transfer
from googlecloudsdk.api_lib.storage.storage_api import StorageClient
from googlecloudsdk.api_lib.storage.storage_util import BucketReference
from googlecloudsdk.api_lib.storage.storage_util import ObjectReference
from tests.lib import e2e_base
from tests.lib.surface.storage.test_base import StorageTestBase
import six


class StorageE2ETestBase(StorageTestBase, e2e_base.WithServiceAuth):
  """Base class for gcloud storage surface e2e tests."""

  def SetUp(self):
    self.storage_client = StorageClient()

  # See go/gcloud-test-howto#guidance-on-cleaning-up-resources-in-tests
  # for more information about contextmanager and on how to call create_bucket.
  @contextlib.contextmanager
  def create_bucket(self, name=None):
    if name is None:
      name = next(self.bucket_name_generator)
    bucket = BucketReference(name)
    try:
      self.storage_client.CreateBucketIfNotExists(name)
      yield bucket
    finally:
      # Note that if CreateBucketIfNotExists does not successfully create a
      # bucket, these calls will raise exceptions, which aren't handled yet.
      for i in self.storage_client.ListBucket(bucket):
        self.storage_client.DeleteObject(ObjectReference.FromMessage(i))
      self.storage_client.DeleteBucket(bucket)

  def create_object(self, bucket, name=None, content=b''):
    if name is None:
      name = next(self.object_name_generator)
    upload = transfer.Upload.FromStream(
        six.BytesIO(content), mime_type='application/octet-stream')
    insert_req = self.storage_client.messages.StorageObjectsInsertRequest(
        bucket=bucket.bucket, name=name)
    self.storage_client.client.objects.Insert(insert_req, upload=upload)
    return ObjectReference.FromBucketRef(bucket, name)
