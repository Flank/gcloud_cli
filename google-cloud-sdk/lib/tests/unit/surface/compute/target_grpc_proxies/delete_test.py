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
"""Tests for the target gRPC proxies delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DeleteTestV1(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_v1.targetGrpcProxies

  def RunDelete(self, command):
    self.Run('compute target-grpc-proxies delete ' + command)

  def testSingle(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1')
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-1', project='my-project'))],)

  def testMultiple(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1 proxy-2 proxy-3')
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-1', project='my-project')),
         (self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-2', project='my-project')),
         (self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-3', project='my-project'))],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.RunDelete('proxy-1 proxy-2 proxy-3')
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-1', project='my-project')),
         (self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-2', project='my-project')),
         (self._target_grpc_proxies_api, 'Delete',
          self.messages.ComputeTargetGrpcProxiesDeleteRequest(
              targetGrpcProxy='proxy-3', project='my-project'))],)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('proxy-1 proxy-2 proxy-3')
    self.CheckRequests()


class DeleteTestBeta(DeleteTestV1):

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_beta.targetGrpcProxies

  def RunDelete(self, command):
    self.Run('beta compute target-grpc-proxies delete ' + command)


class DeleteTestAlpha(DeleteTestBeta):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_alpha.targetGrpcProxies

  def RunDelete(self, command):
    self.Run('alpha compute target-grpc-proxies delete ' + command)


if __name__ == '__main__':
  test_case.main()
