# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Base class for all backend buckets tests."""

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class BackendBucketsTestBase(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):
  """Base class for all backend buckets test."""

  DEFAULT_SIGNED_URL_CACHE_MAX_AGE_SEC = 3600

  def _GetApiName(self, release_track):
    """Returns the API name for the specified release track."""
    if release_track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif release_track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    else:
      return 'v1'

  def _SetUp(self, release_track):
    """Setup common test components.

    Args:
      release_track: Release track the test is targetting.
    """
    api_name = self._GetApiName(release_track)

    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)
    self.track = release_track
    self.service = self.apitools_client.backendBuckets
    self.global_operations = self.apitools_client.globalOperations

  def RunBackendBuckets(self, command):
    """Run the compute backend-buckets command with the arguments."""
    return self.Run('compute backend-buckets ' + command)

  def GetBackendBucketRef(self, name):
    """Returns the specified backend bucket reference."""
    params = {'project': self.Project()}
    collection = 'compute.backendBuckets'
    return self.resources.Parse(name, params=params, collection=collection)

  def GetOperationRef(self, name):
    """Returns the operation reference."""
    params = {'project': self.Project()}
    collection = 'compute.globalOperations'
    return self.resources.Parse(name, params=params, collection=collection)

  def MakeBackendBucketMessage(self,
                               backend_bucket_ref,
                               gcs_bucket_name,
                               enable_cdn=False,
                               signed_url_key_names=None):
    """Returns the backend bucket message with the specified fields."""
    backend_bucket = self.messages.BackendBucket(
        name=backend_bucket_ref.Name(),
        bucketName=gcs_bucket_name,
        enableCdn=enable_cdn,
        selfLink=backend_bucket_ref.SelfLink())
    if signed_url_key_names:
      backend_bucket.cdnPolicy = self.messages.BackendBucketCdnPolicy(
          signedUrlKeyNames=signed_url_key_names,
          signedUrlCacheMaxAgeSec=self.DEFAULT_SIGNED_URL_CACHE_MAX_AGE_SEC)
    return backend_bucket

  def MakeOperationMessage(self, operation_ref, resource_ref=None):
    """Returns the operation message for the specified operation reference."""
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def ExpectGetRequest(self,
                       backend_bucket_ref,
                       backend_bucket=None,
                       exception=None):
    """Expects the backend bucket Get request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendBucketsGetRequest
    self.service.Get.Expect(
        request=request_type(**backend_bucket_ref.AsDict()),
        response=backend_bucket,
        exception=exception)

  def ExpectOperationGetRequest(self, operation_ref, operation):
    """Expects the operation Get request to be invoked."""
    self.global_operations.Get.Expect(
        self.messages.ComputeGlobalOperationsGetRequest(
            operation=operation_ref.operation, project=operation_ref.project),
        operation)

  def ExpectAddSignedUrlKeyRequest(self,
                                   backend_bucket_ref,
                                   key_name,
                                   key_value,
                                   response=None,
                                   exception=None):
    """Expects the AddSignedUrlKey request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendBucketsAddSignedUrlKeyRequest

    request = request_type(
        project=backend_bucket_ref.project,
        backendBucket=backend_bucket_ref.Name(),
        signedUrlKey=messages.SignedUrlKey(
            keyName=key_name, keyValue=key_value))

    self.service.AddSignedUrlKey.Expect(
        request=request, response=response, exception=exception)

  def ExpectDeleteSignedUrlKeyRequest(self,
                                      backend_bucket_ref,
                                      key_name,
                                      response=None,
                                      exception=None):
    """Expects the DeleteSignedUrlKey request to be invoked."""
    messages = self.messages
    request_type = messages.ComputeBackendBucketsDeleteSignedUrlKeyRequest

    request = request_type(
        project=backend_bucket_ref.project,
        backendBucket=backend_bucket_ref.Name(),
        keyName=key_name)

    self.service.DeleteSignedUrlKey.Expect(
        request=request, response=response, exception=exception)
