# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for instances network-interfaces get-effective-firewalls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetEffectiveFirewallsAlphaTest(sdk_test_base.WithFakeAuth,
                                     cli_test_base.CliTestBase):
  """Base class for testing instance get-effective-firewalls command."""

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', 'alpha'),
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.service = self.apitools_client.instances
    self.zone_operations = self.apitools_client.zoneOperations

  def _GetInstance(self, name, zone=None):
    params = {'project': self.Project()}
    params['zone'] = zone

    instance_ref = self.resources.Parse(
        name, params=params, collection='compute.instances')
    instance = self.messages.Instance(networkInterfaces=[
        self.messages.NetworkInterface(name='nic0'),
        self.messages.NetworkInterface(name='nic11'),
    ])

    return instance, instance_ref

  def _ExpectInstanceGetRequest(self, instance, instance_ref, exception=None):
    request_type = self.messages.ComputeInstancesGetRequest

    self.service.Get.Expect(
        request=request_type(**instance_ref.AsDict()),
        response=instance,
        exception=exception)

  def _ExpectOperationGetRequest(self, operation, operation_ref):
    self.zone_operations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
            operation=operation_ref.operation,
            zone=operation_ref.zone,
            project=self.Project()), operation)

  def testGetEffectiveFirewalls(self):
    instance, instance_ref = self._GetInstance('instance-1', zone='atlanta')

    request = self.messages.ComputeInstancesGetEffectiveFirewallsRequest(
        instance='instance-1',
        networkInterface='nic0',
        project=self.Project(),
        zone='atlanta')
    firewall = self.messages.Firewall()
    response = self.messages.InstancesGetEffectiveFirewallsResponse(
        firewalls=[firewall])

    self._ExpectInstanceGetRequest(instance, instance_ref)
    self.service.GetEffectiveFirewalls.Expect(request, response=response)

    self.Run('compute instances network-interfaces get-effective-firewalls '
             'instance-1 --zone atlanta')


class GetEffectiveFirewallsBetaTest(GetEffectiveFirewallsAlphaTest):
  """Base class for testing instance get-effective-firewalls command."""

  def SetUp(self):
    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', 'beta'),
        real_client=core_apis.GetClientInstance(
            'compute', 'beta', no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.service = self.apitools_client.instances
    self.zone_operations = self.apitools_client.zoneOperations


if __name__ == '__main__':
  test_case.main()
