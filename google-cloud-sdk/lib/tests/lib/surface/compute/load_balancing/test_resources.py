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
"""Resources that are shared by two or more tests."""

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

TARGET_HTTP_PROXIES = [
    messages.TargetHttpProxy(
        name='target-http-proxy-1',
        description='My first proxy',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-1',
        selfLink=(_V1_URI_PREFIX +
                  'global/targetHttpProxies/target-http-proxy-1')),
    messages.TargetHttpProxy(
        name='target-http-proxy-2',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-2',
        selfLink=(_V1_URI_PREFIX +
                  'global/targetHttpProxies/target-http-proxy-2')),
    messages.TargetHttpProxy(
        name='target-http-proxy-3',
        description='My last proxy',
        urlMap=_V1_URI_PREFIX + 'global/urlMaps/url-map-3',
        selfLink=(_V1_URI_PREFIX +
                  'global/targetHttpProxies/target-http-proxy-3')),
]


def MakeTargetHttpProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetHttpProxy(
          name='target-http-proxy-1',
          description='My first proxy',
          urlMap=long_prefix + 'global/urlMaps/url-map-1',
          selfLink=(long_prefix +
                    'global/targetHttpProxies/target-http-proxy-1')),
      msgs.TargetHttpProxy(
          name='target-http-proxy-2',
          urlMap=long_prefix + 'global/urlMaps/url-map-2',
          selfLink=(long_prefix +
                    'global/targetHttpProxies/target-http-proxy-2')),
      msgs.TargetHttpProxy(
          name='target-http-proxy-3',
          description='My last proxy',
          urlMap=long_prefix + 'global/urlMaps/url-map-3',
          selfLink=(long_prefix +
                    'global/targetHttpProxies/target-http-proxy-3')),
  ]


TARGET_HTTP_PROXIES_ALPHA = MakeTargetHttpProxies(alpha_messages, 'alpha')
TARGET_HTTP_PROXIES_BETA = MakeTargetHttpProxies(beta_messages, 'beta')
TARGET_HTTP_PROXIES_V1 = MakeTargetHttpProxies(messages, 'v1')


def MakeTargetGrpcProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetGrpcProxy(
          name='target-grpc-proxy-1',
          description='My first proxy',
          urlMap=long_prefix + '/global/urlMaps/url-map-1',
          validateForProxyless=False,
          selfLink=(long_prefix +
                    '/global/targetGrpcProxies/target-grpc-proxy-1')),
      msgs.TargetGrpcProxy(
          name='target-grpc-proxy-2',
          urlMap=long_prefix + '/global/urlMaps/url-map-2',
          validateForProxyless=True,
          selfLink=(long_prefix +
                    '/global/targetGrpcProxies/target-grpc-proxy-2')),
      msgs.TargetGrpcProxy(
          name='target-grpc-proxy-3',
          description='My last proxy',
          urlMap=long_prefix + '/global/urlMaps/url-map-3',
          selfLink=(long_prefix +
                    '/global/targetGrpcProxies/target-grpc-proxy-3'))
  ]


TARGET_GRPC_PROXIES_ALPHA = MakeTargetGrpcProxies(alpha_messages, 'alpha')
TARGET_GRPC_PROXIES_BETA = MakeTargetGrpcProxies(alpha_messages, 'beta')
TARGET_GRPC_PROXIES_V1 = MakeTargetGrpcProxies(alpha_messages, 'v1')


def MakeTargetHttpsProxies(msgs, api):
  prefix = _COMPUTE_PATH + '/' + api
  long_prefix = prefix + '/projects/my-project'
  return [
      msgs.TargetHttpsProxy(
          name='target-https-proxy-1',
          description='My first proxy',
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-1'
                           ]),
          urlMap=long_prefix + '/global/urlMaps/url-map-1',
          selfLink=(long_prefix +
                    '/global/targetHttpsProxies/target-https-proxy-1')),
      msgs.TargetHttpsProxy(
          name='target-https-proxy-2',
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-2'
                           ]),
          urlMap=long_prefix + '/global/urlMaps/url-map-2',
          selfLink=(long_prefix +
                    '/global/targetHttpsProxies/target-https-proxy-2')),
      msgs.TargetHttpsProxy(
          name='target-https-proxy-3',
          description='My last proxy',
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-3'
                           ]),
          urlMap=long_prefix + '/global/urlMaps/url-map-3',
          selfLink=(long_prefix +
                    '/global/targetHttpsProxies/target-https-proxy-3'))
  ]


TARGET_HTTPS_PROXIES_ALPHA = MakeTargetHttpsProxies(alpha_messages, 'alpha')
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
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-1'
                           ])),
      msgs.TargetSslProxy(
          name='target-ssl-proxy-2',
          description='My other proxy',
          proxyHeader=msgs.TargetSslProxy.ProxyHeaderValueValuesEnum.NONE,
          service=(long_prefix + '/global/backendServices/my-service'),
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-2'
                           ])),
      msgs.TargetSslProxy(
          name='target-ssl-proxy-3',
          description='My other other proxy',
          service=(long_prefix + '/global/backendServices/my-service'),
          sslCertificates=([long_prefix + '/global/sslCertificates/ssl-cert-3'
                           ]))
  ]


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
          service=(long_prefix + '/global/backendServices/my-service'))
  ]


TARGET_TCP_PROXIES_V1 = MakeTargetTcpProxies(messages, 'v1')

TARGET_INSTANCES = [
    messages.TargetInstance(
        name='target-instance-1',
        instance=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/instances/instance-1'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/targetInstances/target-instance-1'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.TargetInstance(
        name='target-instance-2',
        instance=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/instances/instance-2'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-1/targetInstances/target-instance-2'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-1')),
    messages.TargetInstance(
        name='target-instance-3',
        instance=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-2/instances/instance-3'),
        natPolicy=messages.TargetInstance.NatPolicyValueValuesEnum.NO_NAT,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/zone-2/targetInstances/target-instance-3'),
        zone=('https://compute.googleapis.com/compute/v1/projects/my-project/'
              'zones/zone-2')),
]

TARGET_POOLS = [
    messages.TargetPool(
        backupPool=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-2'),
        name='pool-1',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-1'),
        sessionAffinity=(
            messages.TargetPool.SessionAffinityValueValuesEnum.CLIENT_IP)),
    messages.TargetPool(
        name='pool-2',
        healthChecks=([
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/httpHealthChecks/check-1',
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'global/httpHealthChecks/check-2'
        ]),
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-2'),
        sessionAffinity=(messages.TargetPool.SessionAffinityValueValuesEnum
                         .CLIENT_IP_PROTO)),
    messages.TargetPool(
        name='pool-3',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/region-1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1/targetPools/pool-3'),
        sessionAffinity=(
            messages.TargetPool.SessionAffinityValueValuesEnum.NONE))
]


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
          tunnels=[
              region2 + '/tunnels/tunnel-3', region2 + '/tunnels/tunnel-33'
          ])
  ]


TARGET_VPN_GATEWAYS_BETA = MakeTargetVpnGateways(beta_messages, 'beta')
TARGET_VPN_GATEWAYS_V1 = MakeTargetVpnGateways(beta_messages, 'v1')
