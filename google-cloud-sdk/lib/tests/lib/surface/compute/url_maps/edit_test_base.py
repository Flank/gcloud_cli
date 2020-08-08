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
"""Test base for the url-maps edit subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib.surface.compute import test_base


class EditTestBase(test_base.BaseEditTest):
  """Test base for url-maps edit command."""

  def SetUp(self):
    self.SelectApi(self.api_version)
    self._url_maps_api = self.compute.urlMaps
    self._regional_url_maps_api = self.compute.regionUrlMaps
    self.url_map = self._CreateUrlMap()
    self.regional_url_map = self._CreateRegionalUrlMap()
    self.yaml_file_contents = self._CreateYaml()
    self.regional_yaml_file_contents = self._CreateRegionalYaml()
    self.json_file_contents = self._CreateJson()

  def _CreateUrlMap(self):
    return self.messages.UrlMap(
        defaultService=(
            'https://compute.googleapis.com/compute/%(api)s/projects/'
            'my-project/global/backendServices/my-backend-service' % {
                'api': self.api_version
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
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/global/backendServices/www-service' % {
                        'api': self.api_version
                    })),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/global/backendServices/youtube-service' % {
                        'api': self.api_version
                    })),
        ],
        name='my-url-map',
        selfLink=(
            'https://compute.googleapis.com/compute/%(api)s/projects/my-project/'
            'global/urlMaps/my-url-map' % {
                'api': self.api_version
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

        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
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
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service
          name: www
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
          name: youtube

        # Example resource:
        # -----------------
        #
        #   defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
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
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
        #     name: www
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
        #     - paths:
        #       - /search/ads
        #       - /search/ads/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #     - paths:
        #       - /images/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #     name: youtube
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
        #     - paths:
        #       - /watch
        #       - /view
        #       - /preview
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        #   tests:
        #   - host: www.google.com
        #     path: /search/ads/inline?q=flowers
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #   - host: youtube.com
        #     path: /watch/this
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #   - host: youtube.com
        #     path: /images/logo.png
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #
        # Original resource:
        # ------------------
        #
        #   defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service
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
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service
        #     name: www
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service
        #     name: youtube
        #   selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/urlMaps/my-url-map
        """ % {'api': self.api_version})

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
          "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/my-backend-service",
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
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-service",
              "name": "www"
            },
            {
              "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-service",
              "name": "youtube"
            }
          ]
        }
        # Example resource:
        # -----------------
        #
        #   {
        #     "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service",
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
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default",
        #         "name": "www",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search"
        #           },
        #           {
        #             "paths": [
        #               "/search/ads",
        #               "/search/ads/*"
        #             ],
        #             "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #           },
        #           {
        #             "paths": [
        #               "/images/*"
        #             ],
        #             "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #           }
        #         ]
        #       },
        #       {
        #         "defaultService": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default",
        #         "name": "youtube",
        #         "pathRules": [
        #           {
        #             "paths": [
        #               "/search",
        #               "/search/*"
        #             ],
        #             "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search"
        #           },
        #           {
        #             "paths": [
        #               "/watch",
        #               "/view",
        #               "/preview"
        #             ],
        #             "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch"
        #           }
        #         ]
        #       }
        #     ],
        #     "tests": [
        #       {
        #         "host": "www.google.com",
        #         "path": "/search/ads/inline?q=flowers",
        #         "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/watch/this",
        #         "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default"
        #       },
        #       {
        #         "host": "youtube.com",
        #         "path": "/images/logo.png",
        #         "service": "https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images"
        #       }
        #     ]
        #   }
        #
        # Original resource:
        # ------------------
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
        """ % {'api': self.api_version})

  def _CreateRegionalUrlMap(self):
    return self.messages.UrlMap(
        defaultService=(
            'https://compute.googleapis.com/compute/%(api)s/projects/'
            'my-project/regions/us-west1/backendServices/my-backend-service' % {
                'api': self.api_version
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
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west1/backendServices/www-service' %
                    {
                        'api': self.api_version
                    })),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=(
                    'https://compute.googleapis.com/compute/%(api)s/projects/'
                    'my-project/regions/us-west1/backendServices/'
                    'youtube-service' % {
                        'api': self.api_version
                    })),
        ],
        name='my-url-map',
        selfLink=(
            'https://compute.googleapis.com/compute/%(api)s/projects/my-project/'
            'regions/us-west1/urlMaps/my-url-map' % {
                'api': self.api_version
            }))

  def _CreateRegionalYaml(self):
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

        defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
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
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service
          name: www
        - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
          name: youtube

        # Example resource:
        # -----------------
        #
        #   defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/default-service
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
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/www-default
        #     name: www
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/search
        #     - paths:
        #       - /search/ads
        #       - /search/ads/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #     - paths:
        #       - /images/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #     name: youtube
        #     pathRules:
        #     - paths:
        #       - /search
        #       - /search/*
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-search
        #     - paths:
        #       - /watch
        #       - /view
        #       - /preview
        #       service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-watch
        #   tests:
        #   - host: www.google.com
        #     path: /search/ads/inline?q=flowers
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/ads
        #   - host: youtube.com
        #     path: /watch/this
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/youtube-default
        #   - host: youtube.com
        #     path: /images/logo.png
        #     service: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendBuckets/images
        #
        # Original resource:
        # ------------------
        #
        #   defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/my-backend-service
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
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/www-service
        #     name: www
        #   - defaultService: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/backendServices/youtube-service
        #     name: youtube
        #   selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/regions/us-west1/urlMaps/my-url-map
        """ % {'api': self.api_version})
