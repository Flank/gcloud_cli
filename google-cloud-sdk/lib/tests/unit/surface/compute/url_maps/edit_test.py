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

Kittens will die if the guideline is ignored.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class URLMapsEditTest(test_base.BaseEditTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = 'v1'
    self._url_maps_api = self.compute_v1.urlMaps
    self.url_map = self._CreateUrlMap()
    self.yaml_file_contents = self._CreateYaml()
    self.json_file_contents = self._CreateJson()

  def _CreateUrlMap(self):
    return self.messages.UrlMap(
        defaultService=(
            'https://www.googleapis.com/compute/%(api)s/projects/'
            'my-project/global/backendServices/my-backend-service' % {
                'api': self._api}),
        description='My URL Map',
        fingerprint=b'my-fingerprint',
        hostRules=[
            self.messages.HostRule(
                hosts=['google.com', '*.google.com'],
                pathMatcher='www'),
            self.messages.HostRule(
                hosts=['youtube.com', '*.youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=(
                    'https://www.googleapis.com/compute/%(api)s/projects/'
                    'my-project/global/backendServices/www-service' % {
                        'api': self._api})),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    'https://www.googleapis.com/compute/%(api)s/projects/'
                    'my-project/global/backendServices/youtube-service' % {
                        'api': self._api})),
        ],
        name='my-url-map',
        selfLink=(
            'https://www.googleapis.com/compute/%(api)s/projects/my-project/'
            'global/urlMaps/my-url-map' % {
                'api': self._api}))

  def _CreateYaml(self):
    return textwrap.dedent("""\
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

        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: My URL Map
        hostRules:
        - hosts:
          - google.com
          - '*.google.com'
          pathMatcher: www
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service
          name: www
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        # Example resource:
        # -----------------
        #
        #   defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
        #   hostRules:
        #   - hosts:
        #     - '*.google.com'
        #     - google.com
        #     pathMatcher: www
        #   - hosts:
        #     - '*.youtube.com'
        #     - youtube.com
        #     - '*-youtube.com'
        #     pathMatcher: youtube
        #   name: site-map
        #   pathMatchers:
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
        #     name: www
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
        #     - paths:
        #       - /search/ads
        #       - /search/ads/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #     - paths:
        #       - /images/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #     name: youtube
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
        #     - paths:
        #       - /watch
        #       - /view
        #       - /preview
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        #   tests:
        #   - host: www.google.com
        #     path: /search/ads/inline?q=flowers
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #   - host: youtube.com
        #     path: /watch/this
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #   - host: youtube.com
        #     path: /images/logo.png
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #
        # Original resource:
        # ------------------
        #
        #   defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        #   description: My URL Map
        #   fingerprint: bXktZmluZ2VycHJpbnQ=
        #   hostRules:
        #   - hosts:
        #     - google.com
        #     - '*.google.com'
        #     pathMatcher: www
        #   - hosts:
        #     - youtube.com
        #     - '*.youtube.com'
        #     pathMatcher: youtube
        #   name: my-url-map
        #   pathMatchers:
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service
        #     name: www
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
        #     name: youtube
        #   selfLink: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
        """ % {'api': self._api})

  def _CreateJson(self):
    return textwrap.dedent("""\
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
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
          "description": "My URL Map",
          "hostRules": [
            {
              "hosts": [
                "google.com",
                "*.google.com"
              ],
              "pathMatcher": "www"
            },
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
              "name": "www"
            },
            {
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        # Example resource:
        # -----------------
        #
        #   {
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service",
        #     "hostRules": [
        #       {
        #         "hosts": [
        #           "*.google.com",
        #           "google.com"
        #         ],
        #         "pathMatcher": "www"
        #       },
        #       {
        #         "hosts": [
        #           "*.youtube.com",
        #           "youtube.com",
        #           "*-youtube.com"
        #         ],
        #         "pathMatcher": "youtube"
        #       }
        #     ],
        #     "name": "site-map",
        #     "pathMatchers": [
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default",
        #         "name": "www",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search"
        #           },
        #           {
        #             "paths": [
        #               "/search/ads",
        #               "/search/ads/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #           },
        #           {
        #             "paths": [
        #               "/images/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #           }
        #         ]
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default",
        #         "name": "youtube",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search"
        #           },
        #           {
        #             "paths": [
        #               "/watch",
        #               "/view",
        #               "/preview"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch"
        #           }
        #         ]
        #       }
        #     ],
        #     "tests": [
        #       {
        #         "host": "www.google.com",
        #         "path": "/search/ads/inline?q=flowers",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/watch/this",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/images/logo.png",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #       }
        #     ]
        #   }
        #
        # Original resource:
        # ------------------
        #
        #   {
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }
        """ % {'api': self._api})

  def RunEdit(self, command):
    self.Run('compute url-maps edit ' + command)

  def testSimpleEditingWithYAML(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingWithBackendBucketsAndYAML(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testUriNormalization(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        tests:
        - host: youtube.com
          path: /view/this
          service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://www.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendServices/youtube-watch') % {
                                          'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-watch') % {'api': self._api}),
                  ],
              )))],
    )

  def testUriNormalizationWithBackendBuckets(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
          - paths:
            - /images/*
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images-bucket
        tests:
        - host: youtube.com
          path: /view/this
          service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://www.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendServices/youtube-watch') % {
                                          'api': self._api},
                              ),
                              self.messages.PathRule(
                                  paths=['/images/*'],
                                  service=(
                                      'https://www.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/global/'
                                      'backendBuckets/images-bucket') % {
                                          'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-watch') % {'api': self._api}),
                  ],
              )))],
    )

  def testUriNormalizationFullUriRequired(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        defaultService: backendBuckets/my-backend-bucket
        """)])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)
    self.AssertErrContains('[defaultService] must be referenced using URIs',
                           normalize_space=True)

  def testRemovalOfEntireStructuresWithYAML(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: My URL Map

        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
                  description='My URL Map',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingWithJSON(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service')  %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testSimpleEditingBackendBucketsWithJSON(self):
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket",
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            },
            {
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/image-bucket",
              "name": "images"
            }
          ]
        }
        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map'))],

        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') % {
                          'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendServices/'
                              'youtube-service') % {'api': self._api}),
                      self.messages.PathMatcher(
                          name='images',
                          defaultService=(
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendBuckets/'
                              'image-bucket') % {'api': self._api}),
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

    self.RunEdit("""
        my-url-map
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
    )

  def testEditingWithJSONWithSyntaxErrorsAndNoRetry(self):
    self.WriteInput('n\n')  # Answer no when prompted to try again.

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        """)])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.RunEdit("""
          my-url-map --format json
          """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
    )
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
          "defaultService", "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
          "description": "A changed description"
        }
        """ % {'api': self._api})

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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
              "description": "A changed description"
            }
            """ % {'api': self._api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
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

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        *defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.RunEdit("""
          my-url-map --format yaml
          """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
    )
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
        *defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})

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
            defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
            description: A changed description

            """ % {'api': self._api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
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

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})])

    self.make_requests.side_effect = iter([
        [self.url_map],
        exceptions.ToolException('resource not found'),
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.RunEdit("""
          my-url-map --format yaml
          """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api,
          'Get',
          self.messages.ComputeUrlMapsGetRequest(
              project='my-project',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api,
          'Update',
          self.messages.ComputeUrlMapsUpdateRequest(
              project='my-project',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendServices/my-backend-service') %
                  {'api': self._api},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )
    self.AssertErrContains(
        'There was a problem applying your changes: resource not found')

    self.AssertErrContains('Edit aborted by user.')


class URLMapsEditAlphaTest(URLMapsEditTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.urlMaps
    self.url_map = self._CreateUrlMap()
    self.yaml_file_contents = self._CreateYaml()
    self.json_file_contents = self._CreateJson()

  def RunEdit(self, command):
    self.Run('alpha compute url-maps edit --global ' + command)


class URLMapsEditBetaTest(URLMapsEditTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._url_maps_api = self.compute_beta.urlMaps
    self.url_map = self._CreateUrlMap()
    self.yaml_file_contents = self._CreateYaml()
    self.json_file_contents = self._CreateJson()

  def RunEdit(self, command):
    self.Run('beta compute url-maps edit ' + command)


class RegionURLMapsEditTest(URLMapsEditTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._url_maps_api = self.compute_alpha.regionUrlMaps
    self.url_map = self._CreateUrlMap()
    self.yaml_file_contents = self._CreateYaml()
    self.json_file_contents = self._CreateJson()

  def RunEdit(self, command):
    self.Run('alpha compute url-maps edit --region us-west1 ' + command)

  def _CreateUrlMap(self):
    return self.messages.UrlMap(
        defaultService=(
            'https://www.googleapis.com/compute/%(api)s/projects/'
            'my-project/regions/us-west1/backendServices/my-backend-service' % {
                'api': self._api
            }),
        description='My URL Map',
        fingerprint=b'my-fingerprint',
        hostRules=[
            self.messages.HostRule(
                hosts=['google.com', '*.google.com'], pathMatcher='www'),
            self.messages.HostRule(
                hosts=['youtube.com', '*.youtube.com'], pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=(
                    'https://www.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west1/backendServices/www-service' %
                    {
                        'api': self._api
                    })),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    'https://www.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west1/backendServices/'
                    'youtube-service' % {
                        'api': self._api
                    })),
        ],
        name='my-url-map',
        selfLink=(
            'https://www.googleapis.com/compute/%(api)s/projects/my-project/'
            'regions/us-west1/urlMaps/my-url-map' % {
                'api': self._api
            }))

  def _CreateYaml(self):
    return textwrap.dedent("""\
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

        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: My URL Map
        hostRules:
        - hosts:
          - google.com
          - '*.google.com'
          pathMatcher: www
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service
          name: www
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube

        # Example resource:
        # -----------------
        #
        #   defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
        #   hostRules:
        #   - hosts:
        #     - '*.google.com'
        #     - google.com
        #     pathMatcher: www
        #   - hosts:
        #     - '*.youtube.com'
        #     - youtube.com
        #     - '*-youtube.com'
        #     pathMatcher: youtube
        #   name: site-map
        #   pathMatchers:
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
        #     name: www
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
        #     - paths:
        #       - /search/ads
        #       - /search/ads/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #     - paths:
        #       - /images/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #     name: youtube
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
        #     - paths:
        #       - /watch
        #       - /view
        #       - /preview
        #       service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        #   tests:
        #   - host: www.google.com
        #     path: /search/ads/inline?q=flowers
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #   - host: youtube.com
        #     path: /watch/this
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #   - host: youtube.com
        #     path: /images/logo.png
        #     service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #
        # Original resource:
        # ------------------
        #
        #   defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        #   description: My URL Map
        #   fingerprint: bXktZmluZ2VycHJpbnQ=
        #   hostRules:
        #   - hosts:
        #     - google.com
        #     - '*.google.com'
        #     pathMatcher: www
        #   - hosts:
        #     - youtube.com
        #     - '*.youtube.com'
        #     pathMatcher: youtube
        #   name: my-url-map
        #   pathMatchers:
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service
        #     name: www
        #   - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
        #     name: youtube
        #   selfLink: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/urlMaps/my-url-map
        """ % {'api': self._api})

  def _CreateJson(self):
    return textwrap.dedent("""\
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
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
          "description": "My URL Map",
          "hostRules": [
            {
              "hosts": [
                "google.com",
                "*.google.com"
              ],
              "pathMatcher": "www"
            },
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service",
              "name": "www"
            },
            {
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        # Example resource:
        # -----------------
        #
        #   {
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service",
        #     "hostRules": [
        #       {
        #         "hosts": [
        #           "*.google.com",
        #           "google.com"
        #         ],
        #         "pathMatcher": "www"
        #       },
        #       {
        #         "hosts": [
        #           "*.youtube.com",
        #           "youtube.com",
        #           "*-youtube.com"
        #         ],
        #         "pathMatcher": "youtube"
        #       }
        #     ],
        #     "name": "site-map",
        #     "pathMatchers": [
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default",
        #         "name": "www",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search"
        #           },
        #           {
        #             "paths": [
        #               "/search/ads",
        #               "/search/ads/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #           },
        #           {
        #             "paths": [
        #               "/images/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #           }
        #         ]
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default",
        #         "name": "youtube",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search"
        #           },
        #           {
        #             "paths": [
        #               "/watch",
        #               "/view",
        #               "/preview"
        #             ],
        #             "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch"
        #           }
        #         ]
        #       }
        #     ],
        #     "tests": [
        #       {
        #         "host": "www.google.com",
        #         "path": "/search/ads/inline?q=flowers",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/watch/this",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/images/logo.png",
        #         "service": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #       }
        #     ]
        #   }
        #
        # Original resource:
        # ------------------
        #
        #   {
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/urlMaps/my-url-map"
        #   }
        """ % {'api': self._api})

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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube

        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', urlMap='my-url-map', region='us-west1'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api}),
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        description: A changed description
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube

        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api}),
                  ],
                  name='my-url-map',
              )))],
    )

  def testUriNormalization(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        ---
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-watch
        tests:
        - host: youtube.com
          path: /view/this
          service: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-watch
        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://www.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/regions/'
                                      'us-west1/backendServices/youtube-watch')
                                  % {'api': self._api},
                              ),
                          ],
                      ),
                  ],
                  name='my-url-map',
                  tests=[
                      self.messages.UrlMapTest(
                          host='youtube.com',
                          path='/view/this',
                          service=('https://www.googleapis.com/compute/%(api)s/'
                                   'projects/my-project/regions/us-west1/'
                                   'backendServices/youtube-watch') %
                          {'api': self._api}),
                  ],
              )))],
    )

  def testUriNormalizationWithBackendBuckets(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        ---
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket
        hostRules:
        - hosts:
          - youtube.com
          - '*.youtube.com'
          pathMatcher: youtube
        pathMatchers:
        - defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube
          pathRules:
          - paths:
            - /view
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-watch
          - paths:
            - /images/*
            service: https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images-bucket
        tests:
        - host: youtube.com
          path: /view/this
          service: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-watch
        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api},
                          pathRules=[
                              self.messages.PathRule(
                                  paths=['/view'],
                                  service=(
                                      'https://www.googleapis.com/compute/'
                                      '%(api)s/projects/my-project/regions/'
                                      'us-west1/backendServices/youtube-watch')
                                  % {'api': self._api},
                              ),
                              self.messages.PathRule(
                                  paths=['/images/*'],
                                  service=('https://www.googleapis.com/compute/'
                                           '%(api)s/projects/my-project/global/'
                                           'backendBuckets/images-bucket') %
                                  {'api': self._api},
                              ),
                          ],
                      ),
                  ],
                  name='my-url-map',
                  tests=[
                      self.messages.UrlMapTest(
                          host='youtube.com',
                          path='/view/this',
                          service=('https://www.googleapis.com/compute/%(api)s/'
                                   'projects/my-project/regions/us-west1/'
                                   'backendServices/youtube-watch') %
                          {'api': self._api}),
                  ],
              )))],
    )

  def testUriNormalizationFullUriRequired(self):
    self.mock_edit.side_effect = iter([
        textwrap.dedent("""\
        ---
        defaultService: backendBuckets/my-backend-bucket
        """)
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: My URL Map

        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api}),
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
        #     "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
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
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service",
        #         "name": "www"
        #       },
        #       {
        #         "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
        #         "name": "youtube"
        #       }
        #     ],
        #     "selfLink": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map"
        #   }

        {
          "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/my-backend-bucket",
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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service",
              "name": "youtube"
            },
            {
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/image-bucket",
              "name": "images"
            }
          ]
        }
        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project', region='us-west1', urlMap='my-url-map'))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/global/backendBuckets/my-backend-bucket') %
                  {'api': self._api},
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
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/regions/us-west1/'
                              'backendServices/youtube-service') %
                          {'api': self._api}),
                      self.messages.PathMatcher(
                          name='images',
                          defaultService=(
                              'https://www.googleapis.com/compute/%(api)s/'
                              'projects/my-project/global/backendBuckets/'
                              'image-bucket') % {'api': self._api}),
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

    self.RunEdit("""
        my-url-map
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             project='my-project',
                             region='us-west1',
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
      self.RunEdit("""
          my-url-map --format json
          """)

    self.AssertFileOpenedWith(self.json_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             project='my-project',
                             urlMap='my-url-map',
                             region='us-west1',
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
          "defaultService", "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
          "description": "A changed description"
        }
        """ % {'api': self._api})

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
              "defaultService": "https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service",
              "description": "A changed description"
            }
            """ % {'api': self._api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format json
        """)

    self.AssertFileOpenedWith(self.json_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
        *defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.RunEdit("""
          my-url-map --format yaml
          """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests([(self._url_maps_api, 'Get',
                         self.messages.ComputeRegionUrlMapsGetRequest(
                             project='my-project',
                             region='us-west1',
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
        *defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})

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
            defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
            description: A changed description

            """ % {'api': self._api}),
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        [],
    ])

    self.RunEdit("""
        my-url-map --format yaml
        """)

    self.AssertFileOpenedWith(self.yaml_file_contents, bad_modifications)

    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
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
        defaultService: https://www.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
        description: A changed description

        """ % {'api': self._api})
    ])

    self.make_requests.side_effect = iter([
        [self.url_map],
        exceptions.ToolException('resource not found'),
    ])

    with self.AssertRaisesToolExceptionRegexp('Edit aborted by user.'):
      self.RunEdit("""
          my-url-map --format yaml
          """)

    self.AssertFileOpenedWith(self.yaml_file_contents)
    self.CheckRequests(
        [(self._url_maps_api, 'Get',
          self.messages.ComputeRegionUrlMapsGetRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
          ))],
        [(self._url_maps_api, 'Update',
          self.messages.ComputeRegionUrlMapsUpdateRequest(
              project='my-project',
              region='us-west1',
              urlMap='my-url-map',
              urlMapResource=self.messages.UrlMap(
                  defaultService=(
                      'https://www.googleapis.com/compute/%(api)s/projects/'
                      'my-project/regions/us-west1/backendServices/'
                      'my-backend-service') % {'api': self._api},
                  description='A changed description',
                  fingerprint=b'my-fingerprint',
                  name='my-url-map',
              )))],
    )
    self.AssertErrContains(
        'There was a problem applying your changes: resource not found')

    self.AssertErrContains('Edit aborted by user.')


if __name__ == '__main__':
  test_case.main()
