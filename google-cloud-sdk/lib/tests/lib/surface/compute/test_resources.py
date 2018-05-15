# -*- coding: utf-8 -*-
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
"""Resources that are shared by two or more tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://www.googleapis.com/compute'

_V1_URI_PREFIX = _COMPUTE_PATH + '/v1/projects/my-project/'
_ALPHA_URI_PREFIX = _COMPUTE_PATH + '/alpha/projects/my-project/'
_BETA_URI_PREFIX = _COMPUTE_PATH + '/beta/projects/my-project/'

_BACKEND_SERVICES_URI_PREFIX = _V1_URI_PREFIX + 'global/backendServices/'
_BACKEND_SERVICES_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'global/backendServices/')
_BACKEND_SERVICES_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'global/backendServices/')

_BACKEND_BUCKETS_URI_PREFIX = _V1_URI_PREFIX + 'global/backendBuckets/'
_BACKEND_BUCKETS_ALPHA_URI_PREFIX = (
    _ALPHA_URI_PREFIX + 'global/backendBuckets/')
_BACKEND_BUCKETS_BETA_URI_PREFIX = (
    _BETA_URI_PREFIX + 'global/backendBuckets/')

_URL_MAPS_URI_PREFIX = _V1_URI_PREFIX + 'global/urlMaps/'
_URL_MAPS_ALPHA_URI_PREFIX = (_ALPHA_URI_PREFIX + 'global/urlMaps/')
_URL_MAPS_BETA_URI_PREFIX = (_BETA_URI_PREFIX + 'global/urlMaps/')


# TODO(b/35952682): Convert all the fixtures here to use this common method.
def _GetMessagesForApi(api):
  if api == 'alpha':
    return alpha_messages
  elif api == 'beta':
    return beta_messages
  elif api == 'v1':
    return messages
  else:
    assert False


ADDRESSES = [
    messages.Address(
        address='23.251.134.124',
        name='address-1',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1/addresses/address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),

    messages.Address(
        address='23.251.134.125',
        name='address-2',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1/addresses/address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]


def MakeAutoscalers(api, scope_name='zone-1', scope_type='zone'):
  """Makes Autoscaler test resources."""
  used_messages = _GetMessagesForApi(api)
  autoscalers = [
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(
              coolDownPeriodSec=60,
              cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
                  utilizationTarget=0.8,
              ),
              customMetricUtilizations=[
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/seconds',
                      utilizationTarget=60.,
                      utilizationTargetType=(
                          used_messages.
                          AutoscalingPolicyCustomMetricUtilization.
                          UtilizationTargetTypeValueValuesEnum.
                          DELTA_PER_MINUTE),
                  ),
              ],
              loadBalancingUtilization=(
                  used_messages.AutoscalingPolicyLoadBalancingUtilization)(
                      utilizationTarget=0.9,
                  ),
              maxNumReplicas=10,
              minNumReplicas=2,
          ),
          name='autoscaler-1',
          target=('https://www.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-1'
                  .format(api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-1'
                    .format(api, scope_type + 's', scope_name)),
      ),
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(
              maxNumReplicas=10,
          ),
          name='autoscaler-2',
          target=('https://www.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-2'
                  .format(api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-2'
                    .format(api, scope_type + 's', scope_name)),
      ),
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(
              customMetricUtilizations=[
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/seconds',
                      utilizationTarget=60.,
                      utilizationTargetType=(
                          used_messages.
                          AutoscalingPolicyCustomMetricUtilization.
                          UtilizationTargetTypeValueValuesEnum.
                          DELTA_PER_MINUTE),
                  ),
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/my-metric',
                      utilizationTarget=30568.,
                      utilizationTargetType=(
                          used_messages.
                          AutoscalingPolicyCustomMetricUtilization.
                          UtilizationTargetTypeValueValuesEnum.
                          DELTA_PER_MINUTE),
                  ),
              ],
              maxNumReplicas=10,
              minNumReplicas=2,
          ),
          name='autoscaler-3',
          target=('https://www.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-3'
                  .format(api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-3'
                    .format(api, scope_type + 's', scope_name)),
      ),
  ]
  for autoscaler in autoscalers:
    setattr(autoscaler, scope_type,
            'https://www.googleapis.com/compute/{0}/'
            'projects/my-project/{1}/{2}'
            .format(api, scope_type + 's', scope_name))
  return autoscalers


def MakeAutoscalerOk(api, scope_name='zone-1', scope_type='zone'):
  """Create autoscaler resource with OK status."""

  used_messages = _GetMessagesForApi(api)
  autoscaler = used_messages.Autoscaler(
      autoscalingPolicy=used_messages.AutoscalingPolicy(
          coolDownPeriodSec=60,
          cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
              utilizationTarget=0.8,
          ),
          maxNumReplicas=10,
          minNumReplicas=2,
      ),
      name='autoscaler-1',
      target=('https://www.googleapis.com/compute/{0}/projects/'
              'my-project/{1}/{2}/instanceGroupManagers/group-1'
              .format(api, scope_type + 's', scope_name)),
      creationTimestamp='Two days ago',
      status=used_messages.Autoscaler.StatusValueValuesEnum.ACTIVE,
      id=2,
      selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                'my-project/{1}/{2}/autoscalers/autoscaler-1'
                .format(api, scope_type + 's', scope_name)),
  )
  setattr(autoscaler, scope_type,
          'https://www.googleapis.com/compute/{0}/projects/my-project/{1}/{2}'
          .format(api, scope_type + 's', scope_name))
  return autoscaler


def MakeAutoscalerWithError(api):
  used_messages = _GetMessagesForApi(api)
  return used_messages.Autoscaler(
      autoscalingPolicy=used_messages.AutoscalingPolicy(
          coolDownPeriodSec=60,
          cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
              utilizationTarget=0.8,
          ),
          maxNumReplicas=10,
          minNumReplicas=2,
      ),
      name='autoscaler-2',
      target=('https://www.googleapis.com/compute/{0}/projects/'
              'my-project/zones/zone-1/instanceGroupManagers/group-2'
              .format(api)),
      zone=('https://www.googleapis.com/compute/{0}/'
            'projects/my-project/zones/zone-1'.format(api)),
      creationTimestamp='Two days ago',
      status=used_messages.Autoscaler.StatusValueValuesEnum.ERROR,
      id=2,
      selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                'my-project/zones/zone-1/autoscalers/autoscaler-2'
                .format(api)),
  )


GLOBAL_ADDRESSES = [
    messages.Address(
        address='23.251.134.126',
        name='global-address-1',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/addresses/global-address-1'),
        status=messages.Address.StatusValueValuesEnum.IN_USE),

    messages.Address(
        address='23.251.134.127',
        name='global-address-2',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/addresses/global-address-2'),
        status=messages.Address.StatusValueValuesEnum.RESERVED),
]


def MakeBackendBuckets(msgs, api):
  """Create backend bucket resources."""
  prefix = _COMPUTE_PATH + '/' + api
  buckets = [
      msgs.BackendBucket(
          bucketName='gcs-bucket-1',
          description='my backend bucket',
          enableCdn=False,
          name='backend-bucket-1-enable-cdn-false',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-1-enable-cdn-false')),
      msgs.BackendBucket(
          bucketName='gcs-bucket-2',
          description='my other backend bucket',
          enableCdn=True,
          name='backend-bucket-2-enable-cdn-true',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-2-enable-cdn-true')),
      msgs.BackendBucket(
          bucketName='gcs-bucket-3',
          description='third backend bucket',
          name='backend-bucket-3-enable-cdn-false',
          selfLink=(prefix + '/projects/my-project/global/'
                    'backendBuckets/backend-bucket-3-enable-cdn-false'))
  ]

  return buckets

BACKEND_BUCKETS_ALPHA = MakeBackendBuckets(alpha_messages, 'alpha')
BACKEND_BUCKETS_BETA = MakeBackendBuckets(beta_messages, 'beta')
BACKEND_BUCKETS = MakeBackendBuckets(messages, 'v1')


def MakeBackendServices(msgs, api):
  """Create backend services resources."""
  prefix = _COMPUTE_PATH + '/' + api
  services = [
      msgs.BackendService(
          backends=[],
          description='my backend service',
          healthChecks=[
              ('https://www.googleapis.com/compute/{0}/projects/'
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
                  group=(
                      'https://www.googleapis.com/compute/'
                      '{0}/projects/my-project/zones/zone-1/'
                      'instanceGroups/group-1'.format(api)),
                  maxRate=100),
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.UTILIZATION),
                  description='group two',
                  group=(
                      'https://www.googleapis.com/compute/{0}/'
                      'projects/my-project/zones/zone-2/'
                      'instanceGroups/group-2'.format(api)),
                  maxUtilization=1.0),
          ],
          healthChecks=[
              ('https://www.googleapis.com/compute/{0}/projects/'
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
                  group=(
                      'https://www.googleapis.com/compute/'
                      '{0}/projects/my-project/zones/'
                      'zone-1/instanceGroups/group-1').format(api),
                  maxRate=100),
          ],
          healthChecks=[
              ('https://www.googleapis.com/compute/{0}/projects/'
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
                  group=(
                      'https://www.googleapis.com/compute/'
                      '{0}/projects/my-project/regions/region-1/'
                      'instanceGroups/group-1'.format(api)),
                  maxRate=100),
          ],
          healthChecks=[
              ('https://www.googleapis.com/compute/{0}/projects/'
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
                  group=(
                      'https://www.googleapis.com/compute/'
                      '{0}/projects/my-project/zones/zone-1/'
                      'instanceGroups/group-1'.format(api)),
                  maxConnectionsPerInstance=100),
              msgs.Backend(
                  balancingMode=(
                      msgs.Backend.BalancingModeValueValuesEnum.UTILIZATION),
                  description='utilziation with conneciton',
                  group=(
                      'https://www.googleapis.com/compute/'
                      '{0}/projects/my-project/zones/zone-2/'
                      'instanceGroups/group-2'.format(api)),
                  maxUtilization=1.0,
                  maxConnections=10),
          ],
          healthChecks=[
              ('https://www.googleapis.com/compute/{0}/projects/'
               'my-project/global/healthChecks/my-health-check'.format(api))
          ],
          name='backend-service-tcp',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.TCP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-tcp'),
          timeoutSec=30),
  ]

  return services

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

  if protocol == 'HTTP':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTP
  elif protocol == 'HTTPS':
    protocol_enum = msgs.BackendService.ProtocolValueValuesEnum.HTTPS
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
              ('https://www.googleapis.com/compute/{0}/projects/'
               'my-project/global/httpHealthChecks/my-health-check'.format(api))
          ],
          name='backend-service-1',
          portName='http',
          protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
          selfLink=(prefix + '/projects/my-project'
                    '/global/backendServices/backend-service-1'),
          sessionAffinity=
          (msgs.BackendService.SessionAffinityValueValuesEnum.GENERATED_COOKIE),
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
              ('https://www.googleapis.com/compute/{0}/projects/'
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
  if whitelist is None:
    whitelist = []
  if blacklist is None:
    blacklist = []
  prefix = _COMPUTE_PATH + '/' + api
  return (msgs.BackendService(
      backends=[],
      description='my backend service',
      healthChecks=[(
          'https://www.googleapis.com/compute/{0}/projects/'
          'my-project/global/httpHealthChecks/my-health-check'.format(api))],
      name='backend-service-1',
      portName='http',
      protocol=msgs.BackendService.ProtocolValueValuesEnum.HTTP,
      selfLink=(prefix + '/projects/my-project'
                '/global/backendServices/backend-service-1'),
      cdnPolicy=msgs.BackendServiceCdnPolicy(cacheKeyPolicy=msgs.CacheKeyPolicy(
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

CENTOS_IMAGES = [
    messages.Image(
        name='centos-6-v20140408',
        family='centos-6',
        selfLink=('https://www.googleapis.com/compute/v1/projects/centos-cloud/'
                  'global/images/centos-6-v20140408'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='centos-6-v20140318',
        family='centos-6',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=('https://www.googleapis.com/compute/v1/projects/centos-cloud/'
                  'global/images/centos-6-v20140318'),
        status=messages.Image.StatusValueValuesEnum.READY),
]


def MakeDiskTypes(msgs, api, scope_type='zone', scope_name='zone-1',
                  project='my-project'):
  """Creates a list of diskType messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.
    scope_type: The type of scope (zone or region)
    scope_name: The name of scope (eg. us-central1-a)
    project: The project name.

  Returns:
    A list of message objects representing diskTypes.
  """

  if api is None:
    api = 'v1'
  prefix = '{0}/{1}'.format(_COMPUTE_PATH, api)
  disk_types = [
      msgs.DiskType(
          name='pd-standard',
          validDiskSize='10GB-10TB',
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-standard'
                    .format(prefix, project, scope_type + 's', scope_name)),
      ),
      msgs.DiskType(
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          name='pd-ssd',
          validDiskSize='10GB-1TB',
          selfLink=('{0}/projects/{1}/{2}/{3}/diskTypes/pd-ssd'
                    .format(prefix, project, scope_type + 's', scope_name))),
  ]
  for disk_type in disk_types:
    # Field 'region' is missing in regional disk types.
    if scope_type == 'zone':
      setattr(disk_type, scope_type,
              '{0}/projects/{1}/{2}/{3}'
              .format(prefix, project, scope_type + 's', scope_name))
  return disk_types

DISK_TYPES = [
    messages.DiskType(
        name='pd-standard',
        validDiskSize='10GB-10TB',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.DiskType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='pd-ssd',
        validDiskSize='10GB-1TB',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

]

DISKS = [
    messages.Disk(
        name='disk-1',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-1'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.Disk(
        name='disk-2',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-2'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-ssd'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.Disk(
        name='disk-3',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/disks/disk-3'),
        sizeGb=10,
        status=messages.Disk.StatusValueValuesEnum.READY,
        type=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/diskTypes/pd-standard'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]


def MakeIamPolicy(msgs, etag, bindings=None):
  if bindings:
    return msgs.Policy(etag=etag, bindings=bindings)
  else:
    return msgs.Policy(etag=etag)


def EmptyAlphaIamPolicy():
  return MakeIamPolicy(alpha_messages, b'test')


def AlphaIamPolicyWithOneBinding():
  return MakeIamPolicy(alpha_messages, b'test',
                       bindings=[alpha_messages.Binding(
                           role='owner',
                           members=['user:testuser@google.com'])])


def AlphaIamPolicyWithOneBindingAndDifferentEtag():
  return MakeIamPolicy(alpha_messages, b'etagTwo',
                       bindings=[alpha_messages.Binding(
                           role='owner',
                           members=['user:testuser@google.com'])])


def EmptyBetaIamPolicy():
  return MakeIamPolicy(beta_messages, b'test')


def BetaIamPolicyWithOneBindingAndDifferentEtag():
  return MakeIamPolicy(beta_messages, b'etagTwo',
                       bindings=[beta_messages.Binding(
                           role='owner',
                           members=['user:testuser@google.com'])])


def MakeForwardingRules(msgs, api):
  """Make regional forwarding rule test resources for the given api version."""
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.ForwardingRule(
          name='forwarding-rule-1',
          IPAddress='162.222.178.83',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.TCP,
          portRange='1-65535',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/forwardingRules/forwarding-rule-1'),
          target=(prefix + '/projects/my-project/'
                  'zones/zone-1/targetInstances/target-1')),

      msgs.ForwardingRule(
          name='forwarding-rule-2',
          IPAddress='162.222.178.84',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.UDP,
          portRange='1-65535',
          region=(prefix + '/projects/my-project/'
                  'regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/forwardingRules/forwarding-rule-2'),
          target=(prefix + '/projects/my-project/'
                  'regions/region-1/targetPools/target-2')),
  ]


FORWARDING_RULES_BETA = MakeForwardingRules(beta_messages, 'beta')
FORWARDING_RULES_V1 = MakeForwardingRules(messages, 'v1')


def MakeGlobalForwardingRules(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.ForwardingRule(
          name='global-forwarding-rule-1',
          IPAddress='162.222.178.85',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.TCP,
          portRange='1-65535',
          selfLink=(prefix + '/projects/my-project/'
                    'global/forwardingRules/global-forwarding-rule-1'),
          target=(prefix + '/projects/my-project/'
                  'global/targetHttpProxies/proxy-1')),

      msgs.ForwardingRule(
          name='global-forwarding-rule-2',
          IPAddress='162.222.178.86',
          IPProtocol=msgs.ForwardingRule.IPProtocolValueValuesEnum.UDP,
          portRange='1-65535',
          selfLink=(prefix + '/projects/my-project/'
                    'global/forwardingRules/global-forwarding-rule-2'),
          target=(prefix + '/projects/my-project/'
                  'global/targetHttpProxies/proxy-2')),
  ]


GLOBAL_FORWARDING_RULES_BETA = MakeGlobalForwardingRules(messages, 'beta')
GLOBAL_FORWARDING_RULES_V1 = MakeGlobalForwardingRules(messages, 'v1')


GLOBAL_OPERATIONS = [
    messages.Operation(
        name='operation-1',
        status=messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/operations/operation-1'),
        targetLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'resource/resource-1')),
]

ALPHA_GLOBAL_OPERATIONS = [
    alpha_messages.Operation(
        name='operation-1',
        status=alpha_messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/operations/operation-1'),
        targetLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'resource/resource-1')),
]

BETA_GLOBAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-1',
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        operationType='insert',
        insertTime='2014-09-04T09:55:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/beta/projects/'
                  'my-project/global/operations/operation-1'),
        targetLink=('https://www.googleapis.com/compute/beta/projects/'
                    'my-project/resource/resource-1')),
]


def MakeHealthChecks(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.HealthCheck(
          name='health-check-http-1',
          type=msgs.HealthCheck.TypeValueValuesEnum.HTTP,
          httpHealthCheck=msgs.HTTPHealthCheck(
              host='www.example.com',
              port=8080,
              portName='happy-http-port',
              requestPath='/testpath',
              proxyHeader=(msgs.HTTPHealthCheck
                           .ProxyHeaderValueValuesEnum.PROXY_V1)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-http-1')),

      msgs.HealthCheck(
          name='health-check-http-2',
          type=msgs.HealthCheck.TypeValueValuesEnum.HTTP,
          httpHealthCheck=msgs.HTTPHealthCheck(
              host='www.example.com',
              port=80,
              requestPath='/',
              proxyHeader=msgs.HTTPHealthCheck.ProxyHeaderValueValuesEnum.NONE),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-http-2')),

      msgs.HealthCheck(
          name='health-check-https',
          type=msgs.HealthCheck.TypeValueValuesEnum.HTTPS,
          httpsHealthCheck=msgs.HTTPSHealthCheck(
              host='www.example.com',
              port=443,
              portName='happy-https-port',
              requestPath='/',
              proxyHeader=(msgs.HTTPSHealthCheck
                           .ProxyHeaderValueValuesEnum.PROXY_V1)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-https')),

      msgs.HealthCheck(
          name='health-check-tcp',
          type=msgs.HealthCheck.TypeValueValuesEnum.TCP,
          tcpHealthCheck=msgs.TCPHealthCheck(
              port=80,
              portName='happy-tcp-port',
              request='req',
              response='ack',
              proxyHeader=msgs.TCPHealthCheck.ProxyHeaderValueValuesEnum.NONE),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-tcp')),

      msgs.HealthCheck(
          name='health-check-ssl',
          type=msgs.HealthCheck.TypeValueValuesEnum.SSL,
          sslHealthCheck=msgs.SSLHealthCheck(
              port=443,
              portName='happy-ssl-port',
              request='req',
              response='ack',
              proxyHeader=(msgs.SSLHealthCheck
                           .ProxyHeaderValueValuesEnum.PROXY_V1)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-ssl'))]


def MakeHealthCheckAlpha(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.HealthCheck(
          name='health-check-http2',
          type=msgs.HealthCheck.TypeValueValuesEnum.HTTP2,
          http2HealthCheck=msgs.HTTP2HealthCheck(
              host='www.example.com',
              port=80,
              portName='happy-http2-port',
              requestPath='/',
              proxyHeader=(
                  msgs.HTTP2HealthCheck.ProxyHeaderValueValuesEnum.NONE)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-http2')),
  ]

HEALTH_CHECKS = MakeHealthChecks(messages, 'v1')
HEALTH_CHECKS_ALPHA = MakeHealthCheckAlpha(alpha_messages, 'alpha')

HTTP_HEALTH_CHECKS = [
    messages.HttpHealthCheck(
        name='health-check-1',
        host='www.example.com',
        port=8080,
        requestPath='/testpath',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/httpHealthChecks/health-check-1')),
    messages.HttpHealthCheck(
        name='health-check-2',
        port=80,
        requestPath='/',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/httpHealthChecks/health-check-2')),
]


def MakeHttpsHealthChecks(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.HttpsHealthCheck(
          name='https-health-check-1',
          host='www.example.com', port=8888,
          requestPath='/testpath',
          selfLink=(prefix + '/projects/my-project/'
                    'global/httpsHealthChecks/https-health-check-1')),
      msgs.HttpsHealthCheck(
          name='https-health-check-2', port=443,
          requestPath='/',
          selfLink=(prefix + '/projects/my-project/'
                    'global/httpsHealthChecks/https-health-check-2'))]


def MakeHosts(msgs, api):
  """Creates a set of Host messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy hosts.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.Host(
          name='host-1',
          description='Host 1',
          hostType='n1-host-64-208',
          instances=[
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-1',
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-2',
          ],
          status=msgs.Host.StatusValueValuesEnum.READY,
          statusMessage='Host has room.',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/hosts/host-1'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),

      msgs.Host(
          name='host-2',
          description='Host Two',
          instances=[
              prefix + '/projects/my-project/zones/zone-1/'
              'instances/instance-3',
          ],
          status=msgs.Host.StatusValueValuesEnum.READY,
          statusMessage='Host is full.',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/hosts/host-2'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),

      msgs.Host(
          name='host-3',
          description='Host III',
          status=msgs.Host.StatusValueValuesEnum.REPAIR,
          statusMessage='Host is unavailable.',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/hosts/host-3'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),
  ]

HOSTS_ALPHA = MakeHosts(alpha_messages, 'alpha')
HOSTS = HOSTS_ALPHA


def MakeHostTypes(msgs, api):
  """Creates a set of Host Type messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy host types.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.HostType(
          cpuPlatform='80286',
          creationTimestamp='1982-02-01T10:00:00.0Z',
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          description='oldie but goodie',
          guestCpus=1,
          id=159265359,
          kind='compute#hostType',
          localSsdGb=0,
          memoryMb=256,
          name='iAPX-286',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/hostTypes/iAPX-286'),
          zone='zone-1'),
      msgs.HostType(
          cpuPlatform='broadwell',
          creationTimestamp='2014-12-12T10:00:00.0Z',
          description='',
          guestCpus=64,
          id=159265360,
          kind='compute#hostType',
          localSsdGb=46,
          memoryMb=416000,
          name='n1-host-64-416',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/hostTypes/n1-host-64-416'),
          zone='zone-1'),
  ]

HOST_TYPES_ALPHA = MakeHostTypes(alpha_messages, 'alpha')
HOST_TYPES = HOST_TYPES_ALPHA

HTTPS_HEALTH_CHECKS_V1 = MakeHttpsHealthChecks(messages, 'v1')
HTTPS_HEALTH_CHECKS_BETA = MakeHttpsHealthChecks(beta_messages, 'beta')

IMAGES = [
    messages.Image(
        name='image-1',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-1'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='image-2',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-2'),
        status=messages.Image.StatusValueValuesEnum.READY),

    messages.Image(
        name='image-3',
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/images/image-3'),
        status=messages.Image.StatusValueValuesEnum.READY),
]


def MakeInstances(msgs, api):
  """Creates a set of VM instance messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing VM instances.
  """
  prefix = _COMPUTE_PATH + '/' + api
  # Create a Scheduling message that includes the preemptible flag, now that all
  # API versions support it.
  scheduling = msgs.Scheduling(
      automaticRestart=False,
      onHostMaintenance=msgs.Scheduling.
      OnHostMaintenanceValueValuesEnum.TERMINATE,
      preemptible=False)
  return [
      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/zones/zone-1/'
              'machineTypes/n1-standard-1'),
          name='instance-1',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.1',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.75'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-1'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),

      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-1'),
          name='instance-2',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.2',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.74'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-2'),
          zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'zones/zone-1')),

      msgs.Instance(
          machineType=(
              prefix + '/projects/my-project/'
              'zones/zone-1/machineTypes/n1-standard-2'),
          name='instance-3',
          networkInterfaces=[
              msgs.NetworkInterface(
                  networkIP='10.0.0.3',
                  accessConfigs=[
                      msgs.AccessConfig(natIP='23.251.133.76'),
                  ],
              ),
          ],
          scheduling=scheduling,
          status=msgs.Instance.StatusValueValuesEnum.RUNNING,
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/instances/instance-3'),
          zone=(prefix + '/projects/my-project/zones/zone-1')),
  ]

INSTANCES_ALPHA = MakeInstances(alpha_messages, 'alpha')
INSTANCES_BETA = MakeInstances(beta_messages, 'beta')
INSTANCES_V1 = MakeInstances(messages, 'v1')


def MakeInstanceGroups(msgs, api, scope_type='zone', scope_name='zone-1'):
  """Creates a set of instanceGroup messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.
    scope_type: The type of scope (zone or region)
    scope_name: The name of scope (eg. us-central1-a)

  Returns:
    A list of message objects representing instanceGroups.
  """
  prefix = '{0}/{1}'.format(_COMPUTE_PATH, api)
  groups = [
      msgs.InstanceGroup(
          name='group-1',
          selfLink=('{0}/projects/my-project/{1}/{2}/instanceGroups/group-1'
                    .format(prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          description='Test instance group',
          fingerprint=b'123',
          namedPorts=[msgs.NamedPort(name='serv-1', port=1111),
                      msgs.NamedPort(name='serv-2', port=2222),
                      msgs.NamedPort(name='serv-3', port=3333)],
          size=0,
      ),
      msgs.InstanceGroup(
          name='group-2',
          selfLink=('{0}/projects/my-project/{1}/{2}/instanceGroups/group-2'
                    .format(prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:55:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/default'),
          namedPorts=[msgs.NamedPort(name='serv-1', port=1111)],
          size=3,
      ),
      msgs.InstanceGroup(
          name='group-3',
          selfLink=('{0}/projects/my-project/{1}/{2}/instanceGroups/group-3'
                    .format(prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:56:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/network-1'),
          size=10,
      ),
      msgs.InstanceGroup(
          name='group-4',
          selfLink=('{0}/projects/my-project/{1}/{2}/instanceGroups/group-4'
                    .format(prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:56:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/network-1'),
          size=1,
      ),
  ]
  for group in groups:
    setattr(group, scope_type,
            '{0}/projects/my-project/{1}/{2}'
            .format(prefix, scope_type + 's', scope_name))
  return groups


def MakeInstancesInInstanceGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-1'),
          status=(msgs.InstanceWithNamedPorts
                  .StatusValueValuesEnum.RUNNING)),
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-2'),
          status=(msgs.InstanceWithNamedPorts
                  .StatusValueValuesEnum.RUNNING)),
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-3'),
          status=(msgs.InstanceWithNamedPorts
                  .StatusValueValuesEnum.STOPPED)),
  ]


def MakeLastAttemptErrors(msgs, error_spec):
  return msgs.ManagedInstanceLastAttempt(
      errors=msgs.ManagedInstanceLastAttempt.ErrorsValue(
          errors=[
              msgs.ManagedInstanceLastAttempt.ErrorsValue.ErrorsValueListEntry(
                  code=err[0],
                  message=err[1]) for err in error_spec]))


def MakeInstancesInManagedInstanceGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-1'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.RUNNING),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.NONE)),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-2'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.STOPPED),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.RECREATING)),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-3'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.RUNNING),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.DELETING)),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-4'),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.CREATING),
          lastAttempt=MakeLastAttemptErrors(
              msgs, [('CONDITION_NOT_MET', 'True is not False'),
                     ('QUOTA_EXCEEDED', 'Limit is 5')])),
  ]


def MakeInstancesInManagedInstanceGroupBeta(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-1'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.RUNNING),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.NONE),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-1',
              name='xxx')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-2'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.STOPPED),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.RECREATING),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-1')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-3'),
          instanceStatus=(msgs.ManagedInstance
                          .InstanceStatusValueValuesEnum.RUNNING),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.DELETING),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-2',
              name='yyy')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-4'),
          currentAction=(msgs.ManagedInstance
                         .CurrentActionValueValuesEnum.CREATING),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-3'),
          lastAttempt=MakeLastAttemptErrors(
              msgs, [('CONDITION_NOT_MET', 'True is not False'),
                     ('QUOTA_EXCEEDED', 'Limit is 5')])),
  ]


def MakeInstanceTemplates(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.InstanceTemplate(
          name='instance-template-1',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-1'),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.1',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.75'),
                      ],
                  ),
              ],
              disks=[
                  msgs.AttachedDisk(
                      autoDelete=True,
                      boot=True,
                      deviceName='device-1',
                      mode=(msgs.AttachedDisk.
                            ModeValueValuesEnum.READ_WRITE),
                      source='disk-1',
                      type=(msgs.AttachedDisk.
                            TypeValueValuesEnum.PERSISTENT),
                  ),
              ],
              machineType='n1-standard-1',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling.
                  OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          )
      ),
      msgs.InstanceTemplate(
          name='instance-template-2',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-2'),
          creationTimestamp='2013-10-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.2',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.76'),
                      ],
                  ),
              ],
              machineType='n1-highmem-1',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling.
                  OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          )
      ),
      msgs.InstanceTemplate(
          name='instance-template-3',
          selfLink=(prefix + '/projects/my-project/'
                    'global/instanceTemplates/instance-template-3'),
          creationTimestamp='2013-11-06T17:54:10.636-07:00',
          properties=msgs.InstanceProperties(
              networkInterfaces=[
                  msgs.NetworkInterface(
                      networkIP='10.0.0.3',
                      accessConfigs=[
                          msgs.AccessConfig(natIP='23.251.133.77'),
                      ],
                  ),
              ],
              machineType='custom-6-17152',
              scheduling=msgs.Scheduling(
                  automaticRestart=False,
                  onHostMaintenance=msgs.Scheduling.
                  OnHostMaintenanceValueValuesEnum.TERMINATE,
                  preemptible=False,
              ),
          )
      )]


INSTANCE_TEMPLATES_V1 = MakeInstanceTemplates(messages, 'v1')
INSTANCE_TEMPLATES_BETA = MakeInstanceTemplates(beta_messages, 'beta')
INSTANCE_TEMPLATES_ALPHA = MakeInstanceTemplates(alpha_messages, 'alpha')


MACHINE_TYPES = [
    messages.MachineType(
        name='n1-standard-1',
        guestCpus=1,
        memoryMb=3840,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-1'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.MachineType(
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
        name='n1-standard-1-d',
        guestCpus=1,
        memoryMb=3840,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-1-d'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.MachineType(
        name='n1-highmem-2',
        guestCpus=2,
        memoryMb=30720,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/machineTypes/n1-standard-2'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
]


def MakeInstanceGroupManagersWithActions(
    api, scope_type, scope_name, current_actions=None, pending_actions=None):
  """Creates instance group manages with actions tests resources."""
  used_messages = _GetMessagesForApi(api)
  igm = used_messages.InstanceGroupManager(
      name='group-1',
      selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                'my-project/{1}/{2}/instanceGroupManagers/group-1'
                .format(api, scope_type + 's', scope_name)),
      creationTimestamp='2013-09-06T17:54:10.636-07:00',
      zone=('https://www.googleapis.com/compute/{0}/'
            'projects/my-project/zones/zone-1'.format(api)),
      baseInstanceName='test-instance-name-1',
      description='Test description.',
      fingerprint=b'1234',
      instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                     'my-project/{1}/{2}/instanceGroups/group-1'
                     .format(api, scope_type + 's', scope_name)),
      instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                        'my-project/global/instanceTemplates/template-1'
                        .format(api)),
      targetPools=[],
      targetSize=1)
  if current_actions:
    igm.currentActions = current_actions
  if pending_actions:
    igm.pendingActions = pending_actions

  setattr(igm, scope_type,
          'https://www.googleapis.com/compute/{0}/projects/my-project/{1}/{2}'
          .format(api, scope_type + 's', scope_name))
  return igm


def MakeInstanceGroupManagersWithCurrentActions(
    api, current_actions_count, scope_type='zone', scope_name='zone-1',
    current_actions_state='creating'):
  """Creates instance group manages with current actions tests resources."""
  used_messages = _GetMessagesForApi(api)
  current_actions = used_messages.InstanceGroupManagerActionsSummary(
      **{current_actions_state: current_actions_count,
         'none': (10 - current_actions_count)})
  return MakeInstanceGroupManagersWithActions(
      api, scope_type, scope_name, current_actions=current_actions)


def MakeInstanceGroupManagersWithPendingActions(
    api, pending_actions_count, current_actions_count=0, scope_type='zone',
    scope_name='zone-1', pending_actions_state='creating',
    current_actions_state='creating'):
  """Creates instance group manages with pending actions tests resources."""
  used_messages = _GetMessagesForApi(api)
  pending_actions = used_messages.InstanceGroupManagerPendingActionsSummary(
      **{pending_actions_state: pending_actions_count})
  current_actions = used_messages.InstanceGroupManagerActionsSummary(
      **{current_actions_state: current_actions_count})
  return MakeInstanceGroupManagersWithActions(
      api, scope_type, scope_name, current_actions, pending_actions)


def MakeInstanceGroupManagers(api, scope_name='zone-1', scope_type='zone'):
  """Creates instance group manages tests resources."""

  used_messages = _GetMessagesForApi(api)
  group_managers = [
      used_messages.InstanceGroupManager(
          name='group-1',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-1'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          baseInstanceName='test-instance-name-1',
          description='Test description.',
          fingerprint=b'1234',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-1'
                         .format(api, scope_type + 's', scope_name)),
          instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                            'my-project/global/instanceTemplates/template-1'
                            .format(api)),
          targetPools=[],
          targetSize=1,
      ),
      used_messages.InstanceGroupManager(
          name='group-2',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-2'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-2',
          description='Test description.',
          fingerprint=b'12345',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-2'
                         .format(api, scope_type + 's', scope_name)),
          instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                            'my-project/global/instanceTemplates/template-2'
                            .format(api)),
          targetPools=[],
          targetSize=10,
      ),
      used_messages.InstanceGroupManager(
          name='group-3',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-3'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2012-01-01T00:00:00.001+11:00',
          baseInstanceName='test-instance-name-3',
          description='Test description.',
          fingerprint=b'12346',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/zones/zone-1/instanceGroups/group-3'
                         .format(api)),
          instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                            'my-project/global/instanceTemplates/template-2'
                            .format(api)),
          targetPools=[],
          targetSize=1,
      ),
  ]
  for group_manager in group_managers:
    setattr(group_manager, scope_type,
            'https://www.googleapis.com/compute/{0}/'
            'projects/my-project/{1}/{2}'
            .format(api, scope_type + 's', scope_name))
  return group_managers


def MakeInstanceGroupManagersWithVersions(api, scope_name='zone-1',
                                          scope_type='zone'):
  """Creates instance group manages tests resources."""

  used_messages = _GetMessagesForApi(api)
  group_managers = [
      used_messages.InstanceGroupManager(
          name='group-1',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-1'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          baseInstanceName='test-instance-name-1',
          description='Test description.',
          fingerprint=b'1234',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-1'
                         .format(api, scope_type + 's', scope_name)),
          instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                            'my-project/global/instanceTemplates/template-1'
                            .format(api)),
          targetPools=[],
          targetSize=1,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=('https://www.googleapis.com/compute/{0}/'
                                    'projects/my-project/global/'
                                    'instanceTemplates/template-1'.format(api)),
              ),
          ],
      ),
      used_messages.InstanceGroupManager(
          name='group-2',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-2'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-2',
          description='Test description.',
          fingerprint=b'12345',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-2'
                         .format(api, scope_type + 's', scope_name)),
          targetPools=[],
          targetSize=10,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=('https://www.googleapis.com/compute/{0}/'
                                    'projects/my-project/global/'
                                    'instanceTemplates/template-1'.format(api)),
                  targetSize=used_messages.FixedOrPercent(percent=60)
              ),
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=('https://www.googleapis.com/compute/{0}/'
                                    'projects/my-project/global/'
                                    'instanceTemplates/template-2'.format(api)),
              ),
          ],
      ),
      used_messages.InstanceGroupManager(
          name='group-3',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-3'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2012-01-01T00:00:00.001+11:00',
          baseInstanceName='test-instance-name-3',
          description='Test description.',
          fingerprint=b'12346',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/zones/zone-1/instanceGroups/group-3'
                         .format(api)),
          instanceTemplate=('https://www.googleapis.com/compute/{0}/projects/'
                            'my-project/global/instanceTemplates/template-2'
                            .format(api)),
          targetPools=[],
          targetSize=1,
      ),
      used_messages.InstanceGroupManager(
          name='group-4',
          selfLink=('https://www.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-4'
                    .format(api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-4',
          description='Test description.',
          fingerprint=b'12347',
          instanceGroup=('https://www.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-4'
                         .format(api, scope_type + 's', scope_name)),
          targetPools=[],
          targetSize=10,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  name='some-tag',
                  instanceTemplate=('https://www.googleapis.com/compute/{0}/'
                                    'projects/my-project/global/'
                                    'instanceTemplates/template-1'.format(api)),
                  targetSize=used_messages.FixedOrPercent(percent=60),
              ),
              used_messages.InstanceGroupManagerVersion(
                  name='other-tag',
                  instanceTemplate=('https://www.googleapis.com/compute/{0}/'
                                    'projects/my-project/global/'
                                    'instanceTemplates/template-1'.format(api)),
              ),
          ],
      ),
  ]
  for group_manager in group_managers:
    setattr(group_manager, scope_type,
            'https://www.googleapis.com/compute/{0}/'
            'projects/my-project/{1}/{2}'
            .format(api, scope_type + 's', scope_name))
  return group_managers


NETWORKS_V1 = [
    # Legacy
    messages.Network(
        name='network-1',
        gatewayIPv4='10.240.0.1',
        IPv4Range='10.240.0.0/16',
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1')),

    # Custom
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=False,
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.REGIONAL)),
        selfLink=('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[
            'https://www.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-1',
            'https://www.googleapis.com/compute/v1/projects/'
            'my-project/regions/region-1/subnetworks/subnetwork-2'
        ]),

    # Auto
    messages.Network(
        name='network-3',
        autoCreateSubnetworks=True,
        routingConfig=messages.NetworkRoutingConfig(routingMode=(
            messages.NetworkRoutingConfig.RoutingModeValueValuesEnum.GLOBAL)),
        selfLink=('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-3'),
        subnetworks=[])
]

NETWORK_PEERINGS_V1 = [
    messages.Network(
        name='network-1',
        autoCreateSubnetworks=True,
        selfLink=('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-1'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-1',
                network='https://www.googleapis.com/compute/v1/'
                'projects/my-project/global/networks/network-2',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.'
            ),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-2',
                network='https://www.googleapis.com/compute/v1/'
                'projects/my-project-2/global/networks/network-3',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer '
                'network.'),
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='peering-3',
                network='https://www.googleapis.com/compute/v1/'
                'projects/my-project-3/global/networks/network-3',
                state=(messages.NetworkPeering.StateValueValuesEnum.INACTIVE),
                stateDetails='Peering is created.')
        ]),
    messages.Network(
        name='network-2',
        autoCreateSubnetworks=True,
        selfLink=('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/networks/network-2'),
        subnetworks=[],
        peerings=[
            messages.NetworkPeering(
                autoCreateRoutes=True,
                name='my-peering-1',
                network='https://www.googleapis.com/compute/v1/projects/'
                'my-project/global/networks/network-1',
                state=messages.NetworkPeering.StateValueValuesEnum.ACTIVE,
                stateDetails='Matching configuration is found on peer network.')
        ])
]


def MakeNodeGroups(msgs, api):
  """Creates a set of Node Group messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy note groups.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.NodeGroup(
          creationTimestamp='2018-01-23T10:00:00.0Z',
          description='description1',
          kind='compute#nodeGroup',
          name='group-1',
          nodeTemplate=(prefix + '/projects/my-project/'
                        'regions/region-1/nodeTemplates/template-1'),
          nodes=[
              msgs.NodeGroupNode(
                  index=1,
                  instances=[
                      prefix + '/projects/my-project/zones/zone-1/'
                      'instances/instance-1',
                      prefix + '/projects/my-project/zones/zone-1/'
                      'instances/instance-2'],
                  nodeType='iAPX-286'),
              msgs.NodeGroupNode(
                  index=2,
                  instances=[
                      prefix + '/projects/my-project/zones/zone-1/'
                      'instances/instance-3'],
                  nodeType='iAPX-286')],
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeGroups/group-1'),
          zone='zone-1'),
      msgs.NodeGroup(
          creationTimestamp='2018-02-21T10:00:00.0Z',
          description='description2',
          kind='compute#nodeGroup',
          name='group-2',
          nodeTemplate=(prefix + '/projects/my-project/'
                        'regions/region-1/nodeTemplates/template-2'),
          nodes=[
              msgs.NodeGroupNode(
                  index=1,
                  instances=[
                      prefix + '/projects/my-project/zones/zone-1/'
                      'instances/instance-4',
                      prefix + '/projects/my-project/zones/zone-1/'
                      'instances/instance-5'],
                  nodeType='n1-node-96-624')],
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeGroups/group-2'),
          zone='zone-1'),
  ]


NODE_GROUPS_ALPHA = MakeNodeGroups(alpha_messages, 'alpha')
NODE_GROUPS = NODE_GROUPS_ALPHA


def MakeNodeTemplates(msgs, api):
  """Creates a set of Node Template messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy note templates.
  """
  prefix = _COMPUTE_PATH + '/' + api
  node_affinity_value = msgs.NodeTemplate.NodeAffinityLabelsValue
  return [
      msgs.NodeTemplate(
          creationTimestamp='2017-12-12T10:00:00.0Z',
          description='a cool template',
          kind='compute#nodeTemplate',
          name='template-1',
          nodeAffinityLabels=node_affinity_value(
              additionalProperties=[
                  node_affinity_value.AdditionalProperty(
                      key='environment', value='prod'),
                  node_affinity_value.AdditionalProperty(
                      key='nodeGrouping', value='frontend')]),
          nodeType='iAPX-286',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/nodeTemplates/template-1'),
          status=msgs.NodeTemplate.StatusValueValuesEnum.READY,
          statusMessage='Template is ready.'),
      msgs.NodeTemplate(
          creationTimestamp='2018-01-15T10:00:00.0Z',
          description='a cold template',
          kind='compute#nodeTemplate',
          name='template-2',
          nodeAffinityLabels=node_affinity_value(
              additionalProperties=[
                  node_affinity_value.AdditionalProperty(
                      key='environment', value='prod'),
                  node_affinity_value.AdditionalProperty(
                      key='nodeGrouping', value='backend')]),
          nodeType='n1-node-96-624',
          region=(prefix + '/projects/my-project/regions/region-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'regions/region-1/nodeTemplates/template-2'),
          status=msgs.NodeTemplate.StatusValueValuesEnum.CREATING,
          statusMessage='Template is being created.'),
  ]


NODE_TEMPLATES_ALPHA = MakeNodeTemplates(alpha_messages, 'alpha')
NODE_TEMPLATES = NODE_TEMPLATES_ALPHA


def MakeNodeTypes(msgs, api):
  """Creates a set of Host Type messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing sole tenancy host types.
  """
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.NodeType(
          cpuPlatform='80286',
          creationTimestamp='1982-02-01T10:00:00.0Z',
          deprecated=msgs.DeprecationStatus(
              state=msgs.DeprecationStatus.StateValueValuesEnum.OBSOLETE),
          description='oldie but goodie',
          guestCpus=1,
          id=159265359,
          kind='compute#nodeType',
          localSsdGb=0,
          memoryMb=256,
          name='iAPX-286',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeTypes/iAPX-286'),
          zone='zone-1'),
      msgs.NodeType(
          cpuPlatform='skylake',
          creationTimestamp='2014-12-12T10:00:00.0Z',
          description='',
          guestCpus=96,
          id=159265360,
          kind='compute#nodeType',
          localSsdGb=46,
          memoryMb=416000,
          name='n1-node-96-624',
          selfLink=(prefix + '/projects/my-project/'
                    'zones/zone-1/nodeTypes/n1-node-96-624'),
          zone='zone-1'),
  ]


NODE_TYPES_ALPHA = MakeNodeTypes(alpha_messages, 'alpha')
NODE_TYPES = NODE_TYPES_ALPHA


def MakeNetworkEndpointGroups(msgs, api):
  """Creates a set of NEG messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.

  Returns:
    A list of message objects representing network endpoint groups.
  """
  prefix = _COMPUTE_PATH + '/' + api
  neg_type_enum = msgs.NetworkEndpointGroup.NetworkEndpointTypeValueValuesEnum
  type_enum = msgs.NetworkEndpointGroup.TypeValueValuesEnum
  return [
      msgs.NetworkEndpointGroup(
          description='My NEG 1',
          kind='compute#networkEndpointGroup',
          loadBalancer=msgs.NetworkEndpointGroupLbNetworkEndpointGroup(
              network=('https://www.googleapis.com/compute/v1/projects/'
                       'my-project/global/networks/network-1'),
              zone='zone-1'),
          name='my-neg1',
          networkEndpointType=neg_type_enum.GCE_VM_IP_PORT,
          selfLink=(prefix + '/projects/my-project/zones/zone-1/'
                    'networkEndpointGroups/my-neg1'),
          size=5,
          type=type_enum.LOAD_BALANCING),
      msgs.NetworkEndpointGroup(
          description='My NEG Too',
          kind='compute#networkEndpointGroup',
          loadBalancer=msgs.NetworkEndpointGroupLbNetworkEndpointGroup(
              network=('https://www.googleapis.com/compute/v1/projects/'
                       'my-project/global/networks/network-2'),
              zone='zone-2'),
          name='my-neg2',
          networkEndpointType=neg_type_enum.GCE_VM_IP_PORT,
          selfLink=(prefix + '/projects/my-project/zones/zone-2/'
                    'networkEndpointGroups/my-neg2'),
          size=2,
          type=type_enum.LOAD_BALANCING),
  ]


NETWORK_ENDPOINT_GROUPS_ALPHA = MakeNetworkEndpointGroups(alpha_messages,
                                                          'alpha')
NETWORK_ENDPOINT_GROUPS = NETWORK_ENDPOINT_GROUPS_ALPHA


def MakeOsloginClient(version, use_extended_profile=False):
  """Return a dummy oslogin API client."""
  oslogin_messages = core_apis.GetMessagesModule('oslogin', version)

  ssh_public_keys_value = oslogin_messages.LoginProfile.SshPublicKeysValue
  profile_basic = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[oslogin_messages.PosixAccount(
          primary=True,
          username='user_google_com',
          uid=123456,
          gid=123456,
          homeDirectory='/home/user_google_com',
          shell='/bin/bash')],
      sshPublicKeys=ssh_public_keys_value(
          additionalProperties=[
              ssh_public_keys_value.AdditionalProperty(
                  key='qwertyuiop',
                  value=oslogin_messages.SshPublicKey(
                      fingerprint=b'asdfasdf',
                      key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))]),
  )

  profile_extended = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[
          oslogin_messages.PosixAccount(
              primary=False,
              username='user_google_com',
              uid=123456,
              gid=123456,
              homeDirectory='/home/user_google_com',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=False,
              username='testaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/testaccount',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=True,
              username='myaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/myaccount',
              shell='/bin/bash'),
      ],
      sshPublicKeys=ssh_public_keys_value(
          additionalProperties=[
              ssh_public_keys_value.AdditionalProperty(
                  key='qwertyuiop',
                  value=oslogin_messages.SshPublicKey(
                      fingerprint=b'asdfasdf',
                      key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))]),
  )

  if use_extended_profile:
    login_profile = profile_extended
  else:
    login_profile = profile_basic

  import_public_key_response = oslogin_messages.ImportSshPublicKeyResponse(
      loginProfile=login_profile)

  class _OsloginUsers(object):

    @classmethod
    def ImportSshPublicKey(cls, message):
      del cls, message  # Unused
      return import_public_key_response

  class _OsloginClient(object):
    users = _OsloginUsers
    MESSAGES_MODULE = oslogin_messages

  return _OsloginClient()


PROJECTS = [
    messages.Project(
        name='my-project',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        commonInstanceMetadata=messages.Metadata(
            items=[
                messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                messages.Metadata.ItemsValueListEntry(
                    key='c',
                    value='d'),
            ]
        ),
        selfLink='https://www.googleapis.com/compute/v1/projects/my-project/')
]

REGIONAL_OPERATIONS = [
    messages.Operation(
        name='operation-2',
        operationType='insert',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        status=messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:53:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1/operations/operation-2'),
        targetLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'regions/region-1/resource/resource-2')),
]

BETA_REGIONAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-2', operationType='insert',
        region=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1'),
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:53:33.679-07:00',
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1/operations/operation-2'),
        targetLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1/resource/resource-2'))]

REGIONS = [
    messages.Region(
        name='region-1',
        quotas=[
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=5120.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=30.0),
            messages.Quota(
                limit=7.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=1.0),
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=2.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-1'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://www.googleapis.com/compute/v1/projects/'
                         'my-project/regions/region-2'))),

    messages.Region(
        name='region-2',
        quotas=[
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=51200.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=300.0),
            messages.Quota(
                limit=70.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=10.0),
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=20.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-2')),

    messages.Region(
        name='region-3',
        quotas=[
            messages.Quota(
                limit=4800.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            messages.Quota(
                limit=102400.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=600.0),
            messages.Quota(
                limit=140.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=20.0),
            messages.Quota(
                limit=480.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=40.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/region-3')),
]


BETA_REGIONS = [
    beta_messages.Region(
        name='region-1',
        quotas=[
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=5120.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=30.0),
            beta_messages.Quota(
                limit=7.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=1.0),
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=2.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1'),
        deprecated=beta_messages.DeprecationStatus(
            state=beta_messages.DeprecationStatus.StateValueValuesEnum
            .DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=(
                'https://www.googleapis.com/compute/beta/projects/'
                'my-project/regions/region-2'))),
    beta_messages.Region(
        name='region-2',
        quotas=[
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=51200.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=300.0),
            beta_messages.Quota(
                limit=70.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=10.0),
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=20.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-2')),
    beta_messages.Region(
        name='region-3',
        quotas=[
            beta_messages.Quota(
                limit=4800.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            beta_messages.Quota(
                limit=102400.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .DISKS_TOTAL_GB,
                usage=600.0),
            beta_messages.Quota(
                limit=140.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=20.0),
            beta_messages.Quota(
                limit=480.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=40.0)],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-3'))]


def MakeRoutes(msgs, api, network='default'):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.Route(
          destRange='10.0.0.0/8',
          name='route-1',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopIp='10.240.0.0',
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-1'),
      ),

      msgs.Route(
          destRange='0.0.0.0/0',
          name='route-2',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopInstance=(
              prefix + '/projects/my-project/'
              'zones/zone-1/instances/instance-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-2'),
      ),

      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-3',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopGateway=(
              prefix + '/projects/my-project/'
              'global/gateways/default-internet-gateway'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-3'),
          priority=1,
      ),

      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-4',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopVpnTunnel=(
              prefix + '/projects/my-project/'
              'regions/region-1/vpnTunnels/tunnel-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-4'),
      ),
  ]

ROUTES_V1 = MakeRoutes(messages, 'v1')
ROUTES_V1_TWO_NETWORKS = ROUTES_V1 + MakeRoutes(messages, 'v1', network='foo')


def MakeSecurityPolicy(msgs, security_policy_ref):
  return msgs.SecurityPolicy(
      name=security_policy_ref.Name(),
      description='my description',
      id=123,
      fingerprint=b'=g\313\0305\220\f\266',
      rules=[
          msgs.SecurityPolicyRule(
              description='default rule',
              priority=2147483647,
              match=msgs.SecurityPolicyRuleMatcher(
                  versionedExpr=msgs.SecurityPolicyRuleMatcher.
                  VersionedExprValueValuesEnum('SRC_IPS_V1'),
                  config=msgs.SecurityPolicyRuleMatcherConfig(
                      srcIpRanges=['*'])),
              action='allow',
              preview=False)
      ],
      selfLink=security_policy_ref.SelfLink())


def MakeSecurityPolicyRule(msgs):
  return msgs.SecurityPolicyRule(
      priority=1000,
      description='my rule',
      action='allow',
      match=msgs.SecurityPolicyRuleMatcher(
          versionedExpr=msgs.SecurityPolicyRuleMatcher.
          VersionedExprValueValuesEnum('SRC_IPS_V1'),
          config=msgs.SecurityPolicyRuleMatcherConfig(
              srcIpRanges=['1.1.1.1'])),
      preview=False)

SNAPSHOTS = [
    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-1',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-1'),
        sourceDisk=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-1'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),

    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-2',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-2'),
        sourceDisk=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-2'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),

    messages.Snapshot(
        diskSizeGb=10,
        name='snapshot-3',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'global/snapshots/snapshot-3'),
        sourceDisk=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/disks/disk-3'),
        status=messages.Snapshot.StatusValueValuesEnum.READY),
]

SSL_CERTIFICATES = [
    messages.SslCertificate(
        name='ssl-cert-1',
        certificate=(
            '-----BEGIN CERTIFICATE-----\n'
            'MIICZzCCAdACCQDjYQHCnQOiTDANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV\n'
            'UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE\n'
            'CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj\n'
            'bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMTcxMloXDTE1MTAxMzIwMTcxMloweDEL\n'
            'MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0\n'
            'bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw\n'
            'FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC\n'
            'gYEAw3JXUCTn8J2VeWqHuc9zJxdy1WfQJtbDxQUUy4nsqU6QPGso3HYXlI/eozg6\n'
            'bGhkJNtDVV4AAPQVv01aoFMt3T6MKLzAkjfse7zKQmQ399vQaE7lbLAV9M4FSV9s\n'
            'wksSvT7cOW9ddcdKdyV3NTbptW5PeUE8Zk/aCFLPLqOg800CAwEAATANBgkqhkiG\n'
            '9w0BAQsFAAOBgQCKMIRiThp2O+wg7M8wcNSdPzAZ61UMeisQKS5OEY90OsekWYUT\n'
            'zMkUznRtycTdTBxEqKQoJKeAXq16SezJaZYE48FpoObQc2ZLMvje7F82tOwC2kob\n'
            'v83LejX3zZnirv2PZVcFgvUE0k3a8/14enHi7j6jZu+Pl5ZM9BZ+vkBO8g==\n'
            '-----END CERTIFICATE-----'),
        creationTimestamp='2014-09-04T09:56:33.679-07:00',
        description='Certificate one.',
        selfLink=_V1_URI_PREFIX + 'global/sslCertificates/ssl-cert-1',
    ),
    messages.SslCertificate(
        name='ssl-cert-2',
        certificate=(textwrap.dedent("""\
            -----BEGIN CERTIFICATE-----
            MIICZzCCAdACCQChX1chr91razANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
            UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
            CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
            bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMzExNVoXDTE1MTAxMzIwMzExNVoweDEL
            MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
            bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
            FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
            gYEAq3S7ZDKHHwdro6f9Zxk8kNZ39a2ejqls4LMropt+RpkHqpaQK17Q2rUykw+f
            P+mXojUB1ZUKkrCE+xcEHeafUgG1lBof56v2bSzIQVeeS1chvDNYGqweEHIkbFHv
            8e8RY9XPkk4hMcW+uxrzaKv1yddBucyETLa3/dYmaEzHcOsCAwEAATANBgkqhkiG
            9w0BAQsFAAOBgQAxBD6GUsgGYfeHkjo3CK/X5cbaPTdUncD13uaI4Q31GWZGhGJX
            t9hMvJdXQ6vzKXBuX6ZLUxvL9SFT+pMLTWGStUFNcDFv/Fqdcre0jPoYEJv/tOHT
            n82GtW9nMhZfVj2PrRiuZwOV8qB6+uEadbcPcET3TcH1WJacbBlHufk1wQ==
            -----END CERTIFICATE-----""")),
        creationTimestamp='2014-10-04T07:56:33.679-07:00',
        description='Certificate two.',
        selfLink=_V1_URI_PREFIX + 'global/sslCertificates/ssl-cert-2',
    ),
]

ALPHA_SSL_CERTIFICATES = [
    alpha_messages.SslCertificate(
        type=alpha_messages.SslCertificate.TypeValueValuesEnum.SELF_MANAGED,
        name='ssl-cert-1',
        selfManaged=alpha_messages.SslCertificateSelfManagedSslCertificate(
            certificate=(textwrap.dedent("""\
                -----BEGIN CERTIFICATE-----
                MIICZzCCAdACCQDjYQHCnQOiTDANBgkqhkiG9w0BAQsFADB4MQswCQYDVQQGEwJV
                UzETMBEGA1UECAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTEPMA0GA1UE
                CgwGR29vZ2xlMRgwFgYDVQQLDA9DbG91ZCBQbGF0Zm9ybXMxFzAVBgNVBAMMDmdj
                bG91ZCBjb21wdXRlMB4XDTE0MTAxMzIwMTcxMloXDTE1MTAxMzIwMTcxMloweDEL
                MAkGA1UEBhMCVVMxEzARBgNVBAgMCldhc2hpbmd0b24xEDAOBgNVBAcMB1NlYXR0
                bGUxDzANBgNVBAoMBkdvb2dsZTEYMBYGA1UECwwPQ2xvdWQgUGxhdGZvcm1zMRcw
                FQYDVQQDDA5nY2xvdWQgY29tcHV0ZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkC
                gYEAw3JXUCTn8J2VeWqHuc9zJxdy1WfQJtbDxQUUy4nsqU6QPGso3HYXlI/eozg6
                bGhkJNtDVV4AAPQVv01aoFMt3T6MKLzAkjfse7zKQmQ399vQaE7lbLAV9M4FSV9s
                wksSvT7cOW9ddcdKdyV3NTbptW5PeUE8Zk/aCFLPLqOg800CAwEAATANBgkqhkiG
                9w0BAQsFAAOBgQCKMIRiThp2O+wg7M8wcNSdPzAZ61UMeisQKS5OEY90OsekWYUT
                zMkUznRtycTdTBxEqKQoJKeAXq16SezJaZYE48FpoObQc2ZLMvje7F82tOwC2kob
                v83LejX3zZnirv2PZVcFgvUE0k3a8/14enHi7j6jZu+Pl5ZM9BZ+vkBO8g==
                -----END CERTIFICATE-----"""))),
        creationTimestamp='2017-12-18T11:11:11.000-07:00',
        description='Self-managed certificate.',
        selfLink=_ALPHA_URI_PREFIX + 'global/sslCertificates/ssl-cert-1',
    ),
    alpha_messages.SslCertificate(
        name='ssl-cert-2',
        type=alpha_messages.SslCertificate.TypeValueValuesEnum.
        MANAGED,
        managed=alpha_messages.SslCertificateManagedSslCertificate(
            domains=[
                'test1.certsbridge.com',
                # Punycode for Ṳᾔḯ¢◎ⅾℯ.certsbridge.com
                'xn--8a342mzfam5b18csni3w.certsbridge.com',
            ],
            status=alpha_messages.SslCertificateManagedSslCertificate.
            StatusValueValuesEnum.ACTIVE,
            domainStatus=alpha_messages.
            SslCertificateManagedSslCertificate.DomainStatusValue(
                additionalProperties=[
                    alpha_messages.SslCertificateManagedSslCertificate.
                    DomainStatusValue.AdditionalProperty(
                        key='test1.certsbridge.com',
                        value=alpha_messages.
                        SslCertificateManagedSslCertificate.DomainStatusValue.
                        AdditionalProperty.ValueValueValuesEnum.
                        ACTIVE,
                    ),
                    alpha_messages.SslCertificateManagedSslCertificate.
                    DomainStatusValue.AdditionalProperty(
                        key='xn--8a342mzfam5b18csni3w.certsbridge.com',
                        value=alpha_messages.
                        SslCertificateManagedSslCertificate.DomainStatusValue.
                        AdditionalProperty.ValueValueValuesEnum.
                        FAILED_CAA_FORBIDDEN,
                    ),
                ])),
        creationTimestamp='2017-12-17T10:00:00.000-07:00',
        description='Managed certificate.',
        selfLink=_ALPHA_URI_PREFIX +
        'global/sslCertificates/ssl-cert-2',
    ),
]

TARGET_HTTP_PROXIES = [
    messages.TargetHttpProxy(
        name='target-http-proxy-1',
        description='My first proxy',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-1',
        selfLink=(
            _V1_URI_PREFIX + 'global/targetHttpProxies/target-http-proxy-1')),

    messages.TargetHttpProxy(
        name='target-http-proxy-2',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-2',
        selfLink=(
            _V1_URI_PREFIX + 'global/targetHttpProxies/target-http-proxy-2')),

    messages.TargetHttpProxy(
        name='target-http-proxy-3',
        description='My last proxy',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-3',
        selfLink=(
            _V1_URI_PREFIX + 'global/targetHttpProxies/target-http-proxy-3')),
]


def MakeTargetHttpsProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetHttpsProxy(
          name='target-https-proxy-1',
          description='My first proxy',
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-1']),
          urlMap=long_prefix + '/global/urlMaps/url-map-1',
          selfLink=(
              long_prefix + '/global/targetHttpsProxies/target-https-proxy-1')),

      msgs.TargetHttpsProxy(
          name='target-https-proxy-2',
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-2']),
          urlMap=long_prefix + '/global/urlMaps/url-map-2',
          selfLink=(
              long_prefix + '/global/targetHttpsProxies/target-https-proxy-2')),

      msgs.TargetHttpsProxy(
          name='target-https-proxy-3',
          description='My last proxy',
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-3']),
          urlMap=long_prefix + '/global/urlMaps/url-map-3',
          selfLink=(
              long_prefix + '/global/targetHttpsProxies/target-https-proxy-3'))]


TARGET_HTTPS_PROXIES_BETA = MakeTargetHttpsProxies(beta_messages, 'beta')
TARGET_HTTPS_PROXIES_V1 = MakeTargetHttpsProxies(messages, 'v1')


def MakeTargetSslProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetSslProxy(
          name='target-ssl-proxy-1',
          description='My first proxy',
          proxyHeader=msgs.TargetSslProxy.ProxyHeaderValueValuesEnum.PROXY_V1,
          service=(long_prefix + '/global/backendServices/my-service'),
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-1'])),

      msgs.TargetSslProxy(
          name='target-ssl-proxy-2',
          description='My other proxy',
          proxyHeader=msgs.TargetSslProxy.ProxyHeaderValueValuesEnum.NONE,
          service=(long_prefix + '/global/backendServices/my-service'),
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-2'])),

      msgs.TargetSslProxy(
          name='target-ssl-proxy-3',
          description='My other other proxy',
          service=(long_prefix + '/global/backendServices/my-service'),
          sslCertificates=([long_prefix +
                            '/global/sslCertificates/ssl-cert-3']))]

TARGET_SSL_PROXIES_V1 = MakeTargetSslProxies(messages, 'v1')


def MakeTargetTcpProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetTcpProxy(
          name='target-tcp-proxy-1',
          description='My first proxy',
          proxyHeader=msgs.TargetTcpProxy.ProxyHeaderValueValuesEnum.PROXY_V1,
          service=(long_prefix + '/global/backendServices/my-service')),

      msgs.TargetTcpProxy(
          name='target-tcp-proxy-2',
          description='My other proxy',
          proxyHeader=msgs.TargetTcpProxy.ProxyHeaderValueValuesEnum.NONE,
          service=(long_prefix + '/global/backendServices/my-service')),

      msgs.TargetTcpProxy(
          name='target-tcp-proxy-3',
          description='My other other proxy',
          service=(long_prefix + '/global/backendServices/my-service'))]

TARGET_TCP_PROXIES_V1 = MakeTargetTcpProxies(messages, 'v1')

TARGET_INSTANCES = [
    messages.TargetInstance(
        name='target-instance-1',
        instance=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/instances/instance-1'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/targetInstances/target-instance-1'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.TargetInstance(
        name='target-instance-2',
        instance=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/instances/instance-2'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/targetInstances/target-instance-2'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),

    messages.TargetInstance(
        name='target-instance-3',
        instance=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-2/instances/instance-3'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-2/targetInstances/target-instance-3'),
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-2')),
]

TARGET_POOLS = [
    messages.TargetPool(
        backupPool=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-2'), name='pool-1',
        region=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1'),
        selfLink=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-1'),
        sessionAffinity=(
            messages.TargetPool.SessionAffinityValueValuesEnum.CLIENT_IP)),
    messages.TargetPool(
        name='pool-2',
        healthChecks=(
            [
                'https://www.googleapis.com/compute/v1/projects/my-project/'
                'global/httpHealthChecks/check-1',
                'https://www.googleapis.com/compute/v1/projects/my-project/'
                'global/httpHealthChecks/check-2']),
        region=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1'),
        selfLink=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-2'),
        sessionAffinity=(
            messages.TargetPool.SessionAffinityValueValuesEnum.CLIENT_IP_PROTO)
    ),
    messages.TargetPool(
        name='pool-3',
        region=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1'),
        selfLink=(
            'https://www.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-3'),
        sessionAffinity=(
            messages.TargetPool.SessionAffinityValueValuesEnum.NONE))]


def MakeTargetVpnGateways(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  region1 = prefix + '/projects/my-project/regions/region-1'
  region2 = prefix + '/projects/my-project/regions/region-2'
  return [
      msgs.TargetVpnGateway(
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          description='gateway 1 description',
          id=123456,
          name='gateway-1',
          network='my-network',
          region=region1,
          selfLink=region1 + '/targetVpnGateways/gateway-1',
          status=msgs.TargetVpnGateway.StatusValueValuesEnum.READY,
          tunnels=[region1 + '/tunnels/tunnel-1']),
      msgs.TargetVpnGateway(
          creationTimestamp='2013-10-06T17:54:10.636-07:00',
          id=22,
          name='gateway-2',
          network='my-network',
          region=region1,
          selfLink=region1 + '/targetVpnGateways/gateway-2',
          status=msgs.TargetVpnGateway.StatusValueValuesEnum.READY,
          tunnels=[]),
      msgs.TargetVpnGateway(
          creationTimestamp='2014-09-06T17:54:10.636-07:00',
          description='gateway 3 description',
          id=333,
          name='gateway-3',
          network='your-network',
          region=region2,
          selfLink=region2 + '/targetVpnGateways/gateway-3',
          status=msgs.TargetVpnGateway.StatusValueValuesEnum.READY,
          tunnels=[region2 + '/tunnels/tunnel-3',
                   region2 + '/tunnels/tunnel-33'])]


TARGET_VPN_GATEWAYS_BETA = MakeTargetVpnGateways(beta_messages, 'beta')
TARGET_VPN_GATEWAYS_V1 = MakeTargetVpnGateways(beta_messages, 'v1')


def MakeUrlMaps(msgs, api):
  """Create url map resources."""
  if api == 'alpha':
    backend_services_prefix = _BACKEND_SERVICES_ALPHA_URI_PREFIX
    backend_buckets_prefix = _BACKEND_BUCKETS_ALPHA_URI_PREFIX
    url_maps_prefix = _URL_MAPS_ALPHA_URI_PREFIX
  elif api == 'beta':
    backend_services_prefix = _BACKEND_SERVICES_BETA_URI_PREFIX
    backend_buckets_prefix = _BACKEND_BUCKETS_BETA_URI_PREFIX
    url_maps_prefix = _URL_MAPS_BETA_URI_PREFIX
  elif api == 'v1':
    backend_services_prefix = _BACKEND_SERVICES_URI_PREFIX
    backend_buckets_prefix = _BACKEND_BUCKETS_URI_PREFIX
    url_maps_prefix = _URL_MAPS_URI_PREFIX

  url_maps = [
      msgs.UrlMap(
          name='url-map-1',
          defaultService=backend_services_prefix + 'default-service',
          hostRules=[
              messages.HostRule(hosts=['*.google.com', 'google.com'],
                                pathMatcher='www'),
              messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                       '*-youtube.com'],
                                pathMatcher='youtube'),
          ],
          pathMatchers=[
              messages.PathMatcher(
                  name='www',
                  defaultService=(backend_services_prefix +
                                  'www-default'),
                  pathRules=[
                      messages.PathRule(paths=['/search', '/search/*'],
                                        service=backend_services_prefix
                                        + 'search'),
                      messages.PathRule(paths=['/search/ads', '/search/ads/*'],
                                        service=backend_services_prefix
                                        + 'ads'),
                      messages.PathRule(paths=['/images'],
                                        service=backend_services_prefix
                                        + 'images'),
                  ]),
              messages.PathMatcher(
                  name='youtube',
                  defaultService=(backend_services_prefix +
                                  'youtube-default'),
                  pathRules=[
                      messages.PathRule(paths=['/search', '/search/*'],
                                        service=(
                                            backend_services_prefix +
                                            'youtube-search')),
                      messages.PathRule(paths=['/watch', '/view', '/preview'],
                                        service=(
                                            backend_services_prefix +
                                            'youtube-watch')),
                  ]),
          ],
          selfLink=(url_maps_prefix + 'url-map-1'),
          tests=[
              messages.UrlMapTest(host='www.google.com',
                                  path='/search/ads/inline?q=flowers',
                                  service=backend_services_prefix +
                                  'ads'),
              messages.UrlMapTest(host='youtube.com',
                                  path='/watch/this',
                                  service=backend_services_prefix +
                                  'youtube-default'),
          ]),
      messages.UrlMap(
          name='url-map-2',
          defaultService=backend_services_prefix + 'default-service',
          hostRules=[
              messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                       '*-youtube.com'],
                                pathMatcher='youtube'),
          ],
          pathMatchers=[
              messages.PathMatcher(
                  name='youtube',
                  defaultService=(backend_services_prefix +
                                  'youtube-default'),
                  pathRules=[
                      messages.PathRule(paths=['/search', '/search/*'],
                                        service=(
                                            backend_services_prefix +
                                            'youtube-search')),
                      messages.PathRule(paths=['/watch', '/view', '/preview'],
                                        service=(
                                            backend_services_prefix +
                                            'youtube-watch')),
                  ]),
          ],
          selfLink=(url_maps_prefix + 'url-map-2'),
          tests=[
              messages.UrlMapTest(host='youtube.com',
                                  path='/watch/this',
                                  service=backend_services_prefix +
                                  'youtube-default'),
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

URL_MAPS_ALPHA = MakeUrlMaps(messages, 'alpha')
URL_MAPS_BETA = MakeUrlMaps(messages, 'beta')
URL_MAPS = MakeUrlMaps(messages, 'v1')


def MakeVpnTunnels(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  region1 = prefix + '/projects/my-project/regions/region-1'
  region2 = prefix + '/projects/my-project/regions/region-2'
  return [
      msgs.VpnTunnel(
          creationTimestamp='2011-11-11T17:54:10.636-07:00',
          description='the first tunnel',
          ikeVersion=1,
          name='tunnel-1',
          peerIp='1.1.1.1',
          region=region1,
          selfLink=region1 + '/vpnTunnels/tunnel-1',
          sharedSecretHash='ff33f3a693905de7e85178529e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region1 + '/targetVpnGateways/gateway-1'
      ),
      msgs.VpnTunnel(
          creationTimestamp='2022-22-22T17:54:10.636-07:00',
          description='the second tunnel',
          ikeVersion=2,
          name='tunnel-2',
          peerIp='2.2.2.2',
          region=region2,
          selfLink=region2 + '/vpnTunnels/tunnel-2',
          sharedSecretHash='2f23232623202de7e85178529e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region2 + '/targetVpnGateways/gateway-2'
      ),
      msgs.VpnTunnel(
          creationTimestamp='2033-33-33T17:54:10.636-07:00',
          description='the third tunnel',
          ikeVersion=2,
          name='tunnel-3',
          peerIp='3.3.3.3',
          region=region1,
          selfLink=region1 + '/vpnTunnels/tunnel-3',
          sharedSecretHash='3f33333633303de7e85178539e3a13feb85a3964',
          status=msgs.VpnTunnel.StatusValueValuesEnum.ESTABLISHED,
          targetVpnGateway=region1 + '/targetVpnGateways/gateway-3'
      )
  ]


VPN_TUNNELS_BETA = MakeVpnTunnels(beta_messages, 'beta')
VPN_TUNNELS_V1 = MakeVpnTunnels(beta_messages, 'v1')

ZONAL_OPERATIONS = [
    messages.Operation(
        name='operation-3',
        httpErrorStatusCode=409,
        operationType='insert',
        zone=('https://www.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1'),
        status=messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:56:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/zone-1/operations/operation-3'),
        targetLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                    'zones/zone-1/resource/resource-3')),
]

BETA_ZONAL_OPERATIONS = [
    beta_messages.Operation(
        name='operation-3',
        httpErrorStatusCode=409,
        operationType='insert',
        zone=('https://www.googleapis.com/compute/beta/projects/my-project/'
              'zones/zone-1'),
        status=beta_messages.Operation.StatusValueValuesEnum.DONE,
        insertTime='2014-09-04T09:56:33.679-07:00',
        selfLink=('https://www.googleapis.com/compute/beta/projects/'
                  'my-project/zones/zone-1/operations/operation-3'),
        targetLink=('https://www.googleapis.com/compute/beta/projects/'
                    'my-project/zones/zone-1/resource/resource-3')),
]

ZONES = [
    messages.Zone(
        name='us-central1-a',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        status=messages.Zone.StatusValueValuesEnum.UP,
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/us-central1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://www.googleapis.com/compute/v1/projects/'
                         'my-project/zones/us-central1-b'))),

    messages.Zone(
        name='us-central1-b',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/us-central1-b')),

    messages.Zone(
        name='europe-west1-a',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/europe-west1-a')),

    messages.Zone(
        name='europe-west1-b',
        status=messages.Zone.StatusValueValuesEnum.DOWN,
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'zones/europe-west1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DELETED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://www.googleapis.com/compute/v1/projects/'
                         'my-project/zones/europe-west1-a'))),
]

BETA_ZONES = [
    beta_messages.Zone(
        name='us-central1-a',
        region=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-a')),
    beta_messages.Zone(
        name='us-central1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-b')),
    beta_messages.Zone(
        name='europe-west1-a',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-a')),
    beta_messages.Zone(
        name='europe-west1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.DOWN,
        region=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-b')),
]

BETA_SUBNETWORKS = [
    beta_messages.Subnetwork(
        name='my-subnet1',
        network=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central1/subnetworks/my-subnet1'),
    ),
    beta_messages.Subnetwork(
        name='my-subnet2',
        network=(
            'https://www.googleapis.com/compute/beta/projects/my-project/'
            'global/networks/my-other-network'),
        ipCidrRange='10.0.0.0/24',
        region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central1/subnetworks/my-subnet2'),
    ),
]
