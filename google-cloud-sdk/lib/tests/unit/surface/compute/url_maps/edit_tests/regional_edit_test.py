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
"""Tests for the url-maps edit subcommand.

This is the primary test for edit subcommands. All other edit
subcommand tests should test the minimum functionality necessary
(i.e., did we display the correct modifiable fields? did we make the
right requests?) and should avoid exercising the edit's base class.

If this guideline is ignored, we will end up with a lot of
hard-to-maintain tests that do not yield any new information about our
code's health. This guideline is similar to how instances_list_test.py
tests every knob of the list subcommands whereas all other
*_list_test.py files only test simple wiring.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.url_maps import edit_test_base


class RegionURLMapsEditTest(edit_test_base.EditTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testSimpleEditingWithYAML(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # At the bottom of this file, you will find an example resource.
        #
        # Only fields that can be modified are shown. The original resource
        # with all of its fields is reproduced in the comment section at the
        # bottom of this document.

        ---
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube

        """ % {'api': self.api_version})
    ])

    self.make_requests.side_effect = iter([
        [self.regional_url_map],
        [],
    ])

    self.Run('compute url-maps edit --region us-west1 my-url-map --format yaml')

    self.AssertFileOpenedWith(self.regional_yaml_file_contents)
    self.CheckRequests(
        [(self._regional_url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map', region='us-west1'))],
        [(self._regional_url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self.api_version},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  hostRules=[
                      self.messages.HostRule(
                          hosts=['youtube.com', '*.youtube.com'],
                          pathMatcher='youtube'),
                  ],
                  pathMatchers=[
                      self.messages.PathMatcher(
                          name='youtube',
                          defaultService=(
                              'https://compute.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self.api_version}),
                  ],
                  name='my-url-map',
              )))],
    )


class RegionURLMapsEditBetaTest(RegionURLMapsEditTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class RegionURLMapsEditAlphaTest(RegionURLMapsEditBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
