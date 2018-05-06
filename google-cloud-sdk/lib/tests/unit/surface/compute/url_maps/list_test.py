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
"""Tests for the url-maps list subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class URLMapsListTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self._url_maps_api = self.compute_v1.urlMaps
    self._test_url_maps = test_resources.URL_MAPS

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def RunList(self, command):
    self.Run('compute url-maps list ' + command)

  def testSimpleCase(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._test_url_maps),
    ]

    self.RunList('')

    self.list_json.assert_called_once_with(
        requests=[(self._url_maps_api,
                   'List',
                   self.messages.ComputeUrlMapsListRequest(
                       maxResults=500,
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME      DEFAULT_SERVICE
            url-map-1 backendServices/default-service
            url-map-2 backendServices/default-service
            url-map-3 backendServices/default-service
            url-map-4 backendBuckets/default-bucket
            """),
        normalize_space=True)

  def testUrlMapsCompleter(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._test_url_maps),
    ]

    self.RunCompleter(
        flags.UrlMapsCompleter,
        expected_command=[
            'compute',
            'url-maps',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'url-map-1',
            'url-map-2',
            'url-map-3',
            'url-map-4',
        ],
        cli=self.cli,
    )


class URLMapsListBetaTest(URLMapsListTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._url_maps_api = self.compute_beta.urlMaps
    self._test_url_maps = test_resources.URL_MAPS_BETA

  def RunList(self, command):
    self.Run('beta compute url-maps list ' + command)


class URLMapsListAlphaTest(URLMapsListTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._url_maps_api = self.compute_alpha.urlMaps
    self._test_url_maps = test_resources.URL_MAPS_ALPHA

  def RunList(self, command):
    self.Run('alpha compute url-maps list ' + command)


if __name__ == '__main__':
  test_case.main()
