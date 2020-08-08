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
"""Resources that are shared by two or more url-maps tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'

_BACKEND_BUCKETS_URI_PREFIX = _V1_URI_PREFIX + 'global/backendBuckets/'
_BACKEND_BUCKETS_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'global/backendBuckets/')
_BACKEND_BUCKETS_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'global/backendBuckets/')

_BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'
_BACKEND_SERVICES_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'global/backendServices/')
_BACKEND_SERVICES_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'global/backendServices/')

_REGION_BACKEND_SERVICES_URI_PREFIX = (
    _V1_URI_PREFIX + 'regions/us-west-1/backendServices/')
_REGION_BACKEND_SERVICES_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'regions/us-west-1/backendServices/')
_REGION_BACKEND_SERVICES_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'regions/us-west-1/backendServices/')

_URL_MAPS_URI_PREFIX = _V1_URI_PREFIX + 'global/urlMaps/'
_URL_MAPS_ALPHA_URI_PREFIX = _ALPHA_URI_PREFIX + 'global/urlMaps/'
_URL_MAPS_BETA_URI_PREFIX = (_BETA_URI_PREFIX + 'global/urlMaps/')

_REGION_URL_MAPS_URI_PREFIX = _V1_URI_PREFIX + 'regions/us-west-1/urlMaps/'
_REGION_URL_MAPS_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'regions/us-west-1/urlMaps/')
_REGION_URL_MAPS_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'regions/us-west-1/urlMaps/')


def MakeUrlMaps(msgs, api, regional):
  """Create url map resources."""
  (backend_services_prefix, backend_buckets_prefix, url_maps_prefix) = {
      ('alpha', False):
          (_BACKEND_SERVICES_ALPHA_URI_PREFIX,
           _BACKEND_BUCKETS_ALPHA_URI_PREFIX, _URL_MAPS_ALPHA_URI_PREFIX),
      ('alpha', True): (_REGION_BACKEND_SERVICES_ALPHA_URI_PREFIX,
                        _BACKEND_BUCKETS_ALPHA_URI_PREFIX,
                        _REGION_URL_MAPS_ALPHA_URI_PREFIX),
      ('beta', False):
          (_BACKEND_SERVICES_BETA_URI_PREFIX, _BACKEND_BUCKETS_BETA_URI_PREFIX,
           _URL_MAPS_BETA_URI_PREFIX),
      ('beta', True):
          (_REGION_BACKEND_SERVICES_BETA_URI_PREFIX,
           _BACKEND_BUCKETS_BETA_URI_PREFIX, _REGION_URL_MAPS_BETA_URI_PREFIX),
      ('v1', False): (_BACKEND_SERVICES_URI_PREFIX, _BACKEND_BUCKETS_URI_PREFIX,
                      _URL_MAPS_URI_PREFIX),
      ('v1', True): (_REGION_BACKEND_SERVICES_URI_PREFIX,
                     _BACKEND_BUCKETS_URI_PREFIX, _REGION_URL_MAPS_URI_PREFIX)
  }[(api, regional)]

  url_maps = [
      msgs.UrlMap(
          name='url-map-1',
          defaultService=backend_services_prefix + 'default-service',
          hostRules=[
              messages.HostRule(
                  hosts=['*.google.com', 'google.com'], pathMatcher='www'),
              messages.HostRule(
                  hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                  pathMatcher='youtube'),
          ],
          pathMatchers=[
              messages.PathMatcher(
                  name='www',
                  defaultService=(backend_services_prefix + 'www-default'),
                  pathRules=[
                      messages.PathRule(
                          paths=['/search', '/search/*'],
                          service=backend_services_prefix + 'search'),
                      messages.PathRule(
                          paths=['/search/ads', '/search/ads/*'],
                          service=backend_services_prefix + 'ads'),
                      messages.PathRule(
                          paths=['/images'],
                          service=backend_services_prefix + 'images'),
                  ]),
              messages.PathMatcher(
                  name='youtube',
                  defaultService=(backend_services_prefix + 'youtube-default'),
                  pathRules=[
                      messages.PathRule(
                          paths=['/search', '/search/*'],
                          service=(backend_services_prefix + 'youtube-search')),
                      messages.PathRule(
                          paths=['/watch', '/view', '/preview'],
                          service=(backend_services_prefix + 'youtube-watch')),
                  ]),
          ],
          selfLink=(url_maps_prefix + 'url-map-1'),
          tests=[
              messages.UrlMapTest(
                  host='www.google.com',
                  path='/search/ads/inline?q=flowers',
                  service=backend_services_prefix + 'ads'),
              messages.UrlMapTest(
                  host='youtube.com',
                  path='/watch/this',
                  service=backend_services_prefix + 'youtube-default'),
          ]),
      messages.UrlMap(
          name='url-map-2',
          defaultService=backend_services_prefix + 'default-service',
          hostRules=[
              messages.HostRule(
                  hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                  pathMatcher='youtube'),
          ],
          pathMatchers=[
              messages.PathMatcher(
                  name='youtube',
                  defaultService=(backend_services_prefix + 'youtube-default'),
                  pathRules=[
                      messages.PathRule(
                          paths=['/search', '/search/*'],
                          service=(backend_services_prefix + 'youtube-search')),
                      messages.PathRule(
                          paths=['/watch', '/view', '/preview'],
                          service=(backend_services_prefix + 'youtube-watch')),
                  ]),
          ],
          selfLink=(url_maps_prefix + 'url-map-2'),
          tests=[
              messages.UrlMapTest(
                  host='youtube.com',
                  path='/watch/this',
                  service=backend_services_prefix + 'youtube-default'),
          ]),
      messages.UrlMap(
          name='url-map-3',
          defaultService=backend_services_prefix + 'default-service',
          selfLink=(url_maps_prefix + 'url-map-3')),
      messages.UrlMap(
          name='url-map-4',
          defaultService=backend_buckets_prefix + 'default-bucket',
          selfLink=(url_maps_prefix + 'url-map-4')),
  ]

  return url_maps


URL_MAPS_ALPHA = MakeUrlMaps(messages, 'alpha', regional=False)
URL_MAPS_BETA = MakeUrlMaps(messages, 'beta', regional=False)
URL_MAPS = MakeUrlMaps(messages, 'v1', regional=False)
REGION_URL_MAPS_ALPHA = MakeUrlMaps(messages, 'alpha', regional=True)
REGION_URL_MAPS_BETA = MakeUrlMaps(messages, 'beta', regional=True)
REGION_URL_MAPS = MakeUrlMaps(messages, 'v1', regional=True)
