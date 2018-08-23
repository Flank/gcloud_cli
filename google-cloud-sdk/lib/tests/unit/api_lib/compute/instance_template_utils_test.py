# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for the instance_template_utils module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import instance_template_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class InstanceTemplateUtilsTest(cli_test_base.CliTestBase,
                                sdk_test_base.WithFakeAuth,
                                parameterized.TestCase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.compute_api = base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
    self.scope_lister = flags.GetDefaultScopeLister(self.compute_api.client)
    self.resources = self.compute_api.resources
    self.region = 'us-central1'

  def testCreateNetworkInterfaceMessage(self):
    network = None
    subnet = None
    address = None
    alias_ip_ranges_string = None
    network_tier = None
    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)
    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            constants.DEFAULT_NETWORK,
            params={'project': self.Project()},
            collection='compute.networks').SelfLink()
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessageWithNetwork(self):
    network = 'network1'
    subnet = None
    address = None
    alias_ip_ranges_string = None
    network_tier = None
    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)
    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink()
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessageWithSubnetAndNetwork(self):
    network = 'network1'
    subnet = 'subnet1'
    address = None
    alias_ip_ranges_string = None
    network_tier = None
    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)
    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink(),
        subnetwork=self.resources.Parse(
            'subnet1',
            params={'region': self.region, 'project': self.Project()},
            collection='compute.subnetworks').SelfLink()
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessageWithSubnet(self):
    network = None
    subnet = 'subnet1'
    address = None
    alias_ip_ranges_string = None
    network_tier = None

    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)

    expected = self.messages.NetworkInterface(
        subnetwork=self.resources.Parse(
            'subnet1',
            params={'region': self.region, 'project': self.Project()},
            collection='compute.subnetworks').SelfLink()
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessageWithOtherOptions(self):
    network = 'network1'
    subnet = 'subnet1'
    address = 'address1'
    alias_ip_ranges_string = '/24'
    network_tier = None

    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)

    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink(),
        subnetwork=self.resources.Parse(
            'subnet1',
            params={'region': self.region, 'project': self.Project()},
            collection='compute.subnetworks').SelfLink(),
        accessConfigs=[
            self.messages.AccessConfig(
                name=constants.DEFAULT_ACCESS_CONFIG_NAME,
                type=self.messages.AccessConfig.TypeValueValuesEnum
                .ONE_TO_ONE_NAT,
                natIP='address1',
            )],
        aliasIpRanges=[self.messages.AliasIpRange(ipCidrRange='/24')]
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessages(self):
    network_interface_arg = [
        {'network': 'network1',
         'subnet': 'subnet1',
         'aliases': '/24'},
        {'network': 'network2',
         'subnet': 'subnet2',
         'aliases': '/24'}]

    result = instance_template_utils.CreateNetworkInterfaceMessages(
        self.resources,
        self.scope_lister,
        self.messages,
        network_interface_arg,
        self.region)

    expected = [
        self.messages.NetworkInterface(
            network=self.resources.Parse(
                'network1',
                params={'project': self.Project()},
                collection='compute.networks').SelfLink(),
            subnetwork=self.resources.Parse(
                'subnet1',
                params={'region': self.region, 'project': self.Project()},
                collection='compute.subnetworks').SelfLink(),
            aliasIpRanges=[self.messages.AliasIpRange(ipCidrRange='/24')]),
        self.messages.NetworkInterface(
            network=self.resources.Parse(
                'network2',
                params={'project': self.Project()},
                collection='compute.networks').SelfLink(),
            subnetwork=self.resources.Parse(
                'subnet2',
                params={'region': self.region, 'project': self.Project()},
                collection='compute.subnetworks').SelfLink(),
            aliasIpRanges=[self.messages.AliasIpRange(ipCidrRange='/24')])]
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessagesWithAddress(self):
    network_interface_arg = [
        # Ensure address is correctly passed.
        {'network': 'network1',
         'address': 'address1'},
        # There is special handling for when address is an empty string.
        {'network': 'network2',
         'address': ''}]

    result = instance_template_utils.CreateNetworkInterfaceMessages(
        self.resources,
        self.scope_lister,
        self.messages,
        network_interface_arg,
        self.region)

    expected = [
        self.messages.NetworkInterface(
            network=self.resources.Parse(
                'network1',
                params={'project': self.Project()},
                collection='compute.networks').SelfLink(),
            accessConfigs=[
                self.messages.AccessConfig(
                    name=constants.DEFAULT_ACCESS_CONFIG_NAME,
                    type=self.messages.AccessConfig.TypeValueValuesEnum
                    .ONE_TO_ONE_NAT,
                    natIP='address1',
                )]),
        self.messages.NetworkInterface(
            network=self.resources.Parse(
                'network2',
                params={'project': self.Project()},
                collection='compute.networks').SelfLink(),
            accessConfigs=[
                self.messages.AccessConfig(
                    name=constants.DEFAULT_ACCESS_CONFIG_NAME,
                    type=self.messages.AccessConfig.TypeValueValuesEnum
                    .ONE_TO_ONE_NAT)])]
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessagesEmpty(self):
    network_interface_arg = None
    result = instance_template_utils.CreateNetworkInterfaceMessages(
        self.resources,
        self.scope_lister,
        self.messages,
        network_interface_arg,
        self.region)
    expected = []
    self.assertEqual(expected, result)

  @parameterized.named_parameters(
      ('BootFirst', [{'name': 'disk1',
                      'mode': 'ro',
                      'boot': 'yes',
                      'auto-delete': 'yes',
                      'device-name': 'pd1'},
                     {'name': 'disk2',
                      'mode': 'rw',
                      'boot': 'no',
                      'auto-delete': 'no'}]),
      ('BootSecond', [{'name': 'disk2',
                       'mode': 'rw',
                       'boot': 'no',
                       'auto-delete': 'no'},
                      {'name': 'disk1',
                       'mode': 'ro',
                       'boot': 'yes',
                       'auto-delete': 'yes',
                       'device-name': 'pd1'}]),
      ('BootFirstDefaults', [{'name': 'disk1',
                              'mode': 'ro',
                              'boot': 'yes',
                              'auto-delete': 'yes',
                              'device-name': 'pd1'},
                             {'name': 'disk2'}]),
      ('BootSecondDefaults', [{'name': 'disk2'},
                              {'name': 'disk1',
                               'mode': 'ro',
                               'boot': 'yes',
                               'auto-delete': 'yes',
                               'device-name': 'pd1'}]))
  def testCreatePersistentAttachedDiskMessages(self, disks):
    result = instance_template_utils.CreatePersistentAttachedDiskMessages(
        self.messages, disks)

    expected = [
        self.messages.AttachedDisk(
            autoDelete=True,
            boot=True,
            deviceName='pd1',
            mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            source='disk1',
            type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        self.messages.AttachedDisk(
            autoDelete=False,
            boot=False,
            mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            source='disk2',
            type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)]
    self.assertEqual(expected, result)

  def testCreatePersistentCreateDiskMessages(self):
    create_disks = [{'name': 'disk1',
                     'mode': 'ro',
                     'size': 2 ** 30,
                     'type': 'HDD',
                     'image': 'image1',
                     'image-project': 'project1',
                     'auto-delete': 'yes',
                     'device-name': 'pd1'},
                    # image family
                    {'name': 'disk2',
                     'mode': 'rw',
                     'size': (2 ** 30) * 2,
                     'type': 'SDD',
                     'image-family': 'family/if1',
                     'image-project': 'project2',
                     'auto-delete': 'no',
                     'device-name': 'pd2'},
                    # defaults
                    {'name': 'disk3',
                     'image': 'image2'}]
    image_uri = self.resources.Parse(
        'image1',
        collection='compute.images',
        params={'project': 'project1'}).SelfLink()
    image_family_uri = self.resources.Parse(
        'family/if1',
        collection='compute.images',
        params={'project': 'project2'}).SelfLink()
    image_uri_no_project = self.resources.Parse(
        'image2',
        collection='compute.images',
        params={'project': self.Project()}).SelfLink()

    results = instance_template_utils.CreatePersistentCreateDiskMessages(
        self.compute_api.client, self.resources, self.Project(),
        create_disks)

    expected = [
        self.messages.AttachedDisk(
            autoDelete=True,
            boot=False,
            deviceName='pd1',
            initializeParams=self.messages.AttachedDiskInitializeParams(
                diskName='disk1',
                sourceImage=image_uri,
                diskSizeGb=1,
                diskType='HDD'),
            mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        self.messages.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='pd2',
            initializeParams=self.messages.AttachedDiskInitializeParams(
                diskName='disk2',
                sourceImage=image_family_uri,
                diskSizeGb=2,
                diskType='SDD'),
            mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        self.messages.AttachedDisk(
            autoDelete=False,
            boot=False,
            initializeParams=self.messages.AttachedDiskInitializeParams(
                diskName='disk3',
                sourceImage=image_uri_no_project),
            mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)]
    self.assertEqual(expected, results)

  def testCreateDefaultBootAttachedDiskMessage(self):
    disk_type = 'HDD'
    disk_device_name = 'pd1'
    disk_auto_delete = False
    disk_size_gb = 1
    image_uri = self.resources.Parse(
        'image1',
        collection='compute.images',
        params={'project': self.Project()}).SelfLink()

    result = instance_template_utils.CreateDefaultBootAttachedDiskMessage(
        self.messages, disk_type, disk_device_name, disk_auto_delete,
        disk_size_gb, image_uri)

    expected = self.messages.AttachedDisk(
        autoDelete=False,
        boot=True,
        deviceName='pd1',
        initializeParams=self.messages.AttachedDiskInitializeParams(
            sourceImage=image_uri,
            diskSizeGb=1,
            diskType='HDD'),
        mode=self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    self.assertEqual(expected, result)

  def testCreateAcceleratorConfigMessages(self):
    accelerator = {
        'type': 'nvidia-tesla-k80',
        'count': 2}

    result = instance_template_utils.CreateAcceleratorConfigMessages(
        self.messages, accelerator)

    expected = [
        self.messages.AcceleratorConfig(
            acceleratorType='nvidia-tesla-k80',
            acceleratorCount=2)]
    self.assertEqual(expected, result)

  def testCreateAcceleratorConfigMessagesEmpty(self):
    accelerator = None
    result = instance_template_utils.CreateAcceleratorConfigMessages(
        self.messages, accelerator)
    self.assertEqual([], result)


class InstanceTemplateUtilsNetworkTierTest(cli_test_base.CliTestBase,
                                           sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.compute_api = base_classes.ComputeApiHolder(base.ReleaseTrack.ALPHA)
    self.scope_lister = flags.GetDefaultScopeLister(self.compute_api.client)
    self.resources = self.compute_api.resources
    self.region = 'us-central1'

  def testCreateNetworkInterfaceMessageWithNetworkTier(self):
    network = 'network1'
    subnet = 'subnet1'
    address = 'address1'
    alias_ip_ranges_string = '/24'
    network_tier = 'PREMIUM'

    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)

    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink(),
        subnetwork=self.resources.Parse(
            'subnet1',
            params={'region': self.region, 'project': self.Project()},
            collection='compute.subnetworks').SelfLink(),
        accessConfigs=[
            self.messages.AccessConfig(
                name=constants.DEFAULT_ACCESS_CONFIG_NAME,
                type=self.messages.AccessConfig.TypeValueValuesEnum
                .ONE_TO_ONE_NAT,
                natIP='address1',
                networkTier=self.messages.AccessConfig
                .NetworkTierValueValuesEnum('PREMIUM')
            )],
        aliasIpRanges=[self.messages.AliasIpRange(ipCidrRange='/24')]
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessageWithNetworkTierNoAddress(self):
    network = 'network1'
    subnet = 'subnet1'
    address = None
    alias_ip_ranges_string = '/24'
    network_tier = 'PREMIUM'

    result = instance_template_utils.CreateNetworkInterfaceMessage(
        self.resources, self.scope_lister, self.messages, network, self.region,
        subnet, address, alias_ip_ranges_string=alias_ip_ranges_string,
        network_tier=network_tier)

    expected = self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink(),
        subnetwork=self.resources.Parse(
            'subnet1',
            params={'region': self.region, 'project': self.Project()},
            collection='compute.subnetworks').SelfLink(),
        accessConfigs=[],
        aliasIpRanges=[self.messages.AliasIpRange(ipCidrRange='/24')]
    )
    self.assertEqual(expected, result)

  def testCreateNetworkInterfaceMessagesWithNetworkTier(self):
    network_interface_arg = [
        # Ensure address is correctly passed.
        {'network': 'network1',
         'address': 'address1',
         'network-tier': 'PREMIUM'}]

    result = instance_template_utils.CreateNetworkInterfaceMessages(
        self.resources, self.scope_lister, self.messages, network_interface_arg,
        self.region)

    expected = [self.messages.NetworkInterface(
        network=self.resources.Parse(
            'network1',
            params={'project': self.Project()},
            collection='compute.networks').SelfLink(),
        accessConfigs=[
            self.messages.AccessConfig(
                name=constants.DEFAULT_ACCESS_CONFIG_NAME,
                type=self.messages.AccessConfig.TypeValueValuesEnum
                .ONE_TO_ONE_NAT,
                natIP='address1',
                networkTier=self.messages.AccessConfig
                .NetworkTierValueValuesEnum('PREMIUM')
            )])]
    self.assertEqual(expected, result)


if __name__ == '__main__':
  test_case.main()
