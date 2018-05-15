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
"""Tests for the backend-services get-health subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


def _MakeHealth1(test_obj):
  messages = test_obj.messages
  return messages.BackendServiceGroupHealth(
      healthStatus=[messages.HealthStatus(
          healthState=messages.HealthStatus.HealthStateValueValuesEnum.HEALTHY,
          instance=(test_obj.compute_uri +
                    '/projects/my-project/zones/zone-1/instances/instance-1'))])


def _MakeHealth2(test_obj):
  messages = test_obj.messages
  return messages.BackendServiceGroupHealth(
      healthStatus=[messages.HealthStatus(
          healthState=(messages.HealthStatus
                       .HealthStateValueValuesEnum.UNHEALTHY),
          instance=(test_obj.compute_uri +
                    '/projects/my-project/zones/zone-1/instances/instance-2'))])


def _MakeHealthDouble(test_obj):
  messages = test_obj.messages
  return messages.BackendServiceGroupHealth(
      healthStatus=[messages.HealthStatus(
          healthState=(messages.HealthStatus
                       .HealthStateValueValuesEnum.UNHEALTHY),
          instance=(test_obj.compute_uri +
                    '/projects/my-project/zones/zone-1/instances/instance-3')),
                    messages.HealthStatus(
                        healthState=(messages.HealthStatus
                                     .HealthStateValueValuesEnum.UNHEALTHY),
                        instance=(test_obj.compute_uri +
                                  '/projects/my-project/zones/zone-1/instances/'
                                  'instance-4'))])

GROUP_1 = ('https://www.googleapis.com/resourceviews/v1beta1/'
           'projects/my-project/zones/zone-1/resourceViews/group-1')
GROUP_2 = ('https://www.googleapis.com/resourceviews/v1beta1/'
           'projects/my-project/zones/zone-2/resourceViews/group-2')


class BackendServicesGetHealthTest(test_base.BaseTest,
                                   test_case.WithOutputCapture):

  def testSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],
        )],

        [_MakeHealth1(self)],

        [_MakeHealth2(self)],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1 --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              backendService='backend-service-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-1/resourceViews/group-1
            status:
              healthStatus:
              - healthState: HEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-1
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-2/resourceViews/group-2
            status:
              healthStatus:
              - healthState: UNHEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(uri=self.compute_uri)))

  def testScopeWarning(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],)],
        [_MakeHealth1(self)],
        [_MakeHealth2(self)],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1 --global
        """)
    self.AssertErrNotContains('WARNING:')

  def testSimpleCaseURI(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],
        )],

        [_MakeHealth1(self)],

        [_MakeHealthDouble(self)],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1 --uri --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              backendService='backend-service-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            {uri}/projects/my-project/zones/zone-1/instances/instance-1
            {uri}/projects/my-project/zones/zone-1/instances/instance-3
            {uri}/projects/my-project/zones/zone-1/instances/instance-4
            """.format(uri=self.compute_uri)))

  def testNoGroupsCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[],
        )],
        [],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1 --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))]
    )
    self.assertFalse(self.GetOutput())

  def testUriSupport(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],
        )],

        [_MakeHealth1(self)],

        [_MakeHealth2(self)],
    ])

    self.Run("""
        compute backend-services get-health
          {uri}/projects/my-project/global/backendServices/backend-service-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              backendService='backend-service-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-1/resourceViews/group-1
            status:
              healthStatus:
              - healthState: HEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-1
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-2/resourceViews/group-2
            status:
              healthStatus:
              - healthState: UNHEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(uri=self.compute_uri)))

  def testWithNonExistentBackendService(self):
    messages = self.messages
    def MakeRequests(*_, **kwargs):
      yield
      kwargs['errors'].append((404, 'Not Found'))
    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(textwrap.dedent("""\
        Could not fetch resource:
         - Not Found
        """)):
      self.Run("""
          compute backend-services get-health backend-service-1 --global
          """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))],
    )
    self.assertFalse(self.GetOutput())

  def testWithGetHealthError(self):
    messages = self.messages

    def MakeRequests(*_, **kwargs):
      MakeRequests.call_count = getattr(MakeRequests, 'call_count', 0) + 1

      if MakeRequests.call_count == 1:
        return iter([messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),],)])

      if MakeRequests.call_count == 2:
        return iter([_MakeHealth1(self)])

      if MakeRequests.call_count == 3:
        kwargs['errors'].append((500, 'Server Error'))
        return iter([])

      self.fail('Too many calls to MakeRequests')

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(textwrap.dedent("""\
        Could not get health for some groups:
         - Server Error
        """)):
      self.Run("""
        compute backend-services get-health backend-service-1 --global
        """)

    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              backendService='backend-service-1'))],

        [(self.compute.backendServices,
          'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              backendService='backend-service-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-1/resourceViews/group-1
            status:
              healthStatus:
              - healthState: HEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-1
            """.format(uri=self.compute_uri)))

  def testInteractiveScopeListing(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [],
        [
            messages.BackendService(
                selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                          'backend-service-1'),
                name='backend-service-1',
                port=80,
                backends=[
                    messages.Backend(group=GROUP_1),
                    messages.Backend(group=GROUP_2),
                ],)
        ],
        [_MakeHealth1(self)],
        [_MakeHealth2(self)],
    ])
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.IsInteractive',
        return_value=True)
    self.Run('compute backend-services get-health backend-service-1')

    self.CheckRequests(
        [(self.compute.regions, 'List', self.messages.ComputeRegionsListRequest(
            maxResults=500,
            project='my-project',))],
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project', backendService='backend-service-1'))],
        [(self.compute.backendServices, 'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              backendService='backend-service-1'))],
        [(self.compute.backendServices, 'GetHealth',
          messages.ComputeBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              backendService='backend-service-1'))],
    )


class BackendServicesGetHealthAlphaTest(BackendServicesGetHealthTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testScopeWarning(self):
    """Override. Warning should be printed."""
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],)],
        [_MakeHealth1(self)],
        [_MakeHealth2(self)],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1
             --region alaska
        """)
    self.AssertErrNotContains('WARNING:')

  def testRegionSimpleCase(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [messages.BackendService(
            selfLink=(test_resources._BACKEND_SERVICES_URI_PREFIX +
                      'backend-service-1'),
            name='backend-service-1',
            port=80,
            backends=[
                messages.Backend(group=GROUP_1),
                messages.Backend(group=GROUP_2),
            ],
        )],

        [_MakeHealth1(self)],

        [_MakeHealth2(self)],
    ])

    self.Run("""
        compute backend-services get-health backend-service-1
        --region alaska
        """)

    self.CheckRequests(
        [(self.compute.regionBackendServices,
          'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              project='my-project',
              region='alaska',
              backendService='backend-service-1'))],

        [(self.compute.regionBackendServices,
          'GetHealth',
          messages.ComputeRegionBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_1),
              project='my-project',
              region='alaska',
              backendService='backend-service-1'))],

        [(self.compute.regionBackendServices,
          'GetHealth',
          messages.ComputeRegionBackendServicesGetHealthRequest(
              resourceGroupReference=messages.ResourceGroupReference(
                  group=GROUP_2),
              project='my-project',
              region='alaska',
              backendService='backend-service-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-1/resourceViews/group-1
            status:
              healthStatus:
              - healthState: HEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-1
            ---
            backend: https://www.googleapis.com/resourceviews/v1beta1/projects/my-project/zones/zone-2/resourceViews/group-2
            status:
              healthStatus:
              - healthState: UNHEALTHY
                instance: {uri}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(uri=self.compute_uri)))


if __name__ == '__main__':
  test_case.main()
