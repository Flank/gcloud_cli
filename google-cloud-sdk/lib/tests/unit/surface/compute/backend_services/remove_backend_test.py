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
"""Tests for the backend services remove-backend subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class RemoveBackendTest(test_base.BaseTest):

  def testWithNonExistentBackend(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Backend \[my-group-3\] in zone \[us-central1-a\] is not a backend of '
        r'backend service \[my-backend-service\].'):
      self.Run("""
          compute backend-services remove-backend my-backend-service
            --instance-group my-group-3 --instance-group-zone us-central1-a
            --global
          """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
    )

  def testScopeWarning(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(group=(
                    self.compute_uri +
                    '/projects/my-project/zones/'
                    'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(group=(
                    self.compute_uri +
                    '/projects/my-project/zones/'
                    'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend my-backend-service
          --instance-group my-group-1 --instance-group-zone us-central1-a
          --global
        """)
    self.AssertErrNotContains('WARNING:')

  def testWithExistingBackend(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend my-backend-service
          --instance-group my-group-1 --instance-group-zone us-central1-a
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
                                 'us-central1-a/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testUriSupport(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend
          {uri}/projects/my-project/global/backendServices/my-backend-service
          --instance-group {uri}/projects/my-project/zones/us-central1-a/instanceGroups/my-group-1
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
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],

        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
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
        compute backend-services remove-backend my-backend-service
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
                          group=(self.compute_uri +
                                 '/projects/my-project/zones/'
                                 'us-central1-a/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

    self.AssertErrContains('my-group-1')
    self.AssertErrContains('us-central1-a')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('us-central2-a')

  def testWithExistingBackendIG(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend my-backend-service
          --instance-group my-group-1 --instance-group-zone us-central1-a
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
                                 '/projects/my-project/zones'
                                 '/us-central1-a/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithNonExistentRegionBackend(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri + '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri + '/projects/my-project/zones/'
                           'us-central1-a/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Backend \[my-group-3\] in region \[us-central1\] is not a backend of '
        r'backend service \[my-backend-service\].'):
      self.Run("""
          compute backend-services remove-backend my-backend-service
            --instance-group my-group-3 --instance-group-region us-central1
            --global
          """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              backendService='my-backend-service',
              project='my-project'))],
    )

  def testWithExistingBackendRegionalIG(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/regions/'
                           'us-central1/instanceGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/regions/'
                           'us-central1/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend my-backend-service
          --instance-group my-group-1 --instance-group-region us-central1
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
                                 '/projects/my-project/regions'
                                 '/us-central1/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithExistingBackendNetworkEndpointGroup(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [messages.BackendService(
            name='my-backend-service',
            backends=[
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/zones/'
                           'us-central1-a/networkEndpointGroups/my-group-1')),
                messages.Backend(
                    group=(self.compute_uri +
                           '/projects/my-project/regions/'
                           'us-central1/instanceGroups/my-group-2')),
            ],
            port=80,
            fingerprint=b'my-fingerprint',
            timeoutSec=120)],
        [],
    ]

    self.Run("""
        compute backend-services remove-backend my-backend-service
          --network-endpoint-group my-group-1
          --network-endpoint-group-zone us-central1-a
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
                                 '/projects/my-project/regions'
                                 '/us-central1/instanceGroups/my-group-2')),
                  ],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithExistingBackendSingleGlobalNeg(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [
            messages.BackendService(
                name='my-backend-service',
                backends=[
                    messages.Backend(
                        group=(
                            self.compute_uri +
                            '/projects/my-project/global/networkEndpointGroups/my-global-neg'
                        ))
                ],
                port=80,
                fingerprint=b'my-fingerprint',
                timeoutSec=120)
        ],
        [],
    ]

    self.Run("""\
        compute backend-services remove-backend my-backend-service
          --network-endpoint-group my-global-neg
          --global-network-endpoint-group
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
                  backends=[],
                  timeoutSec=120),
              project='my-project'))],
    )

  def testWithExistingBackendSingleRegionNeg(self):
    messages = self.messages
    self.make_requests.side_effect = [
        [
            messages.BackendService(
                name='my-backend-service',
                backends=[
                    messages.Backend(
                        group=(
                            self.compute_uri +
                            '/projects/my-project/regions/us-central1/networkEndpointGroups/my-region-neg'
                        ))
                ],
                port=80,
                fingerprint=b'my-fingerprint',
                timeoutSec=120)
        ],
        [],
    ]

    self.Run("""\
        compute backend-services remove-backend my-backend-service
          --network-endpoint-group my-region-neg
          --network-endpoint-group-region us-central1
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
                  backends=[],
                  timeoutSec=120),
              project='my-project'))],
    )

if __name__ == '__main__':
  test_case.main()
