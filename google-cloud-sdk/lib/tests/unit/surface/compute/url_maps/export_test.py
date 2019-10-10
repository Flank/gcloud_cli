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
"""Tests for the url-maps export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import url_maps_test_base


class UrlMapsExportTestBeta(url_maps_test_base.UrlMapsTestBase):

  def PreSetUp(self):
    # TODO(b/135125441): Use SelectApi() instead.
    self.track = calliope.base.ReleaseTrack.BETA
    self._api = 'beta'

  def RunExport(self, command):
    self.Run('compute url-maps export ' + command)

  def testExportToStdOut(self):
    url_map_ref = self.GetUrlMapRef('url-map-1')
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    self.ExpectGetRequest(url_map_ref=url_map_ref, url_map=url_map)

    self.RunExport('url-map-1 --global')

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
            name: url-map-1
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/url-map-1
            """ % {'api': self._api}))

  def testExportToFile(self):
    url_map_ref = self.GetUrlMapRef('url-map-1', region='alaska')
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    self.ExpectGetRequest(url_map_ref=url_map_ref, url_map=url_map)

    file_name = os.path.join(self.temp_path, 'export.yaml')

    self.RunExport('url-map-1 --region alaska'
                   ' --destination {0}'.format(file_name))

    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_url_map = export_util.Import(
        message_type=self.messages.UrlMap, stream=data)
    self.AssertMessagesEqual(url_map, exported_url_map)


class UrlMapsExportTestAlpha(UrlMapsExportTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._api = 'alpha'


if __name__ == '__main__':
  test_case.main()
