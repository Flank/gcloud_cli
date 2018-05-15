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
"""Integration tests for creating/deleting firewalls."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class AddressesTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.address_names_used = []

  def GetAddressName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.address_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='gcloud-compute-test-address'))
    self.address_names_used.append(self.address_name)

  def TearDown(self):
    for name in self.address_names_used:
      # Address names may be in either regional or global scope, but
      # we don't know which.  So we attempt to remove them from both.
      # self.CleanUpResource() silently fails if an address is not in
      # the given scope, and so this is safe.
      self.CleanUpResource(name, 'addresses',
                           scope=e2e_test_base.REGIONAL)
      self.CleanUpResource(name, 'addresses',
                           scope=e2e_test_base.EXPLICIT_GLOBAL)

  def _TestAddressCreation(self):
    self.GetAddressName()
    self.Run('compute addresses create {0} --region {1}'.format(
        self.address_name, self.region))
    self.AssertNewErrContains(self.address_name)
    self.Run('compute addresses list')
    self.AssertNewOutputContains(self.address_name)
    adrs = self.Run('compute addresses describe {0} --region {1}'.format(
        self.address_name, self.region))
    self.AssertNewOutputContains('RESERVED')
    return adrs

  def testAssignExternalAddressToInstance(self):
    # Create instance
    self._TestInstanceCreation()

    # Create external address
    address = self._TestAddressCreation().address

    # Ensure addresses is not currently associated with instance
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputNotContains(address)

    # Delete existing access config
    self.Run('compute instances delete-access-config {0} '
             '--zone {1}'.format(self.instance_name, self.zone))
    self.ClearOutput()

    # Add access config with created address
    self.Run('compute instances add-access-config {0} '
             '--zone {1} --address {2}'.format(self.instance_name, self.zone,
                                               address))
    self.ClearOutput()

    # Address should now be associated with instance
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContains(address)

    # Address should be marked 'in use'.
    self.Run('compute addresses describe {0} --region {1}'.format(
        self.address_name, self.region))
    self.AssertNewOutputContains('IN_USE')

  def testAssignExternalAddressToInstanceUponCreation(self):
    # Create external address
    address = self._TestAddressCreation().address

    # Create instance with the new address
    self.GetInstanceName()
    self.Run('compute instances create {0} --zone {1} '
             '--address {2}'.format(self.instance_name, self.zone, address))

    # Address should be associated with instance
    self.Run('compute instances describe {0} --zone {1}'.format(
        self.instance_name, self.zone))
    self.AssertNewOutputContains(address)

    # Address should be marked 'in use'.
    self.Run('compute addresses describe {0} --region {1}'.format(
        self.address_name, self.region))
    self.AssertNewOutputContains('IN_USE')

  def testAssignIpVersion(self):
    self.GetAddressName()
    self.Run('compute addresses create {0} --global --ip-version ipv4'.format(
        self.address_name))
    self.AssertErrContains(self.address_name)
    self.Run(
        'compute addresses describe {0} --global'.format(self.address_name))
    self.AssertNewOutputContains('IPV4')


class AddressesAlphaTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.address_names_used = []

  def GetAddressName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.address_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='alpha-gcloud-compute-test-address'))
    self.address_names_used.append(self.address_name)

  def TearDown(self):
    for name in self.address_names_used:
      self.CleanUpResource(
          name, 'addresses', scope=e2e_test_base.EXPLICIT_GLOBAL)

  def testVpcPeeringAddress(self):
    self.GetAddressName()
    self.Run(
        'compute addresses create {0} --global --prefix-length 24 --purpose '
        'VPC_PEERING --network default'.format(self.address_name))
    self.AssertErrContains(self.address_name)
    self.Run('compute addresses describe {0} --global'.format(
        self.address_name))
    self.AssertNewOutputContains('VPC_PEERING')


if __name__ == '__main__':
  e2e_instances_test_base.main()
