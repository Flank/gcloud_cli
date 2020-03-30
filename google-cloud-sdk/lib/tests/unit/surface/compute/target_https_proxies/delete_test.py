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
"""Tests for the target-https-proxies delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetHttpsProxiesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self._api = ''
    self.SelectApi('v1')
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDelete(self, command):
    self.Run('compute target-https-proxies delete %s' % command)

  def testWithSingleTargetHttpsProxy(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1')

    self.CheckRequests(
        [(self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1', project='my-project'))],)

  def testWithManyTargetHttpsProxies(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests(
        [(self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1', project='my-project')),
         (self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-2', project='my-project')),
         (self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-3', project='my-project'))],)

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests(
        [(self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-1', project='my-project')),
         (self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-2', project='my-project')),
         (self._target_https_proxies_api, 'Delete',
          messages.ComputeTargetHttpsProxiesDeleteRequest(
              targetHttpsProxy='proxy-3', project='my-project'))],)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests()

  def testWithManyRegionTargetHttpsProxies(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run(self._api + """
              compute target-https-proxies delete --region us-west-1
             proxy-1 proxy-2 proxy-3
             """)

    self.CheckRequests([(self.compute.regionTargetHttpsProxies, 'Delete',
                         messages.ComputeRegionTargetHttpsProxiesDeleteRequest(
                             targetHttpsProxy='proxy-1',
                             project='my-project',
                             region='us-west-1')),
                        (self.compute.regionTargetHttpsProxies, 'Delete',
                         messages.ComputeRegionTargetHttpsProxiesDeleteRequest(
                             targetHttpsProxy='proxy-2',
                             project='my-project',
                             region='us-west-1')),
                        (self.compute.regionTargetHttpsProxies, 'Delete',
                         messages.ComputeRegionTargetHttpsProxiesDeleteRequest(
                             targetHttpsProxy='proxy-3',
                             project='my-project',
                             region='us-west-1'))],)


class TargetHttpsProxiesDeleteBetaTest(TargetHttpsProxiesDeleteTest):

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDelete(self, command):
    self.Run('beta compute target-https-proxies delete %s' % command)


class TargetHttpsProxiesDeleteAlphaTest(TargetHttpsProxiesDeleteBetaTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_https_proxies_api = self.compute.targetHttpsProxies

  def RunDelete(self, command):
    self.Run('alpha compute target-https-proxies delete %s' % command)


if __name__ == '__main__':
  test_case.main()
