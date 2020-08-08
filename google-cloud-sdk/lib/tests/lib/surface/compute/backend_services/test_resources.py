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
"""Resources that are shared by two or more backend services tests."""

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

_BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'


def MakeBackendServices(msgs, api):
  """Create backend services resources."""
  prefix = _COMPUTE_PATH + '/' + api
  services = [
      msgs.BackendService(
          backends=[],
          description='my backend service',
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='backend-service-1',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-1'),
          timeoutSec=30),
      msgs.BackendService(
          backends=[
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.RATE),
                  description='group one',
                  group=('https://compute.googleapis.com/compute/'
                         '{0}/projects/my-project/zones/zone-1/'
                         'instanceGroups/group-1'.format(api)),
                  maxRate=100),
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.UTILIZATION),
                  description='group two',
                  group=('https://compute.googleapis.com/compute/{0}/'
                         'projects/my-project/zones/zone-2/'
                         'instanceGroups/group-2'.format(api)),
                  maxUtilization=1.0),
          ],
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='backend-service-2',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-2'),
          timeoutSec=30),
      msgs.BackendService(
          backends=[
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.RATE),
                  description='instance group one',
                  group=('https://compute.googleapis.com/compute/'
                         '{0}/projects/my-project/zones/'
                         'zone-1/instanceGroups/group-1').format(api),
                  maxRate=100),
          ],
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='instance-group-service',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/instance-group-service'),
          timeoutSec=30),
      msgs.BackendService(
          backends=[
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.RATE),
                  description='group one',
                  group=('https://compute.googleapis.com/compute/'
                         '{0}/projects/my-project/regions/region-1/'
                         'instanceGroups/group-1'.format(api)),
                  maxRate=100),
          ],
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='regional-instance-group-service',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/regional-instance-group-service'),
          timeoutSec=30),
      msgs.BackendService(
          backends=[
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.CONNECTION),
                  description='max connections',
                  group=('https://compute.googleapis.com/compute/'
                         '{0}/projects/my-project/zones/zone-1/'
                         'instanceGroups/group-1'.format(api)),
                  maxConnectionsPerInstance=100),
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.UTILIZATION),
                  description='utilziation with conneciton',
                  group=('https://compute.googleapis.com/compute/'
                         '{0}/projects/my-project/zones/zone-2/'
                         'instanceGroups/group-2'.format(api)),
                  maxUtilization=1.0,
                  maxConnections=10),
          ],
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/healthChecks/my-health-check'.format(api))
          ],
          name='backend-service-tcp',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-tcp'),
          timeoutSec=30)
  ]

  return services


def MakeBackendServiceWithOutlierDetection(msgs, api):
  """Create backend services resource configured with outlier detection."""
  prefix = _COMPUTE_PATH + '/' + api
  return msgs.BackendService(
      backends=[],
      description='my backend service',
      healthChecks=[
          ('https://compute.googleapis.com/compute/{0}/projects/'
           'my-project/global/httpHealthChecks/my-health-check'.format(api))
      ],
      name='backend-service-1',
      portName='http',
      protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
      selfLink=(prefix + '/projects/my-project'
                '/global/backendServices/backend-service-1'),
      timeoutSec=30,
      outlierDetection=msgs.OutlierDetection(
          interval=msgs.Duration(seconds=1500)))


BACKEND_SERVICES_ALPHA = MakeBackendServices(alpha_messages, 'alpha')
BACKEND_SERVICES_BETA = MakeBackendServices(beta_messages, 'beta')
BACKEND_SERVICES_V1 = MakeBackendServices(messages, 'v1')


def MakeBackendServicesWithLegacyHealthCheck(msgs, api, protocol):
  if protocol == 'HTTP':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTP
  elif protocol == 'HTTPS':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTPS

  proj_url = _COMPUTE_PATH + '/{api}/projects/my-project'.format(api=api)
  return [
      msgs.BackendService(
          backends=[],
          description='my backend service',
          healthChecks=[
              (proj_url + '/global/httpHealthChecks/http-health-check'),
              (proj_url + '/global/httpsHealthChecks/https-health-check')
          ],
          name='backend-service-1',
          portName='https',
          protocol=protocol_enum,
          selfLink=proj_url + '/global/backendServices/backend-service-1',
          timeoutSec=30)
  ]


HTTP_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1 = (
    MakeBackendServicesWithLegacyHealthCheck(messages, 'v1', 'HTTP'))
HTTPS_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1 = (
    MakeBackendServicesWithLegacyHealthCheck(messages, 'v1', 'HTTPS'))


def MakeBackendServicesWithHealthCheck(msgs, api, protocol):
  """Make a backend service with health checks."""

  if protocol == 'GRPC':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.GRPC
  elif protocol == 'HTTP':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTP
  elif protocol == 'HTTPS':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTPS
  elif protocol == 'HTTP2':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTP2
  elif protocol == 'TCP':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.TCP
  elif protocol == 'SSL':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.SSL

  proj_url = _COMPUTE_PATH + '/{api}/projects/my-project'.format(api=api)
  return [
      msgs.BackendService(
          backends=[],
          healthChecks=[
              (proj_url + '/global/healthChecks/orig-health-check'),
          ],
          name='backend-service-3',
          portName='http',
          protocol=protocol_enum,
          selfLink=proj_url + '/global/backendServices/backend-service-3',
          timeoutSec=30)
  ]


HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA = (
    MakeBackendServicesWithHealthCheck(alpha_messages, 'alpha', 'HTTP'))

HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA = (
    MakeBackendServicesWithHealthCheck(alpha_messages, 'alpha', 'HTTPS'))

TCP_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA = (
    MakeBackendServicesWithHealthCheck(alpha_messages, 'alpha', 'TCP'))

SSL_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA = (
    MakeBackendServicesWithHealthCheck(alpha_messages, 'alpha', 'SSL'))

HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_BETA = (
    MakeBackendServicesWithHealthCheck(beta_messages, 'beta', 'HTTP'))

HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_BETA = (
    MakeBackendServicesWithHealthCheck(beta_messages, 'beta', 'HTTPS'))

HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1 = (
    MakeBackendServicesWithHealthCheck(messages, 'v1', 'HTTP'))

HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1 = (
    MakeBackendServicesWithHealthCheck(messages, 'v1', 'HTTPS'))


def MakeBackendServicesWithGenCookieSessionAffinity(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.BackendService(
          backends=[],
          description='my backend service',
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='backend-service-1',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-1'),
          sessionAffinity=(msgs.BackendService.SessionAffinityValueValuesEnum
                           .GENERATED_COOKIE),
          affinityCookieTtlSec=18,
          timeoutSec=30),
  ]


BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_ALPHA = (
    MakeBackendServicesWithGenCookieSessionAffinity(alpha_messages, 'alpha'))

BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_BETA = (
    MakeBackendServicesWithGenCookieSessionAffinity(beta_messages, 'beta'))

BACKEND_SERVICES_WITH_GEN_COOKIE_SESSION_AFFINITY_V1 = (
    MakeBackendServicesWithGenCookieSessionAffinity(messages, 'v1'))


def MakeBackendServicesWithConnectionDrainingTimeout(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.BackendService(
          backends=[],
          description='my backend service',
          healthChecks=[
              ('https://compute.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='backend-service-1',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-1'),
          connectionDraining=msgs.ConnectionDraining(drainingTimeoutSec=120)),
  ]


BACKEND_SERVICES_WITH_CONNECTION_DRAINING_TIMEOUT_ALPHA = (
    MakeBackendServicesWithConnectionDrainingTimeout(alpha_messages, 'alpha'))

BACKEND_SERVICES_WITH_CONNECTION_DRAINING_TIMEOUT = (
    MakeBackendServicesWithConnectionDrainingTimeout(messages, 'v1'))


# MakeBackendServicesWithCustomCacheKey does not validate the input.
def MakeBackendServicesWithCustomCacheKey(msgs,
                                          api,
                                          include_host=True,
                                          include_protocol=True,
                                          include_query_string=True,
                                          whitelist=None,
                                          blacklist=None):
  """Creates backend service with custom cache key."""
  if whitelist is None:
    whitelist = []
  if blacklist is None:
    blacklist = []
  prefix = _COMPUTE_PATH + '/' + api
  return (msgs.BackendService(
      backends=[],
      description='my backend service',
      healthChecks=[
          ('https://compute.googleapis.com/compute/{0}/projects/'
           'my-project/global/httpHealthChecks/my-health-check'.format(api))
      ],
      name='backend-service-1',
      portName='http',
      protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
      selfLink=(prefix + '/projects/my-project'
                '/global/backendServices/backend-service-1'),
      cdnPolicy=msgs.BackendServiceCdnPolicy(
          cacheKeyPolicy=msgs.CacheKeyPolicy(
              includeHost=include_host,
              includeProtocol=include_protocol,
              includeQueryString=include_query_string,
              queryStringWhitelist=whitelist,
              queryStringBlacklist=blacklist))))


BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_ALPHA = (
    MakeBackendServicesWithCustomCacheKey(alpha_messages, 'alpha'))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_EXCLUDE_ALL_ALPHA = (
    MakeBackendServicesWithCustomCacheKey(
        alpha_messages,
        'alpha',
        include_host=False,
        include_protocol=False,
        include_query_string=False))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_WHITELIST_ALPHA = (
    MakeBackendServicesWithCustomCacheKey(
        alpha_messages, 'alpha', whitelist=['contentid', 'language']))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_BLACKLIST_ALPHA = (
    MakeBackendServicesWithCustomCacheKey(
        alpha_messages, 'alpha', blacklist=['contentid', 'language']))

BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_BETA = (
    MakeBackendServicesWithCustomCacheKey(beta_messages, 'beta'))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_EXCLUDE_ALL_BETA = (
    MakeBackendServicesWithCustomCacheKey(
        beta_messages,
        'beta',
        include_host=False,
        include_protocol=False,
        include_query_string=False))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_WHITELIST_BETA = (
    MakeBackendServicesWithCustomCacheKey(
        beta_messages, 'beta', whitelist=['contentid', 'language']))
BACKEND_SERVICES_WITH_CUSTOM_CACHE_KEY_BLACKLIST_BETA = (
    MakeBackendServicesWithCustomCacheKey(
        beta_messages, 'beta', blacklist=['contentid', 'language']))
