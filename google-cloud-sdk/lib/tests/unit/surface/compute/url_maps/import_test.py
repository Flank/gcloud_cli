# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the url maps import subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import url_maps_test_base


class UrlMapsImportTestBeta(url_maps_test_base.UrlMapsTestBase):

  def PreSetUp(self):
    # TODO(b/135125441): Use SelectApi() instead.
    self.track = calliope.base.ReleaseTrack.BETA
    self._api = 'beta'

  def RunImport(self, command):
    self.Run('compute url-maps import ' + command)

  def testImportUrlMapsFromStdIn(self):
    url_map_ref = self.GetUrlMapRef('url-map-1')
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    url_map.description = 'changed'

    self.ExpectGetRequest(
        url_map_ref=url_map_ref, exception=http_error.MakeHttpError(code=404))
    self.ExpectInsertRequest(url_map_ref=url_map_ref, url_map=url_map)

    self.WriteInput(export_util.Export(url_map))

    self.RunImport('url-map-1 --global')

  def testImportUrlMapsFromFile(self):
    url_map_ref = self.GetUrlMapRef('url-map-1', region='alaska')
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    url_map.description = 'changed'
    url_map.pathMatchers = [
        self.messages.PathMatcher(
            name='temp',
            defaultService=url_map.defaultService,
            routeRules=[
                self.messages.HttpRouteRule(
                    routeAction=self.messages.HttpRouteAction(
                        weightedBackendServices=[
                            self.messages.WeightedBackendService(
                                backendService=url_map.defaultService, weight=1)
                        ],
                        faultInjectionPolicy=self.messages.HttpFaultInjection(
                            abort=self.messages.HttpFaultAbort(
                                percentage=10.0))))
            ])
    ]

    # Write the modified url_map to a file.
    file_name = os.path.join(self.temp_path, 'temp-bs.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=url_map, stream=stream)

    self.ExpectGetRequest(
        url_map_ref=url_map_ref,
        url_map=self.MakeTestUrlMap(self.messages, self._api))
    self.ExpectPatchRequest(url_map_ref=url_map_ref, url_map=url_map)

    self.WriteInput('y\n')

    self.RunImport('url-map-1 --source {0} --region alaska'.format(file_name))

  def testImportBackendServiceInvalidSchema(self):
    # This test ensures that the schema files do not contain invalid fields.
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    # id and fingerprint fields should be removed from schema files manually.
    url_map.id = 12345

    # Write the modified url_map to a file.
    file_name = os.path.join(self.temp_path, 'temp-bs.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=url_map, stream=stream)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, "Additional properties are not allowed "
        "('id' was unexpected)"):
      self.RunImport('url-map-1 --source {0} --global'.format(file_name))


class UrlMapsImportTestAlpha(UrlMapsImportTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA
    self._api = 'beta'


if __name__ == '__main__':
  test_case.main()
