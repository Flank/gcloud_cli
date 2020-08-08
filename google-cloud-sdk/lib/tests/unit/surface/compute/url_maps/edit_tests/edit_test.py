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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import edit
from tests.lib import test_case
from tests.lib.surface.compute.url_maps import edit_test_base


class URLMapsEditTest(edit_test_base.EditTestBase):

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
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingWithBackendBucketsAndYAML(self):
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
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testUriNormalization(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        ---
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        tests:
        - host: youtube.com
          path: /view/this
          service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://compute.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendServices/youtube-watch') %
                                  {'api': self.api},
                              ),
                          ],
                      ),
                  ],
                  name='my-url-map',
                  tests=[
                      self.messages.UrlMapTest(
                          host='youtube.com',
                          path='/view/this',
                          service=(
                              'https://compute.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-watch') % {'api': self.api}),
                  ],
              )))],
    )

  def testUriNormalizationWithBackendBuckets(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        ---
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
          - paths:
            - /images/*
            service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images-bucket
        tests:
        - host: youtube.com
          path: /view/this
          service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://compute.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendServices/youtube-watch') %
                                  {'api': self.api},
                              ),
                              self.messages.PathRule(
                                  paths=['/images/*'],
                                  service=(
                                      'https://compute.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendBuckets/images-bucket') %
                                  {'api': self.api},
                              ),
                          ],
                      ),
                  ],
                  name='my-url-map',
                  tests=[
                      self.messages.UrlMapTest(
                          host='youtube.com',
                          path='/view/this',
                          service=(
                              'https://compute.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-watch') % {'api': self.api}),
                  ],
              )))],
    )

  def testUriNormalizationFullUriRequired(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
            ---
            defaultService: backendBuckets/my-backend-bucket
            """), edit.NoSaveException
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertErrContains(
        '[defaultService] must be referenced using URIs', normalize_space=True)

  def testRemovalOfEntireStructuresWithYAML(self):
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



        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # Only fields that can be modified are shown. The full resource with
        # its output-only fields is:

        ---
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: My URL Map

        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
                  description='My URL Map',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingWithJSON(self):
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


        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # Only fields that can be modified are shown. The full resource with
        # its output-only fields is:
        #
        #   {
        #     "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
        #     "description": "My URL Map",
        #     "fingerprint": "bXktZmluZ2VycHJpbnQ=",
        #     "hostRules": [
        #       {
        #         "hosts": [
        #           "google.com",
        #           "*.google.com"
        #         ],
        #         "pathMatcher": "www"
        #       },
        #       {
        #         "hosts": [
        #           "youtube.com",
        #           "*.youtube.com"
        #         ],
        #         "pathMatcher": "youtube"
        #       }
        #     ],
        #     "name": "my-url-map",
        #     "pathMatchers": [
        #       {
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
          "description": "A changed description",
          "hostRules": [
            {
              "hosts": [
                "youtube.com",
                "*.youtube.com"
              ],
              "pathMatcher": "youtube"
            }
          ],
          "pathMatchers": [
            {
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format json')

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingBackendBucketsWithJSON(self):
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


        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # Only fields that can be modified are shown. The full resource with
        # its output-only fields is:
        #
        #   {
        #     "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
        #     "description": "My URL Map",
        #     "fingerprint": "bXktZmluZ2VycHJpbnQ=",
        #     "hostRules": [
        #       {
        #         "hosts": [
        #           "google.com",
        #           "*.google.com"
        #         ],
        #         "pathMatcher": "www"
        #       },
        #       {
        #         "hosts": [
        #           "youtube.com",
        #           "*.youtube.com"
        #         ],
        #         "pathMatcher": "youtube"
        #       }
        #     ],
        #     "name": "my-url-map",
        #     "pathMatchers": [
        #       {
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket",
          "description": "A changed description",
          "hostRules": [
            {
              "hosts": [
                "youtube.com",
                "*.youtube.com"
              ],
              "pathMatcher": "youtube"
            }
          ],
          "pathMatchers": [
            {
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            },
            {
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/image-bucket",
              "name": "images"
            }
          ]
        }
        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format json')

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self.api},
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
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self.api}),
                      self.messages.PathMatcher(
                          name='images',
                          defaultService=(
                              'https://compute.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendBuckets/'
                              'image-bucket') % {'api': self.api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testNoModificationCase(self):
    self.mock_edit.side_effect = iter([self.yaml_file_contents])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             project='my-project',
                             urlMap='my-url-map',
                         ))],)

  def testEditingWithJSONWithSyntaxErrorsAndNoRetry(self):
    self.WriteInput('n\n')  # Answer no when prompted to try again.

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

        {
          "defaultService", "my-backend-service",
          "description": "A changed description"
        }
        """)
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.Run('compute url-maps edit my-url-map --format json')

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             project='my-project',
                             urlMap='my-url-map',
                         ))],)
    self.AssertErrContains('There was a problem parsing your changes: Expecting'
                           ' \':\' delimiter: line')

    # The syntax error occurred at line 15, so we check to make sure we
    # did our calculations correctly.
    self.AssertErrContains('15 column 19 (char 485)')

    self.AssertErrContains('Edit aborted by user.')

  def testEditingWithJSONWithSyntaxErrorsAndRetry(self):
    self.WriteInput('y\n')  # Answer yes when prompted to try again.

    bad_modifications = textwrap.dedent("""\
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

        {
          "defaultService", "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
          "description": "A changed description"
        }
        """ % {'api': self.api})

    self.mock_edit.side_effect = iter([
        bad_modifications,
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

            {
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
              "description": "A changed description"
            }
            """ % {'api': self.api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format json')

    self.AssertFileOpenedWith(self.json_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )
    self.AssertErrContains('There was a problem parsing your changes: Expecting'
                           ' \':\' delimiter: line')
    self.AssertErrContains('15 column 19 (char 485)')

  def testEditingWithYAMLWithSyntaxErrorsAndNoRetry(self):
    self.WriteInput('n\n')  # Answer no when prompted to try again.

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
        *defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeUrlMapsGetRequest(
                             project='my-project',
                             urlMap='my-url-map',
                         ))],)
    self.AssertErrContains(
        'There was a problem parsing your changes: Failed to parse YAML: '
        'found undefined alias')

    # The syntax error occurred at line 15, so we check to make sure we
    # did our calculations correctly.
    self.AssertErrContains(r'in \"<unicode string>\", line 15, column 1:')

    self.AssertErrContains('Edit aborted by user.')

  def testEditingWithYAMLWithSyntaxErrorsAndRetry(self):
    self.WriteInput('y\n')  # Answer yes when prompted to try again.

    bad_modifications = textwrap.dedent("""\
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
        *defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self.api})

    self.mock_edit.side_effect = iter([
        bad_modifications,
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
            defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
            description: A changed description

            """ % {'api': self.api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )

    self.AssertErrContains(
        'There was a problem parsing your changes: Failed to parse YAML: '
        'found undefined alias')
    self.AssertErrContains(r'in \"<unicode string>\", line 15, column 1:')

  def testEditingWithServerError(self):
    self.WriteInput('n\n')  # Answer no when prompted to try again.

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
        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self.api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        exceptions.ToolException('resource not found'),
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.Run('compute url-maps edit my-url-map --format yaml')

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://compute.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self.api},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )
    self.AssertErrContains(
        'There was a problem applying your changes: resource not found')

    self.AssertErrContains('Edit aborted by user.')


class URLMapsEditBetaTest(URLMapsEditTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class URLMapsEditAlphaTest(URLMapsEditBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
