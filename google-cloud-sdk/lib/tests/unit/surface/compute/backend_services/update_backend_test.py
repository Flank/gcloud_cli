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
"""Tests for the backend services update-backend subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  m = test_obj.messages
  test_obj._utilization = m.Backend.BalancingModeValueValuesEnum.UTILIZATION
  test_obj._rate = m.Backend.BalancingModeValueValuesEnum.RATE
  test_obj._connection = m.Backend.BalancingModeValueValuesEnum.CONNECTION

  if api_version == 'v1':
    test_obj._backend_services = test_resources.BACKEND_SERVICES_V1
  else:
    raise ValueError('bad api version: [{0}]'.format(api_version))


class BackendServicesUpdateBackendTest(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')

  def testScopeWarning(self):
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],
        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --description "my new description"
          --global
        """)

    self.AssertErrNotContains('WARNING:')

  def testWithNoFlags(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --instance-group: Must be specified.'
        ):
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

  def testWithNewDescription(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [self._backend_services[1]],

        [],
    ])

    self.Run("""
        compute backend-services update-backend backend-service-2
          --instance-group group-1
          --instance-group-zone zone-1
          --description "my new description"
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
                          description='my new description',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          # maxRate can still be set if using
                          # UTILIZATION.
                          maxRate=100,
                          maxUtilization=1.0),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._rate,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRatePerInstance=1000.0),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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

  def testWithNewDescriptionIG(self):
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
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/zone-1/'
                                 'instanceGroups/group-1'),
                          maxUtilization=0.3,
                          # maxConnections is allowed with UTILIZATION.
                          maxConnectionsPerInstance=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/zone-2/'
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
                              self.compute_uri +
                              '/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._connection,
                          description='group two',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/zones/zone-2/'
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
                              self.compute_uri +
                              '/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=230),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/zones/zone-2/'
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
                              self.compute_uri +
                              '/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxConnectionsPerInstance=200),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/zones/zone-2/'
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
                              self.compute_uri +
                              '/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxConnections=40),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='utilziation with conneciton',
                          group=(
                              self.compute_uri +
                              '/projects/my-project/zones/zone-2/'
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
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-1/'
                              'instanceGroups/group-1'),
                          maxRate=100),
                      messages.Backend(
                          balancingMode=self._utilization,
                          description='group two',
                          group=(
                              'https://www.googleapis.com/compute/'
                              'v1/projects/my-project/zones/zone-2/'
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


if __name__ == '__main__':
  test_case.main()
