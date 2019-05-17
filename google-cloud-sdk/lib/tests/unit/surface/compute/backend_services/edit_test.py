# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_services import edit_util


def _MakeBackendService(messages):
  return messages.BackendService(
      backends=[
          messages.Backend(
              balancingMode=(
                  messages.Backend.BalancingModeValueValuesEnum.RATE),
              group=(
                  'https://www.googleapis.com/compute/v1/projects/'
                  'my-project/regions/us-central1/instanceGroups/group-1'),
              maxRate=123),
          messages.Backend(
              balancingMode=(
                  messages.Backend.BalancingModeValueValuesEnum.RATE),
              group=(
                  'https://www.googleapis.com/compute/v1/projects/'
                  'my-project/zones/us-central1-b/instanceGroups/group-2'),
              maxRate=456),
      ],
      description='The best backend service',
      healthChecks=[
          ('https://www.googleapis.com/compute/v1/projects/my-project/'
           'global/httpHealthChecks/health-check'),
      ],
      name='my-backend-service',
      port=80,
      portName='http',
      protocol=messages.BackendService.ProtocolValueValuesEnum.HTTP,
      selfLink=('https://www.googleapis.com/compute/v1/projects/my-project/'
                'global/backendServices/backend-service'),
      timeoutSec=15,
  )


class BackendServicesEditTest(test_base.BaseEditTest):

  def testSimpleEditingWithYAML(self):
    messages = self.messages
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # At the bottom of this file, you will find an example resource.
        #
        # Only fields that can be modified are shown. The original resource
        # with all of its fields is reproduced in the comment section at the
        # bottom of this document.

        ---
        backends:
        - balancingMode: RATE
          group: https://www.googleapis.com/compute/v1/projects/my-project/zones/europe-west1-a/instanceGroups/other-group
          maxRate: 789
        description: I edited this
        healthChecks:
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/other-health-check-1
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/other-health-check-2
        port: 80
        portName: http2
        timeoutSec: 10
        """)])

    self.make_requests.side_effect = iter([
        [_MakeBackendService(messages)],
        [],
    ])

    updated_service = messages.BackendService(
        backends=[
            messages.Backend(
                balancingMode=(
                    messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(
                    'https://www.googleapis.com/compute/v1/projects/'
                    'my-project/zones/europe-west1-a/instanceGroups/'
                    'other-group'),
                maxRate=789),
        ],
        description='I edited this',
        healthChecks=[
            ('https://www.googleapis.com/compute/v1/projects/my-project/'
             'global/httpHealthChecks/other-health-check-1'),
            ('https://www.googleapis.com/compute/v1/projects/my-project/'
             'global/httpHealthChecks/other-health-check-2')
        ],
        name='my-backend-service',
        port=80,
        portName='http2',
        timeoutSec=10,
    )

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(edit_util.YAML_FILE_CONTENTS)
    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],

        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service
              ))],
        )

  def testScopeWarning(self):
    messages = self.messages
    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        # You can edit the resource below. Lines beginning with "#" are
        # ignored.
        #
        # If you introduce a syntactic error, you will be given the
        # opportunity to edit the file again. You can abort by closing this
        # file without saving it.
        #
        # At the bottom of this file, you will find an example resource.
        #
        # Only fields that can be modified are shown. The original resource
        # with all of its fields is reproduced in the comment section at the
        # bottom of this document.

        ---
        backends:
        - balancingMode: RATE
          group: https://www.googleapis.com/compute/v1/projects/my-project/zones/europe-west1-a/instanceGroups/other-group
          maxRate: 789
        description: I edited this
        healthChecks:
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/other-health-check-1
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/other-health-check-2
        port: 80
        portName: http2
        timeoutSec: 10
        """)])

    self.make_requests.side_effect = iter([
        [_MakeBackendService(messages)],
        [],
    ])
    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)
    self.AssertErrNotContains('WARNING:')

  def testHealthCheckUriRequired(self):
    messages = self.messages
    edit_text1 = textwrap.dedent("""\
            ---
            backends:
            - balancingMode: RATE
              group: https://www.googleapis.com/compute/v1/projects/my-project/zones/europe-west1-a/instanceGroups/other-group
              maxRate: 789
            healthChecks:
            - other-health-check
            """)
    edit_text2 = textwrap.dedent("""\
            ---
            backends:
            - balancingMode: RATE
              group: https://www.googleapis.com/compute/v1/projects/my-project/zones/europe-west1-a/instanceGroups/other-group
              maxRate: 789
            healthChecks:
            - {uri}/projects/my-project/global/networks/other-health-check
            """.format(uri=self.compute_uri))
    self.mock_edit.side_effect = iter([edit_text1, edit_text2])

    self.make_requests.side_effect = iter([
        [_MakeBackendService(messages)],
        [],
    ])

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertErrContains('[healthChecks] must be referenced using URIs.')
    # Note we only check the beginning and end of the full uri because
    # different api versions (v1 vs v2 beta1) lead to different locations
    # of line breakes in the middle of the rror message.
    self.AssertErrContains('Invalid [healthChecks] reference: [{uri}'.format(
        uri=self.compute_uri))
    self.AssertErrContains('networks/other-health-check].')
    self.AssertFileOpenedWith(edit_util.YAML_FILE_CONTENTS,
                              edit_text1, edit_text2)
    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],
        )

  def testBackendUriRequired(self):
    messages = self.messages
    edit_text = textwrap.dedent("""\
            ---
            backends:
            - balancingMode: RATE
              group: my-group
              maxRate: 789
            healthChecks:
            - {uri}/projects/my-project/global/httpHealthChecks/other-health-check-2
            """.format(uri=self.compute_uri))
    self.mock_edit.side_effect = iter([edit_text])
    self.make_requests.side_effect = iter([
        [_MakeBackendService(messages)],
        [],
    ])

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)
    self.AssertErrContains('[group] must be referenced using URIs',
                           normalize_space=True)

  def testBackendUriAsInstanceGroupNotAnError(self):
    messages = self.messages
    edit_text = textwrap.dedent("""\
            ---
            backends:
            - balancingMode: RATE
              group: {uri}/projects/my-project/zones/us-central1-f/instanceGroups/qux
              maxRate: 789
            healthChecks:
            - {uri}/projects/my-project/global/httpHealthChecks/other-health-check-2
            """.format(uri=self.compute_uri))
    self.mock_edit.side_effect = iter([edit_text])
    self.make_requests.side_effect = iter([
        [_MakeBackendService(messages)],
        [],
    ])

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)
    self.AssertErrNotContains('Invalid')

  def testMixedHealthChecksAndProtocol(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        protocol: HTTPS
        healthChecks:
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/http-health-check
        - https://www.googleapis.com/compute/v1/projects/my-project/global/httpsHealthChecks/https-health-check
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
            ('https://www.googleapis.com/compute/v1/projects/my-project/'
             'global/httpHealthChecks/http-health-check'),
            ('https://www.googleapis.com/compute/v1/projects/my-project/'
             'global/httpsHealthChecks/https-health-check')
        ],
        name='my-backend-service',
        protocol=messages.BackendService.ProtocolValueValuesEnum.HTTPS,
    )

    self.Run("""
        compute backend-services edit my-backend-service --format yaml --global
        """)

    self.AssertFileOpenedWith(yaml_contents)
    self.CheckRequests(
        [(self.compute.backendServices,
          'Get',
          messages.ComputeBackendServicesGetRequest(
              project='my-project',
              backendService='my-backend-service'))],

        [(self.compute.backendServices,
          'Update',
          messages.ComputeBackendServicesUpdateRequest(
              project='my-project',
              backendService='my-backend-service',
              backendServiceResource=updated_service
              ))],
        )

  def testRegionScopeWarning(self):
    messages = self.messages

    self.mock_edit.side_effect = iter([textwrap.dedent("""\
        ---
        protocol: HTTPS
        healthChecks:
        - https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/generic-health-check
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
        - https://www.googleapis.com/compute/v1/projects/my-project/global/healthChecks/generic-health-check
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
            ('https://www.googleapis.com/compute/v1/projects/my-project/'
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


if __name__ == '__main__':
  test_case.main()
