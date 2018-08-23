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
"""Tests for the target-http-proxies delete subcommand."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetHttpProxiesDeleteTest(test_base.BaseTest,
                                  completer_test_base.CompleterBase):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute.targetHttpProxies

  def RunDelete(self, command):
    self.Run('compute target-http-proxies delete ' + command)

  def testWithSingleTargetHttpProxy(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-1', project='my-project'))],)

  def testWithManyTargetHttpProxies(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-1', project='my-project')),
         (self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-2', project='my-project')),
         (self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-3', project='my-project'))],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests(
        [(self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-1', project='my-project')),
         (self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-2', project='my-project')),
         (self._target_http_proxies_api, 'Delete',
          self.messages.ComputeTargetHttpProxiesDeleteRequest(
              targetHttpProxy='proxy-3', project='my-project'))],)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('proxy-1 proxy-2 proxy-3')

    self.CheckRequests()

  class MockTransformUri(object):

    def __init__(self, uri_list):
      self.original_uri_list = uri_list[:]
      self.Reset()

    def Reset(self):
      self.uri_list = self.original_uri_list[:]

    def Transform(self, *args, **kwargs):  # pylint: disable=unused-argument
      url_map = self.uri_list.pop() if self.uri_list else 'ERROR'
      return ('https://www.googleapis.com/compute/v1/projects/my-project'
              '/global/targetHttpProxies/{0}').format(url_map)

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.TARGET_HTTP_PROXIES)
    uri_list = [
        'target-http-proxy-1',
        'target-http-proxy-2',
        'target-http-proxy-3',
    ]
    self.RunCompletion('compute target-http-proxies delete t', uri_list)


class TargetHttpProxiesDeleteAlphaTest(TargetHttpProxiesDeleteTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_http_proxies_api = self.compute_alpha.targetHttpProxies

  def RunDelete(self, command):
    self.Run('alpha compute target-http-proxies delete --global ' + command)


if __name__ == '__main__':
  test_case.main()
