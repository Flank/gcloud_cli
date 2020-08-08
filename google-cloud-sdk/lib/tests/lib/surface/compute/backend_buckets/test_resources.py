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
"""Resources that are shared by two or more backend buckets tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'


def MakeBackendBuckets(msgs, api):
  """Create backend bucket resources."""
  prefix = _COMPUTE_PATH + '/' + api
  buckets = [
      msgs.BackendBucket(
          bucketName='gcs-bucket-1',
          description='my backend bucket',
          enableCdn=False,
          name='backend-bucket-1-enable-cdn-false',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-1-enable-cdn-false')),
      msgs.BackendBucket(
          bucketName='gcs-bucket-2',
          description='my other backend bucket',
          enableCdn=True,
          name='backend-bucket-2-enable-cdn-true',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-2-enable-cdn-true')),
      msgs.BackendBucket(
          bucketName='gcs-bucket-3',
          description='third backend bucket',
          name='backend-bucket-3-enable-cdn-false',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-3-enable-cdn-false'))
  ]

  return buckets

BACKEND_BUCKETS_ALPHA = MakeBackendBuckets(alpha_messages, 'alpha')
BACKEND_BUCKETS_BETA = MakeBackendBuckets(beta_messages, 'beta')
BACKEND_BUCKETS = MakeBackendBuckets(messages, 'v1')



