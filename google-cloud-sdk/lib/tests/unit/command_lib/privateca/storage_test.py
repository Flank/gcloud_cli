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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.privateca import storage
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


def GetCertificateAuthorityRef(relative_name):
  return resources.REGISTRY.ParseRelativeName(
      relative_name=relative_name,
      collection='privateca.projects.locations.certificateAuthorities')


class StorageUtilsTest(sdk_test_base.WithFakeAuth):

  _CA_NAME = 'projects/foo/locations/us-west1/certificateAuthorities/my-ca'

  def SetUp(self):
    self.ca_ref = GetCertificateAuthorityRef(self._CA_NAME)
    self.messages = storage_util.GetMessages()
    self.client = api_mock.Client(
        client_class=apis.GetClientClass('storage', 'v1'),
        real_client=storage_util.GetClient())
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  @mock.patch.object(uuid, 'uuid4', autospec=True)
  def testCreateBucketCreatesCorrectBucket(self, mock_uuid):
    bucket_uuid = '28657537-369c-41c6-81fe-0212b41cc732'
    expected_bucket_name = 'privateca_content_{}'.format(bucket_uuid)

    mock_uuid.return_value = uuid.UUID(bucket_uuid)
    self.client.buckets.Insert.Expect(
        request=self.messages.StorageBucketsInsertRequest(
            project='foo',
            bucket=self.messages.Bucket(
                name=expected_bucket_name,
                location='us-west1',
                versioning=self.messages.Bucket.VersioningValue(enabled=True))),
        response=self.messages.Bucket())

    result = storage.CreateBucketForCertificateAuthority(self.ca_ref)
    self.assertEqual(result, storage_util.BucketReference(expected_bucket_name))


if __name__ == '__main__':
  test_case.main()
