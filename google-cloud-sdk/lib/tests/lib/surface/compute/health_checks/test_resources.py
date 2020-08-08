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
"""Resources that are shared by two or more health check tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


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
              proxyHeader=(
                  msgs.HTTPHealthCheck.ProxyHeaderValueValuesEnum.PROXY_V1)),
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
              proxyHeader=(
                  msgs.HTTPSHealthCheck.ProxyHeaderValueValuesEnum.PROXY_V1)),
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
              proxyHeader=(
                  msgs.SSLHealthCheck.ProxyHeaderValueValuesEnum.PROXY_V1)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-ssl')),
      msgs.HealthCheck(
          name='health-check-http2',
          type=msgs.HealthCheck.TypeValueValuesEnum.HTTP2,
          http2HealthCheck=msgs.HTTP2HealthCheck(
              host='www.example.com',
              port=443,
              portName='happy-http2-port',
              requestPath='/',
              proxyHeader=(
                  msgs.HTTP2HealthCheck.ProxyHeaderValueValuesEnum.PROXY_V1)),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-http2')),
      msgs.HealthCheck(
          name='health-check-grpc',
          type=msgs.HealthCheck.TypeValueValuesEnum.GRPC,
          grpcHealthCheck=msgs.GRPCHealthCheck(
              port=88, grpcServiceName='gRPC-service'),
          selfLink=(prefix + '/projects/'
                    'my-project/global/healthChecks/health-check-grpc'))
  ]


def MakeHealthCheckBeta(msgs, api):
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
HEALTH_CHECKS_BETA = MakeHealthCheckBeta(beta_messages, 'beta')

HTTP_HEALTH_CHECKS = [
    messages.HttpHealthCheck(
        name='health-check-1',
        host='www.example.com',
        port=8080,
        requestPath='/testpath',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/httpHealthChecks/health-check-1')),
    messages.HttpHealthCheck(
        name='health-check-2',
        port=80,
        requestPath='/',
        selfLink=('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/global/httpHealthChecks/health-check-2')),
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


HTTPS_HEALTH_CHECKS_V1 = MakeHttpsHealthChecks(messages, 'v1')
HTTPS_HEALTH_CHECKS_BETA = MakeHttpsHealthChecks(beta_messages, 'beta')
