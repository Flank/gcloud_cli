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
"""Tests for the url-maps delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

MESSAGES = apis.GetMessagesModule('compute', 'v1')


class UrlMapsDeleteTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._url_maps_api = self.compute_v1.urlMaps

  def RunDelete(self, command):
    self.Run('compute url-maps delete ' + command)

  def ExpectCompletion(self, expected_completion):
    self.RunCompletion('compute url-maps delete ', expected_completion)

  def testWithSingleUrlMap(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('map-1')

    self.CheckRequests([(self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-1', project='my-project'))],)

  def testWithManyUrlMaps(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('map-1 map-2 map-3')

    self.CheckRequests([(self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-1', project='my-project')),
                        (self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-2', project='my-project')),
                        (self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-3', project='my-project'))],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.RunDelete('map-1 map-2 map-3')

    self.CheckRequests([(self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-1', project='my-project')),
                        (self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-2', project='my-project')),
                        (self._url_maps_api, 'Delete',
                         self.messages.ComputeUrlMapsDeleteRequest(
                             urlMap='map-3', project='my-project'))],)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('map-1 map-2 map-3')

    self.CheckRequests()

  def testDeleteCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.URL_MAPS)
    self.ExpectCompletion([
        'url-map-3',
        'url-map-4',
        'url-map-1',
        'url-map-2',
    ])


class UrlMapsDeleteTestBeta(UrlMapsDeleteTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.urlMaps

  def RunDelete(self, command):
    self.Run('beta compute url-maps delete --global ' + command)


class UrlMapsDeleteTestAlpha(UrlMapsDeleteTestBeta):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.urlMaps

  def RunDelete(self, command):
    self.Run('alpha compute url-maps delete --global ' + command)

  def testDeleteCompletion(self):
    # Completion test handled in misc_completion_test.py
    pass


if __name__ == '__main__':
  test_case.main()
