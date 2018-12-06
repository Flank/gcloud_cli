# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Unit tests for the compute ssh utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import ssh_utils
from tests.lib import sdk_test_base
from tests.lib import test_case


class GetExternalIPAddressTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.external_ip_address = '10.0.0.0'
    self.access_config = self.messages.AccessConfig(
        natIP=self.external_ip_address)
    self.external_nic = self.messages.NetworkInterface(
        accessConfigs=[self.access_config])
    self.internal_ip_address = '10.0.0.1'
    self.internal_nic = self.messages.NetworkInterface(
        networkIP=self.internal_ip_address)

  def testSingleExternalNic(self):
    instance = self.messages.Instance(
        name='instance-1', zone='zone-1', networkInterfaces=[self.external_nic])
    ip_result = ssh_utils.GetExternalIPAddress(instance)
    self.assertEqual(self.external_ip_address, ip_result)
    self.assertIs(ssh_utils.GetExternalInterface(instance), self.external_nic)

  def testSingleInternalNic(self):
    instance = self.messages.Instance(
        name='instance-1', zone='zone-1', networkInterfaces=[self.internal_nic])
    ip_result = ssh_utils.GetInternalIPAddress(instance)
    self.assertEqual(self.internal_ip_address, ip_result)
    self.assertIs(ssh_utils.GetInternalInterface(instance), self.internal_nic)

  def testMultipleNics(self):
    instance = self.messages.Instance(
        name='instance-1',
        zone='zone-1',
        networkInterfaces=[self.internal_nic, self.external_nic])
    self.assertEqual(ssh_utils.GetExternalIPAddress(instance),
                     self.external_ip_address)
    self.assertIs(ssh_utils.GetExternalInterface(instance), self.external_nic)
    self.assertEqual(ssh_utils.GetInternalIPAddress(instance),
                     self.internal_ip_address)
    self.assertIs(ssh_utils.GetInternalInterface(instance), self.internal_nic)

  def testMissingIPAddress(self):
    instance_no_ip = self.messages.Instance(
        name='Test', zone='Zone-test', networkInterfaces=[self.internal_nic])
    self.assertRaises(ssh_utils.MissingExternalIPAddressError,
                      ssh_utils.GetExternalIPAddress, instance_no_ip)

  def testMissingInterface(self):
    instance_no_internal = self.messages.Instance(name='Test', zone='Zone-test')
    self.assertRaises(exceptions.ToolException, ssh_utils.GetInternalInterface,
                      instance_no_internal)

  def testUnallocatedIPAddress(self):
    access_config_no_ip = self.messages.AccessConfig()
    nic_no_ip = self.messages.NetworkInterface(
        accessConfigs=[access_config_no_ip])
    instance_no_ip = self.messages.Instance(
        name='Test', zone='Zone-test', networkInterfaces=[nic_no_ip])
    self.assertRaises(ssh_utils.UnallocatedIPAddressError,
                      ssh_utils.GetExternalIPAddress, instance_no_ip)


if __name__ == '__main__':
  test_case.main()
