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
"""Tests for the backend-buckets delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_buckets import test_resources


class BackendBucketsDeleteGaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._backend_buckets = test_resources.BACKEND_BUCKETS

  def RunDelete(self, command):
    self.Run('compute backend-buckets delete ' + command)

  def testWithSingleBackendBucket(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete("""
        backend-bucket-1
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Delete',
          messages.ComputeBackendBucketsDeleteRequest(
              backendBucket='backend-bucket-1',
              project='my-project'))])

  def testWithManyBackendBuckets(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete("""
        backend-bucket-1 backend-bucket-2
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Delete',
          messages.ComputeBackendBucketsDeleteRequest(
              backendBucket='backend-bucket-1',
              project='my-project')),

         (self.compute.backendBuckets,
          'Delete',
          messages.ComputeBackendBucketsDeleteRequest(
              backendBucket='backend-bucket-2',
              project='my-project'))])

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.RunDelete("""
        backend-bucket-1 backend-bucket-2
        """)

    self.CheckRequests(
        [(self.compute.backendBuckets,
          'Delete',
          messages.ComputeBackendBucketsDeleteRequest(
              backendBucket='backend-bucket-1',
              project='my-project')),

         (self.compute.backendBuckets,
          'Delete',
          messages.ComputeBackendBucketsDeleteRequest(
              backendBucket='backend-bucket-2',
              project='my-project'))])

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete("""
          backend-bucket-1 backend-bucket-2
          """)

    self.CheckRequests()


class BackendBucketsDeleteAlphaTest(BackendBucketsDeleteGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA

  def RunDelete(self, command):
    self.Run('alpha compute backend-buckets delete ' + command)


class BackendBucketsDeleteBetaTest(BackendBucketsDeleteGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA

  def RunDelete(self, command):
    self.Run('beta compute backend-buckets delete ' + command)


class BackendBucketsDeleteCompletionGaTest(test_base.BaseTest,
                                           completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self._backend_buckets = test_resources.BACKEND_BUCKETS

  def RunDeleteCompletion(self, command, choices):
    self.RunCompletion('compute backend-buckets delete ' + command, choices)

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        self._backend_buckets)
    self.RunDeleteCompletion(
        'b',
        [
            'backend-bucket-3-enable-cdn-false',
            'backend-bucket-2-enable-cdn-true',
            'backend-bucket-1-enable-cdn-false',
        ])


class BackendBucketsDeleteCompletionAlphaTest(
    BackendBucketsDeleteCompletionGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA

  def RunDeleteCompletion(self, command, choices):
    self.RunCompletion('alpha compute backend-buckets delete ' + command,
                       choices)


class BackendBucketsDeleteCompletionBetaTest(
    BackendBucketsDeleteCompletionGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA

  def RunDeleteCompletion(self, command, choices):
    self.RunCompletion('beta compute backend-buckets delete ' + command,
                       choices)


if __name__ == '__main__':
  test_case.main()
