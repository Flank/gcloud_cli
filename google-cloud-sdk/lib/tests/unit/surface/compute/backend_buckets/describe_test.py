# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the backend-buckets describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_buckets import test_resources


class BackendBucketsDescribeGaTest(test_base.BaseTest,
                                   test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi('v1')
    self._backend_buckets = test_resources.BACKEND_BUCKETS

  def RunDescribe(self, command):
    self.Run('compute backend-buckets describe ' + command)

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[0]],
    ])

    self.RunDescribe("""
        my-backend-bucket
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='my-backend-bucket',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bucketName: gcs-bucket-1
            description: my backend bucket
            enableCdn: false
            name: backend-bucket-1-enable-cdn-false
            selfLink: {uri}/projects/my-project/global/backendBuckets/backend-bucket-1-enable-cdn-false
            """.format(uri=self.compute_uri)))

  def testEnableCdnTrue(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_buckets[1]],
    ])

    self.RunDescribe("""
        my-backend-bucket
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Get',
          messages.ComputeBackendBucketsGetRequest(
              backendBucket='my-backend-bucket',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bucketName: gcs-bucket-2
            description: my other backend bucket
            enableCdn: true
            name: backend-bucket-2-enable-cdn-true
            selfLink: {uri}/projects/my-project/global/backendBuckets/backend-bucket-2-enable-cdn-true
            """.format(uri=self.compute_uri)))


class BackendBucketsDescribeAlphaTest(BackendBucketsDescribeGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA

  def RunDescribe(self, command):
    self.Run('alpha compute backend-buckets describe ' + command)


class BackendBucketsDescribeBetaTest(BackendBucketsDescribeGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA

  def RunDescribe(self, command):
    self.Run('beta compute backend-buckets describe ' + command)


class BackendBucketsDescribeCompletionGaTest(test_base.BaseTest,
                                             completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self._backend_buckets = test_resources.BACKEND_BUCKETS

  def RunDescribeCompletion(self, command, choices):
    self.RunCompletion('compute backend-buckets describe ' + command, choices)

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        self._backend_buckets)
    self.RunDescribeCompletion(
        'b',
        ['backend-bucket-1-enable-cdn-false',
         'backend-bucket-2-enable-cdn-true',
         'backend-bucket-3-enable-cdn-false'])
    self.RunDescribeCompletion(
        'backend-bucket-2',
        ['backend-bucket-2-enable-cdn-true'])


class BackendBucketsDescribeCompletionAlphaTest(
    BackendBucketsDescribeCompletionGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA

  def RunDescribeCompletion(self, command, choices):
    self.RunCompletion('alpha compute backend-buckets describe ' + command,
                       choices)


class BackendBucketsDescribeCompletionBetaTest(
    BackendBucketsDescribeCompletionGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA

  def RunDescribeCompletion(self, command, choices):
    self.RunCompletion('beta compute backend-buckets describe ' + command,
                       choices)


if __name__ == '__main__':
  test_case.main()
