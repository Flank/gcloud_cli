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
"""Tests for the backend-services edit subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_services import edit_util


class BackendServicesWithHealthcheckApiEditTest(test_base.BaseEditTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testScopeWarning(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        protocol: HTTPS
        healthChecks:
        - https://www.googleapis.com/compute/beta/projects/my-project/global/healthChecks/generic-health-check
        """)])

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    self.Run("""
        compute backend-services edit my-backend-service --region alaska --format yaml
        """)
    self.AssertErrNotContains('WARNING:')

  def testMixedHealthChecksAndProtocol_RegionBackendService(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        protocol: HTTPS
        healthChecks:
        - https://www.googleapis.com/compute/beta/projects/my-project/global/healthChecks/generic-health-check
        """)])

    yaml_contents = (edit_util.YAML_FILE_CONTENTS_HEADER +
                     '{}\n' +
                     edit_util.YAML_FILE_CONTENTS_EXAMPLE +
                     '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(
        healthChecks=[
            ('https://www.googleapis.com/compute/beta/projects/my-project/'
             'global/healthChecks/generic-health-check')
        ],
        name='my-backend-service',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTPS,
    )

    self.Run("""
        compute backend-services edit my-backend-service --region alaska --format yaml
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.regionBackendServices,
          'Get',
          messages.ComputeRegionBackendServicesGetRequest(
              project='my-project',
              region='alaska',
              backendService='my-backend-service'))],

        [(self.compute.regionBackendServices,
          'Update',
          messages.ComputeRegionBackendServicesUpdateRequest(
              project='my-project',
              region='alaska',
              backendService='my-backend-service',
              backendServiceResource=updated_service
              ))],
        )


class BackendServicesWithSessionAffinityApiEditTest(test_base.BaseEditTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testNone(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        sessionAffinity: NONE
        """)])

    yaml_contents = (
        edit_util.YAML_FILE_CONTENTS_HEADER + '{}\n' +
        edit_util.YAML_FILE_CONTENTS_EXAMPLE +
        '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(
        sessionAffinity=
        messages.BackendService.SessionAffinityValueValuesEnum.NONE,
        name='my-backend-service',)

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service))],)

  def testClientIp(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        sessionAffinity: CLIENT_IP
        """)])

    yaml_contents = (
        edit_util.YAML_FILE_CONTENTS_HEADER + '{}\n' +
        edit_util.YAML_FILE_CONTENTS_EXAMPLE +
        '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(
        sessionAffinity=
        messages.BackendService.SessionAffinityValueValuesEnum.CLIENT_IP,
        name='my-backend-service',)

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service))],)

  def testGeneratedCookie(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        sessionAffinity: GENERATED_COOKIE
        """)])

    yaml_contents = (
        edit_util.YAML_FILE_CONTENTS_HEADER + '{}\n' +
        edit_util.YAML_FILE_CONTENTS_EXAMPLE +
        '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(
        sessionAffinity=
        messages.BackendService.SessionAffinityValueValuesEnum.GENERATED_COOKIE,
        name='my-backend-service',)

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service))],)

  def testAffinityTtl(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        affinityCookieTtlSec: 18
        """)])

    yaml_contents = (
        edit_util.YAML_FILE_CONTENTS_HEADER + '{}\n' +
        edit_util.YAML_FILE_CONTENTS_EXAMPLE +
        '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(affinityCookieTtlSec=18,
                                              name='my-backend-service',)

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service))],)

  def testGeneratedCookieAffinityTtl(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        sessionAffinity: GENERATED_COOKIE
        affinityCookieTtlSec: 18
        """)])

    yaml_contents = (
        edit_util.YAML_FILE_CONTENTS_HEADER + '{}\n' +
        edit_util.YAML_FILE_CONTENTS_EXAMPLE +
        '#   name: my-backend-service\n')

    self.make_requests.side_effect = iter([
        [messages.BackendService(name='my-backend-service')],
        [],
    ])

    updated_service = messages.BackendService(
        sessionAffinity=
        messages.BackendService.SessionAffinityValueValuesEnum.GENERATED_COOKIE,
        affinityCookieTtlSec=18,
        name='my-backend-service',)

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices, 'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        [(self.compute.backendServices, 'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service))],)

if __name__ == '__main__':
  test_case.main()
