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

"""Tests for the backend services update-backend subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_services import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  m = test_obj.messages
  test_obj._utilization = m.Backend.BalancingModeValueValuesEnum.UTILIZATION
  test_obj._rate = m.Backend.BalancingModeValueValuesEnum.RATE
  test_obj._connection = m.Backend.BalancingModeValueValuesEnum.CONNECTION

  if api_version == 'v1':
    test_obj._backend_services = test_resources.BACKEND_SERVICES_V1
  elif api_version == 'beta':
    test_obj._backend_services = test_resources.BACKEND_SERVICES_BETA
  elif api_version == 'alpha':
    test_obj._backend_services = test_resources.BACKEND_SERVICES_ALPHA
  else:
    raise ValueError('bad api version: [{0}]'.format(api_version))


class BackendServicesUpdateBackendTest(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],
        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --region alaska
          --instance-group group-1
          --instance-group-zone zone-1
          --description "my new description"
        """)

    self.AssertErrNotContains('WARNING:')

  def testWithNoFlags(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of ([--instance-group : --instance-group-region | '
        '--instance-group-zone] | [--network-endpoint-group : '
        '--network-endpoint-group-zone]) must be specified.'):
      self.Run("""
          compute backend-services update-backend backend-service-2
          """)

    self.CheckRequests()

  def testWithNoMutationFlags(self):
    with self.AssertRaisesToolExceptionRegexp(
        'At least one property must be modified.'):
      self.Run("""
          compute backend-services update-backend backend-service-2
            --instance-group group-1
            --instance-group-zone zone-1
          """)

    self.CheckRequests()

  def testWithNonExistentGroup(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'No backend with name \[group-3\] in zone \[zone-3\] is part of the '
        r'backend service \[backend-service-2\].'):
      self.Run("""
          compute backend-services update-backend backend-service-2
            --instance-group group-3
            --instance-group-zone zone-3
            --max-rate 1
            --global
          """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
    )

  def testRegionalWithNewDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --region alaska
          --instance-group group-1
          --instance-group-zone zone-1
          --description "my new description"
        """)

    self.CheckRequests(
        [(self.compute.regionBackendServices,
          'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              backendService='backend-service-2',
              region='alaska',
              project='my-project'))],
        [(self.compute.regionBackendServices,
          'Update',
          messages.ComputeRegionBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='my new description',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              region='alaska',
              project='my-project'))],
    )

  def testWithDescriptionRemoval(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --description ""
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeBeingChangedToUtilization(self):
    self.templateTestWithBalancingModeBeingChangedToUtilization("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --balancing-mode UTILIZATION
          --max-utilization 1.0
          --global
        """)

  def testWithBalancingModeBeingChangedToUtilizationLowerCase(self):
    self.templateTestWithBalancingModeBeingChangedToUtilization("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --balancing-mode utilization
          --max-utilization 1.0
          --global
        """)

  def templateTestWithBalancingModeBeingChangedToUtilization(self, cmd):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run(cmd)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          # maxRate can still be set if using
                          # UTILIZATION.
                          maxRate=100,
                          maxUtilization=1.0),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeBeingChangedToRate(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-2
          --instance-group-zone zone-2
          --balancing-mode RATE
          --max-rate 100
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxRate=100),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithMaxUtilization(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-2
          --instance-group-zone zone-2
          --max-utilization 0.5
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=0.5),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithMaxRatePerInstance(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --max-rate-per-instance 1000
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRatePerInstance=1000.0),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeConnectionsBeingChangedToUtilization(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[4]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-tcp
          --instance-group group-1
          --instance-group-zone zone-1
          --balancing-mode UTILIZATION
          --max-utilization 0.3
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-tcp',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-tcp',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxUtilization=0.3,
                          # maxConnections is allowed with UTILIZATION.
                          maxConnectionsPerInstance=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0,
                          maxConnections=10),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='backend-service-tcp',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.TCP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-tcp'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeUtilizationBeingChangedToConnection(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-2
          --instance-group-zone zone-2
          --balancing-mode CONNECTION
          --max-connections 200
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._connection,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxConnections=200),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeConnectionsBeingChangedToRate(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[4]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-tcp
          --instance-group group-1
          --instance-group-zone zone-1
          --balancing-mode RATE
          --max-rate 230
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-tcp',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-tcp',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=230),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0,
                          maxConnections=10),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='backend-service-tcp',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.TCP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-tcp'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeRateBeingChangedToConnection(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --balancing-mode CONNECTION
          --max-connections-per-instance 200
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxConnectionsPerInstance=200),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithMaxConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[4]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-tcp
          --instance-group group-1
          --instance-group-zone zone-1
          --max-connections 40
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-tcp',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-tcp',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxConnections=40),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0,
                          maxConnections=10),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='backend-service-tcp',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.TCP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-tcp'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testRateWithMaxConnections(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-connections.*cannot be set with RATE balancing mode'):
      self.Run("""
          compute backend-services update-backend backend-service-2
            --instance-group group-1
            --instance-group-zone zone-1
            --max-connections 1000
            --global
          """)

  def testConnectionWithMaxRate(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[4]],

        [],
    ])

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        '.*--max-rate.*cannot be set with CONNECTION balancing mode'):
      self.Run("""
          compute backend-services update-backend backend-service-tcp
            --instance-group group-1
            --instance-group-zone zone-1
            --max-rate 40
            --global
          """)

  def testWithCapacityScaler(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --capacity-scaler 0
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          capacityScaler=0.0,
                          description='group one',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'instanceGroups/group-2'),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithFailover(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --failover
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='backend-service-2', project='my-project'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='backend-service-2',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          failover=True,
                          description='group one',
                          group=self.resources.Create(
                              'compute.instanceGroups',
                              instanceGroup='group-1',
                              project='my-project',
                              zone='zone-1').SelfLink(),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=self.resources.Create(
                              'compute.instanceGroups',
                              instanceGroup='group-2',
                              project='my-project',
                              zone='zone-2').SelfLink(),
                          maxUtilization=1.0),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='backend-service-2',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'backend-service-2'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithNewDescriptionZonalIG(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[2]],
        [],
    ])

    self.Run("""
        compute backend-services update-backend instance-group-service
          --instance-group group-1
          --instance-group-zone zone-1
          --description "my new description"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='instance-group-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='instance-group-service',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='my new description',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/zones/'
                              'zone-1/instanceGroups/group-1'),
                          maxRate=100),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='instance-group-service',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'instance-group-service'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithNewDescriptionRegionalIG(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[3]],
        [],
    ])

    self.Run("""
        compute backend-services update-backend regional-instance-group-service
          --instance-group group-1
          --instance-group-region region-1
          --description "my new description"
          --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='regional-instance-group-service',
              project='my-project'))],
        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              backendService='regional-instance-group-service',
              backendServiceResource=messages.BackendService(
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='my new description',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/regions/'
                              'region-1/instanceGroups/group-1'),
                          maxRate=100),
                  ],
                  healthChecks=[
                      (self.compute_uri + '/projects/'
                       'my-project/global/httpHealthChecks/my-health-check')
                  ],
                  name='regional-instance-group-service',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/'
                            'my-project/global/backendServices/'
                            'regional-instance-group-service'),
                  timeoutSec=30),
              project='my-project'))],
    )


class BackendServicesUpdateBackendWithNEGTest(test_base.BaseTest,
                                              parameterized.TestCase):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.backend_service = self.messages.BackendService(
        backends=[
            self.messages.Backend(
                balancingMode=self._connection,
                description='max connections',
                group=(
                    'https://compute.googleapis.com/compute/'
                    'alpha/projects/my-project/zones/zone-1/'
                    'networkEndpointGroups/neg-1'),
                maxConnectionsPerEndpoint=100),
            self.messages.Backend(
                balancingMode=self._rate,
                description='max connections',
                group=(
                    'https://compute.googleapis.com/compute/'
                    'alpha/projects/my-project/zones/zone-2/'
                    'networkEndpointGroups/neg-2'),
                maxRatePerEndpoint=0.9),
            self.messages.Backend(
                balancingMode=self._utilization,
                description='utilziation with conneciton',
                group=(
                    'https://compute.googleapis.com/compute/'
                    'alpha/projects/my-project/zones/zone-1/'
                    'instanceGroups/ig-1'),
                maxUtilization=1.0,
                maxConnections=10),
        ],
        healthChecks=[
            ('https://compute.googleapis.com/compute/alpha/projects/'
             'my-project/global/healthChecks/my-health-check')
        ],
        name='my-backend-service',
        portName='http',
        protocol=self.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=(self.compute_uri + '/projects/my-project'
                  '/global/backendServices/my-backend-service'),
        timeoutSec=30)

  def testUtilizationBalancingModeIncompatibleWithNeg(self):
    self.make_requests.side_effect = iter([
        [self.backend_service],
        [],
    ])
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--network-endpoint-group]: cannot be set with '
        'UTILIZATION balancing mode'):
      self.Run("""
          compute backend-services update-backend my-backend-service
            --network-endpoint-group neg-1
            --network-endpoint-group-zone zone-1
            --balancing-mode UTILIZATION
            --global
          """)

  def testInstanceGroupAndNetworkEndpointGroupMutualExclusion(self):
    self.make_requests.side_effect = iter([
        [self.backend_service],
        [],
    ])
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of ([--instance-group : --instance-group-region | '
        '--instance-group-zone] | [--network-endpoint-group : '
        '--network-endpoint-group-zone]) must be specified.'):
      self.Run("""
          compute backend-services update-backend my-backend-service
            --network-endpoint-group neg-2
            --network-endpoint-group-zone zone-1
            --instance-group my-group
            --instance-group-zone us-central1-f
            --balancing-mode CONNECTION
            --max-connections 100
            --global
          """)

  @parameterized.parameters(
      ('--network-endpoint-group', 'neg-1', 'CONNECTION',
       '--max-connections-per-instance'),
      ('--network-endpoint-group', 'neg-1', 'RATE', '--max-rate-per-instance'),
      ('--instance-group', 'ig-1', 'CONNECTION',
       '--max-connections-per-endpoint'),
      ('--instance-group', 'ig-1', 'RATE', '--max-rate-per-endpoint'),)
  def testGroupResourceMatchesFlags(self, group_flag, resource_name,
                                    balancing_mode, incomptaible_flag):
    self.make_requests.side_effect = iter([
        [self.backend_service],
        [],
    ])
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [{0}]: cannot be set with {1}'.format(
            incomptaible_flag, group_flag)):
      self.Run("""
          compute backend-services update-backend my-backend-service
            {0} {1}
            {0}-zone zone-1
            --balancing-mode {2}
            {3} 100
            --global
          """.format(
              group_flag, resource_name, balancing_mode, incomptaible_flag))

  def testWithBalancingModeConnectionsBeingChangedToRate(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.backend_service],
        [],
    ])

    self.Run("""
        compute backend-services update-backend my-backend-service
          --network-endpoint-group neg-1
          --network-endpoint-group-zone zone-1
          --balancing-mode RATE
          --max-rate-per-endpoint 230
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
                  backends=[
                      messages.Backend(
                          balancingMode=self._rate,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'networkEndpointGroups/neg-1'),
                          maxRatePerEndpoint=230),
                      messages.Backend(
                          balancingMode=self._rate,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'networkEndpointGroups/neg-2'),
                          maxRatePerEndpoint=0.9),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/ig-1'),
                          maxUtilization=1.0,
                          maxConnections=10),
                  ],
                  healthChecks=[
                      ('https://compute.googleapis.com/compute/alpha/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/my-project'
                            '/global/backendServices/my-backend-service'),
                  timeoutSec=30),
              project='my-project'))],
    )

  def testWithBalancingModeRateBeingChangedToConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self.backend_service],
        [],
    ])

    self.Run("""
        compute backend-services update-backend my-backend-service
          --network-endpoint-group neg-2
          --network-endpoint-group-zone zone-2
          --balancing-mode CONNECTION
          --max-connections-per-endpoint 320
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
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'networkEndpointGroups/neg-1'),
                          maxConnectionsPerEndpoint=100),
                      messages.Backend(
                          balancingMode=self._connection,
                          description='max connections',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-2/'
                              'networkEndpointGroups/neg-2'),
                          maxConnectionsPerEndpoint=320),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              'https://compute.googleapis.com/compute/'
                              'alpha/projects/my-project/zones/zone-1/'
                              'instanceGroups/ig-1'),
                          maxUtilization=1.0,
                          maxConnections=10),
                  ],
                  healthChecks=[
                      ('https://compute.googleapis.com/compute/alpha/projects/'
                       'my-project/global/healthChecks/my-health-check')
                  ],
                  name='my-backend-service',
                  portName='http',
                  protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
                  selfLink=(self.compute_uri + '/projects/my-project'
                            '/global/backendServices/my-backend-service'),
                  timeoutSec=30),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
