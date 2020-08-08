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
"""Unit tests for api_lib.compute.instances.ops_agents.utils module."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import guest_policy_validator as validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.core import yaml
from tests.lib import test_case

_GUEST_POLICY_YAML_TEMPLATE = textwrap.dedent("""\
assignment:
  instances:
  - zones/us-east1-c/instances/my-instance-1
description: '{desc}'
name: projects/509821339075/guestPolicies/test_policy
packageRepositories:
- yum:
    baseUrl: https://packages.cloud.google.com/yum/repos/google-cloud-logging-el7-x86_64-all
    displayName: Google Cloud Logging Agent Repository
    gpgKeys:
    - https://packages.cloud.google.com/yum/doc/yum-key.gpg
    - https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
    id: google-cloud-logging
packages:
- desiredState: UPDATED
  name: google-fluentd
recipes:
- desiredState: UPDATED
  installSteps:
  - scriptRun:
      script: |-
        #!/bin/bash
        sleep 5m
        sudo service stackdriver-agent stop
        sudo yum remove stackdriver-agent
        sudo yum install -y "stackdriver-agent-6.0.0-1"

        # Start the service post installation.
        /usr/sbin/service stackdriver-agent start

  name: start-stackdriver-agent-service
""")

_GUEST_POLICY_WITHOUT_DESCRIPTION = textwrap.dedent("""\
assignment:
  instances:
  - zones/us-east1-c/instances/my-instance-1
createTime: '2020-06-22T21:54:26.166Z'
etag: d52ade7f-29cc-457a-9b22-77af25f66c6a
name: projects/509821339075/guestPolicies/policy_without_description
packages:
- desiredState: UPDATED
  name: my-package
updateTime: '2020-06-22T21:54:26.166Z'
""")


class UtilsTest(test_case.TestCase):

  def _LoadMessage(self, serialized_yaml, message_type):
    resource_to_parse = yaml.load(serialized_yaml)
    return encoding.PyValueToMessage(message_type, resource_to_parse)

  def SetUp(self):
    self.messages = osconfig_api_utils.GetClientMessages(
        None, api_version_override='v1beta')

  def testOpsAgentPolicyReturnsTrue(self):
    ops_agent_guest_policy_description = json.dumps({
        'type': 'ops-agents',
        'description': 'desc',
        'agents': [{
            'enableAutoupgrade': True,
            'packageState': 'installed',
            'type': 'logging',
            'version': '1.6.35-1'
        }]
    })
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(
            desc=ops_agent_guest_policy_description),
        self.messages.GuestPolicy)
    self.assertTrue(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithEmptyDescriptionReturnsFalse(self):
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc=''), self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithoutTypeInDescriptionReturnsFalse(self):
    no_type_json_description = json.dumps({
        'agents': [],
    })
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc=no_type_json_description),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithNonOpsAgentTypeInDescriptionReturnsFalse(self):
    non_ops_agent_type_json_description = json.dumps({
        'type': 'non-ops-agents'
    })
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(
            desc=non_ops_agent_type_json_description),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithJsonArrayInDescriptionReturnsFalse(self):
    json_array_description = json.dumps([])
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc=json_array_description),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithOpsAgentStringInDescriptionReturnsFalse(self):
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc='ops-agents'),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithTypeStringInDescriptionReturnsFalse(self):
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc='type'),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithBrokenJsonInDescriptionReturnsFalse(self):
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_YAML_TEMPLATE.format(desc='{"ops-agents":}'),
        self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))

  def testGuestPolicyWithoutDescriptionReturnsFalse(self):
    guest_policy = self._LoadMessage(
        _GUEST_POLICY_WITHOUT_DESCRIPTION, self.messages.GuestPolicy)
    self.assertFalse(validator.IsOpsAgentPolicy(guest_policy))


if __name__ == '__main__':
  test_case.main()
