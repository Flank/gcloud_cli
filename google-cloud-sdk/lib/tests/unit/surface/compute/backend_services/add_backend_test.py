# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the backend services add-backend subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  m = test_obj.messages
  test_obj._utilization = m.Backend.BalancingModeValueValuesEnum.UTILIZATION
  test_obj._rate = m.Backend.BalancingModeValueValuesEnum.RATE
  test_obj._connection = m.Backend.BalancingModeValueValuesEnum.CONNECTION


class BackendServiceAddBackendTest(test_base.BaseTest, parameterized.TestCase):

  def SetUp(self):
    SetUp(self, 'v1')

  def testScopeWarning(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --global
        """)
    self.AssertErrNotContains('WARNING:')

  def testWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=('https://compute.googleapis.com/compute/'
                           'v1/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=('https://compute.googleapis.com/compute/'
                           'v1/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group-3 --instance-group-zone us-central1-a
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-1')),
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-2')),
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-3')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithDuplicateZonalBackend(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=('https://compute.googleapis.com/compute/'
                           'v1/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Backend \[my-group\] in zone \[us-central1-a\] already exists in '
        r'backend service \[my-backend-service\].'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --global
          """)

  def testWithDuplicateRegionalBackend(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=('https://compute.googleapis.com/compute/'
                           'v1/projects/my-project/regions/'
                           'us-central1/instanceGroups/my-group')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ]

    with self.AssertRaisesToolExceptionRegexp(
        r'Backend \[my-group\] in region \[us-central1\] already exists in '
        r'backend service \[my-backend-service\].'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-region us-central1
            --global
          """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
    )

  def testWithDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --description "Hello, world!"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          description='Hello, world!',
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithUtilizationBalancingMode(self):
    self.templateTestWithUtilizationBalancingMode("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode UTILIZATION
          --max-utilization 1.0
          --global
        """)

  def testWithUtilizationBalancingModeLowerCase(self):
    self.templateTestWithUtilizationBalancingMode("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode utilization
          --max-utilization 1.0
          --global
        """)

  def templateTestWithUtilizationBalancingMode(self, cmd):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run(cmd)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxUtilization=1.0),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithRateBalancingModeAndMaxRate(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode RATE
          --max-rate 100
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxRate=100),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  @parameterized.parameters(
      ('--instance-group', 'instance', 'instanceGroups'),
      ('--network-endpoint-group', 'endpoint', 'networkEndpointGroups'))
  def testWithRateBalancingModeAndMaxRatePerInstance(self, flag_base,
                                                     rate_flag_suffix,
                                                     resource_type):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          {0} my-group
          {0}-zone us-central1-a
          --balancing-mode RATE
          --max-rate-per-{1} 0.9
          --global
        """.format(flag_base, rate_flag_suffix))

    backend = messages.Backend(
        balancingMode=self._rate,
        group=('https://compute.googleapis.com/compute/v1/projects/my-project/'
               'zones/us-central1-a/{}/my-group'.format(resource_type)))
    if rate_flag_suffix == 'instance':
      backend.maxRatePerInstance = 0.9
    elif rate_flag_suffix == 'endpoint':
      backend.maxRatePerEndpoint = 0.9
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[backend],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testMaxRateAndMaxRatePerInstanceMutualExclusion(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=('https://compute.googleapis.com/compute/'
                           'v1/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --max-rate: At most one of --max-connections | '
        '--max-connections-per-endpoint | --max-connections-per-instance | '
        '--max-rate | --max-rate-per-endpoint | '
        '--max-rate-per-instance may be specified.'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode RATE
            --max-rate 100
            --max-rate-per-instance 0.9
          """)
    self.CheckRequests()

  def testWithCapacityScaler(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --capacity-scaler 0.0
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          capacityScaler=0.0,
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )
    self.AssertErrNotContains('WARNING: ')

  def testUriSupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend
          {uri}/projects/my-project/global/backendServices/my-backend-service
          --instance-group https://compute.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instanceGroups/my-group
          --global
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testUriSupportWithProjectsContainingColons(self):
    messages = self.messages
    properties.VALUES.core.project.Set('google.com:my-project')
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend
          {compute_uri}/projects/google.com:my-project/global/backendServices/my-backend-service
          --instance-group https://compute.googleapis.com/compute/v1/projects/google.com:my-project/zones/us-central1-a/instanceGroups/my-group
          --global
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='google.com:my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/google.com:my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='google.com:my-project'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],

        # Note that prompting is done after the backend service has
        # been fetched. This is intentional. We only want to prompt if
        # the backend service actually exists, otherwise the user is
        # burdened with prompting friction if he or she refers to a
        # non-existent backend service.
        [
            messages.Region(name='us-central1'),
            messages.Region(name='us-east1'),
        ],
        [
            messages.Zone(name='us-central1-a'),
            messages.Zone(name='us-central1-b'),
            messages.Zone(name='us-central2-a'),
        ],
        [],
    ])
    self.WriteInput('3\n')

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group-1
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],

        self.regions_list_request,
        self.zones_list_request,

        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-1')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

    self.AssertErrContains('my-group-1')
    self.AssertErrContains('us-central1-a')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('us-central2-a')

  def testInstanceGroupsWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testInstanceGroupsURISupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group {0}/projects/my-project/zones/us-central1-a/instanceGroups/my-group
          --instance-group-zone us-central1-a
          --global
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithConnectionBalancingModeAndMaxConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode CONNECTION
          --max-connections 100
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxConnections=100),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  @parameterized.parameters(
      ('--instance-group', 'instance', 'instanceGroups'),
      ('--network-endpoint-group', 'endpoint', 'networkEndpointGroups'))
  def testWithConnectionBalancingModeAndMaxConnectionsPerInstance(
      self, flag_base, rate_flag_suffix, resource_type):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          {0} my-group {0}-zone us-central1-a
          --balancing-mode CONNECTION
          --max-connections-per-{1} 5
          --global
        """.format(flag_base, rate_flag_suffix))

    backend = messages.Backend(
        balancingMode=self._connection,
        group=('https://compute.googleapis.com/compute/v1/projects/my-project/'
               'zones/us-central1-a/{}/my-group'.format(resource_type)))
    if rate_flag_suffix == 'instance':
      backend.maxConnectionsPerInstance = 5
    elif rate_flag_suffix == 'endpoint':
      backend.maxConnectionsPerEndpoint = 5
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[backend],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testMaxConnectionsAndMaxConnectionsPerInstanceMutualExclusion(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --max-connections: At most one of --max-connections | '
        '--max-connections-per-endpoint | --max-connections-per-instance | '
        '--max-rate | --max-rate-per-endpoint | '
        '--max-rate-per-instance may be specified.'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-f
            --balancing-mode CONNECTION
            --max-connections 100
            --max-connections-per-instance 5
          """)
    self.CheckRequests()

  def testWithRateBalancingModeAndMaxConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-connections.*cannot be set with RATE balancing mode'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode RATE
            --max-connections 100
            --global
          """)

  def testWithRateBalancingModeAndMaxUtilization(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-utilization.*cannot be set with RATE balancing mode'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode RATE
            --max-utilization 0.5
            --global
          """)

  def testWithConnectionBalancingModeAndMaxRatePerInstance(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-rate-per-instance.*cannot be set with CONNECTION'
        ' balancing mode'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode CONNECTION
            --max-rate-per-instance 0.9
            --global
          """)

  def testWithConnectionBalancingModeAndMaxUtilization(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-utilization.*cannot be set with CONNECTION balancing mode'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode CONNECTION
            --max-utilization 0.4
            --global
          """)

  def testWithUtilizationBalancingModeAndMaxRatePerInstance(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode UTILIZATION
          --max-rate-per-instance 0.5
          --max-utilization 0.7
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxRatePerInstance=0.5,
                          maxUtilization=0.7),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithUtilizationBalancingModeAndMaxConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode UTILIZATION
          --max-connections 200
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxConnections=200),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithUtilizationBalancingModeAndMaxConnectionsAndMaxRate(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'At most one of --max-connections | --max-connections-per-endpoint | '
        '--max-connections-per-instance | --max-rate | --max-rate-per-endpoint '
        '| --max-rate-per-instance may be specified.'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode UTILIZATION
            --max-connections 200
            --max-rate 20
          """)

  def testUtilizationBalancingModeIncompatibleWithNeg(self):
    messages = self.messages
    self.make_requests.side_effect = iter([[
        messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)
    ]])
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--network-endpoint-group]: cannot be set with '
        'UTILIZATION balancing mode'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --network-endpoint-group my-group
            --network-endpoint-group-zone us-central1-a
            --balancing-mode UTILIZATION
            --max-connections 100
            --global
          """)

  def testInstanceGroupAndNetworkEndpointGroupMutualExclusion(self):
    messages = self.messages
    self.make_requests.side_effect = iter([[
        messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)
    ]])
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of ([--instance-group : --instance-group-region | '
        '--instance-group-zone] | [--network-endpoint-group : '
        '--global-network-endpoint-group | --network-endpoint-group-region | '
        '--network-endpoint-group-zone]) must be specified.'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --network-endpoint-group my-group
            --network-endpoint-group-zone us-central1-a
            --instance-group my-group
            --instance-group-zone us-central1-f
            --balancing-mode CONNECTION
            --max-connections 100
            --global
          """)

  @parameterized.parameters(
      ('--network-endpoint-group', 'CONNECTION',
       '--max-connections-per-instance'),
      ('--network-endpoint-group', 'RATE', '--max-rate-per-instance'),
      ('--instance-group', 'CONNECTION', '--max-connections-per-endpoint'),
      ('--instance-group', 'RATE', '--max-rate-per-endpoint'),
  )
  def testGroupResourceMatchesFlags(self, group_flag, balancing_mode,
                                    incompatible_flag):
    messages = self.messages
    self.make_requests.side_effect = iter([[
        messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)
    ]])
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [{0}]: cannot be set with {1}'.format(
            incompatible_flag, group_flag)):
      self.Run("""
          compute backend-services add-backend my-backend-service
            {0} my-group
            {0}-zone us-central1-a
            --balancing-mode {1}
            {2} 100
            --global
          """.format(group_flag, balancing_mode, incompatible_flag))

  def testWithFailover(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group
          --instance-group-zone us-central1-a
          --failover
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          failover=True,
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                      ),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )


class BackendServiceAddBackendRegionalInstanceGroupTest(test_base.BaseTest):

  def testInstanceGroupsWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/old-group')),
            ],
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-region us-central1
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/old-group')),
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/regions/'
                                 'us-central1/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testInstanceGroupsURISupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group {0}/projects/my-project/regions/us-central1/instanceGroups/my-group
          --global
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/regions/'
                                 'us-central1/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testInstanceGroupsWithScopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central1-a'),
            self.messages.Zone(name='us-central1-b'),
            self.messages.Zone(name='us-central2-a'),
        ],
        [],
    ])

    self.WriteInput('2\n')
    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/regions/'
                                 'us-central2/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testRegionScopeWarning(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --region alaska
          --instance-group my-group --instance-group-zone us-central1-a
        """)
    self.AssertErrNotContains('WARNING:')

  def testRegionWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint=b'my-fingerprint',
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --region alaska
          --instance-group my-group --instance-group-zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute.regionBackendServices,
          'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project',
              region='alaska'))],
        [(self.compute.regionBackendServices,
          'Update',
          messages.ComputeRegionBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://compute.googleapis.com/compute/'
                                 'v1/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project',
              region='alaska'))],
    )


class BackendServiceAddBackendGlobalNetworkEndpointGroupTest(
    test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testAddGlobalNetworkEndpointGroup(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.BackendService(
                name='my-backend-service',
                fingerprint=b'my-fingerprint',
                port=80,
                timeoutSec=120)
        ],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --global-network-endpoint-group
          --network-endpoint-group my-group
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/global'
                                 '/networkEndpointGroups/my-group')),
                  ],
                  healthChecks=[],
                  timeoutSec=120),
              project='my-project'))],
    )


class BackendServiceAddBackendRegionNetworkEndpointGroupTest(
    test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testAddRegionalNetworkEndpointGroup(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.BackendService(
                name='my-backend-service',
                fingerprint=b'my-fingerprint',
                port=80,
                timeoutSec=120)
        ],
        [],
    ])

    self.Run('compute backend-services add-backend my-backend-service '
             '--network-endpoint-group-region us-central1 '
             '--network-endpoint-group my-serverless-neg --global')

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='my-backend-service',
              backendServiceResource=messages.BackendService(
                  name='my-backend-service',
                  port=80,
                  fingerprint=b'my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/regions/us-central1'
                                 '/networkEndpointGroups/my-serverless-neg')),
                  ],
                  healthChecks=[],
                  timeoutSec=120),
              project='my-project'))])


if __name__ == '__main__':
  test_case.main()
