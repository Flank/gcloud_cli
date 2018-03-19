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
"""Tests for the backend services add-backend subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)
  m = test_obj.messages
  test_obj._utilization = m.Backend.BalancingModeValueValuesEnum.UTILIZATION
  test_obj._rate = m.Backend.BalancingModeValueValuesEnum.RATE
  test_obj._connection = m.Backend.BalancingModeValueValuesEnum.CONNECTION


class BackendServiceAddBackendBetaTest(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testScopeWarning(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint='my-fingerprint',
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

  def testWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=('https://www.googleapis.com/compute/'
                                 'beta/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project',
              region='alaska'))],
    )

  def testWithConnectionBalancingModeAndMaxConnections(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          group=('https://www.googleapis.com/compute/'
                                 'beta/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxConnections=100),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithConnectionBalancingModeAndMaxConnectionsPerInstance(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            port=80,
            fingerprint='my-fingerprint',
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --instance-group my-group --instance-group-zone us-central1-a
          --balancing-mode CONNECTION
          --max-connections-per-instance 5
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._connection,
                          group=('https://www.googleapis.com/compute/'
                                 'beta/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group'),
                          maxConnectionsPerInstance=5),
                  ],
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
                    group=('https://www.googleapis.com/compute/'
                           'beta/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group')),
            ],
            port=80,
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesArgumentErrorRegexp(
        'argument --max-connections-per-instance: At most one of --max-rate | '
        '--max-rate-per-instance | --max-connections | '
        '--max-connections-per-instance may be specified.'
        ):
      self.Run("""
          compute backend-services add-backend my-backend-service
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
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegexp(
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
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegexp(
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
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegexp(
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
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.assertRaisesRegexp(
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
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          group=('https://www.googleapis.com/compute/'
                                 'beta/projects/my-project/zones/'
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
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          balancingMode=self._utilization,
                          group=('https://www.googleapis.com/compute/'
                                 'beta/projects/my-project/zones/'
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
            fingerprint='my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesArgumentErrorMatches(
        'argument --max-connections: At most one of --max-connections | '
        '--max-connections-per-instance | --max-rate | --max-rate-per-instance '
        'may be specified.'):
      self.Run("""
          compute backend-services add-backend my-backend-service
            --instance-group my-group --instance-group-zone us-central1-a
            --balancing-mode UTILIZATION
            --max-connections 200
            --max-rate 20
          """)


class BackendServiceAddBackendRegionalInstanceGroupTest(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testInstanceGroupsWithNoExistingBackends(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
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

  def testInstanceGroupsWithNoExistingBackendsAndRegionalService(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint='my-fingerprint',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/old-group')),
            ],
            port=80,
            timeoutSec=120)],
        [],
    ])

    self.Run("""
        compute backend-services add-backend my-backend-service
          --region alaska
          --instance-group my-group --instance-group-region us-central1
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
                  fingerprint='my-fingerprint',
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
              project='my-project',
              region='alaska'))],
    )

  def testInstanceGroupsURISupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
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
            fingerprint='my-fingerprint',
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
                  fingerprint='my-fingerprint',
                  backends=[
                      messages.Backend(
                          group=(self.compute_uri +
                                 '/projects/my-project/regions/'
                                 'us-central2/instanceGroups/my-group')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

if __name__ == '__main__':
  test_case.main()
