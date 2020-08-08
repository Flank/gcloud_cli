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
"""Tests for the backend services create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute.backend_services.create import test_base


class WithSessionAffinityApiTest(test_base.BackendServiceCreateTestBase):

  # Modify the session affinity map.
  def _ModifySessionAffinityMap(self, session_affinity_map, messages):
    pass

  # Tests that default settings are applied to affinity and cookie TTL
  # if not specified
  def testDefault(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30),
            project='my-project'))],)

  # Test setting client IP-based affinity
  def testClientIp(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity client_ip
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .CLIENT_IP)),
            project='my-project'))],)

  # Test setting generated cookie affinity with the default TTL (0)
  def testGeneratedCookieNoTtl(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity generated_cookie
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .GENERATED_COOKIE)),
            project='my-project'))],)

  # Test setting generated cookie affinity with a specific TTL
  def testGeneratedCookieWithTtl(self):
    messages = self.messages

    self.Run("""
        compute backend-services create my-backend-service
          --http-health-checks my-health-check-1
          --description "My backend service"
          --session-affinity generated_cookie
          --affinity-cookie-ttl 18
          --global
        """)

    self.CheckRequests([(
        self.compute.backendServices, 'Insert',
        messages.ComputeBackendServicesInsertRequest(
            backendService=messages.BackendService(
                backends=[],
                description='My backend service',
                healthChecks=[
                    (self.compute_uri + '/projects/'
                     'my-project/global/httpHealthChecks/my-health-check-1'),
                ],
                name='my-backend-service',
                portName='http',
                protocol=(messages.BackendService.ProtocolValueValuesEnum.HTTP),
                timeoutSec=30,
                sessionAffinity=
                (messages.BackendService.SessionAffinityValueValuesEnum
                 .GENERATED_COOKIE),
                affinityCookieTtlSec=18),
            project='my-project'))],)

  def testSetIlbSessionAffinity_ClientIpProto(self):
    self._TestSetILBSessionAffinity('client_ip_proto')

  def testSetIlbSessionAffinity_ClientIpPortProto(self):
    self._TestSetILBSessionAffinity('client_ip_port_proto')

  # Test ilb setting all supported session affinitys.
  def _TestSetILBSessionAffinity(self,
                                 session_affiniy,
                                 specify_global_health_check=True):
    messages = self.messages
    session_affinity_map = {
        'none':
            messages.BackendService.SessionAffinityValueValuesEnum.NONE,
        'client_ip':
            messages.BackendService.SessionAffinityValueValuesEnum.CLIENT_IP,
        'client_ip_proto':
            messages.BackendService.SessionAffinityValueValuesEnum
            .CLIENT_IP_PROTO,
        'client_ip_port_proto':
            messages.BackendService.SessionAffinityValueValuesEnum
            .CLIENT_IP_PORT_PROTO
    }
    self._ModifySessionAffinityMap(session_affinity_map, messages)

    self.Run("""compute backend-services create my-backend-service
        --health-checks=my-health-check-1
        --protocol=TCP
        --load-balancing-scheme=internal
        --description "My backend service"
        --region=alaska
        %s
        --session-affinity %s
        """ % ('--global-health-checks'
               if specify_global_health_check else '', session_affiniy))

    self.CheckRequests([
        (self.compute.regionBackendServices, 'Insert',
         messages.ComputeRegionBackendServicesInsertRequest(
             backendService=messages.BackendService(
                 backends=[],
                 description='My backend service',
                 loadBalancingScheme=(
                     messages.BackendService.LoadBalancingSchemeValueValuesEnum.
                     INTERNAL),
                 healthChecks=[
                     (self.compute_uri + '/projects/'
                      'my-project/global/healthChecks/my-health-check-1')
                 ],
                 name='my-backend-service',
                 protocol=(messages.BackendService.ProtocolValueValuesEnum.TCP),
                 timeoutSec=30,
                 sessionAffinity=session_affinity_map[session_affiniy]),
             region='alaska',
             project='my-project'))
    ],)


class WithSessionAffinityApiBetaTest(WithSessionAffinityApiTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.BETA)


class WithSessionAffinityApiAlphaTest(WithSessionAffinityApiBetaTest):

  def SetUp(self):
    self._SetUp(calliope_base.ReleaseTrack.ALPHA)

  def _ModifySessionAffinityMap(self, session_affinity_map, messages):
    session_affinity_map['client_ip_no_destination'] = (
        messages.BackendService.SessionAffinityValueValuesEnum
        .CLIENT_IP_NO_DESTINATION)

  def testSetIlbSessionAffinity_ClientIpPortProto(self):
    self._TestSetILBSessionAffinity('client_ip_no_destination')


if __name__ == '__main__':
  test_case.main()
