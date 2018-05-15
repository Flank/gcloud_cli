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
"""Integration tests for manipulating subnetworks."""

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.sdk_test_base import Retry
from tests.lib.surface.compute import e2e_test_base


class SubnetworksTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='subnets-test-network'))
    self.subnetwork_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='subnets-test-subnet'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(self.subnetwork_name, 'networks subnets',
                         scope=e2e_test_base.REGIONAL)
    self.CleanUpResource(self.network_name, 'networks',
                         scope=e2e_test_base.GLOBAL)

  def testSubnetworks(self):
    self.Run('compute networks create {0} --subnet-mode custom'
             .format(self.network_name))
    self.AssertNewOutputContains(self.network_name)
    self.Run('compute networks subnets create {0} --network {1} '
             '--region {2} --range 10.11.12.0/24'
             .format(self.subnetwork_name, self.network_name, self.region))
    self.AssertNewOutputContains(self.subnetwork_name)
    self.Run('compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('name: {0}'.format(self.subnetwork_name))

    # Do not assert the output to avoid flakiness, because it depends on Ncon
    # index for the result, which sometimes has a long delay but is out of
    # control of Arcus.
    self.Run('alpha compute networks subnets list-usable')

    self.Run('compute networks subnets delete {0} --region {1}'
             .format(self.subnetwork_name, self.region))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testSubnetworksPrivateIpGoogleAccess(self):
    self.Run('compute networks create {0} --subnet-mode custom'
             .format(self.network_name))
    self.AssertNewOutputContains(self.network_name)

    # First create a subnetwork without privateIpGoogleAccess enabled.
    self.Run('beta compute networks subnets create {0} --network {1} '
             '--region {2} --range 10.11.12.0/24'.format(
                 self.subnetwork_name, self.network_name, self.region))
    self.AssertNewOutputContains(self.subnetwork_name)
    self.Run('beta compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('privateIpGoogleAccess: false')

    # Set --enable-private-ip-google-access.
    self.Run('beta compute networks subnets update {0} --region {1} '
             '--enable-private-ip-google-access'.format(
                 self.subnetwork_name, self.region))
    self.Run('beta compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('privateIpGoogleAccess: true')

    # Turn it off again.
    self.Run('beta compute networks subnets update {0} --region {1} '
             '--no-enable-private-ip-google-access'.format(
                 self.subnetwork_name, self.region))
    self.Run('beta compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('privateIpGoogleAccess: false')

    # Delete the subnet.
    self.Run('compute networks subnets delete {0} --region {1}'
             .format(self.subnetwork_name, self.region))

    # Create the subnet again but with --private-ip-google-access enabled this
    # time.
    self.Run('beta compute networks subnets create {0} --network {1} '
             '--region {2} --range 10.11.12.0/24 '
             '--enable-private-ip-google-access'.format(
                 self.subnetwork_name, self.network_name, self.region))
    self.AssertNewOutputContains(self.subnetwork_name)
    self.Run('beta compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('privateIpGoogleAccess: true')

    # Delete the subnet.
    self.Run('compute networks subnets delete {0} --region {1}'
             .format(self.subnetwork_name, self.region))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testSubnetworksAddRemoveSecondaryRange(self):
    self.Run('compute networks create {0} --subnet-mode custom'
             .format(self.network_name))
    self.AssertNewOutputContains(self.network_name)

    # First create a subnetwork with no secondary ranges.
    self.Run('compute networks subnets create {0} --network {1} '
             '--region {2} --range 10.11.12.0/24'.format(
                 self.subnetwork_name, self.network_name, self.region))
    self.AssertNewOutputContains(self.subnetwork_name)
    self.Run('compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('privateIpGoogleAccess: false')
    self.AssertNewOutputNotContains('10.11.13.0/24')

    # Add a secondary range.
    self.Run('compute networks subnets update {0} --region {1} '
             '--add-secondary-ranges range1=10.11.13.0/24'.format(
                 self.subnetwork_name, self.region))
    self.ClearOutput()
    self.Run('compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputContains('10.11.13.0/24')

    # Remove it.
    self.Run('compute networks subnets update {0} --region {1} '
             '--remove-secondary-ranges range1'.format(self.subnetwork_name,
                                                       self.region))
    self.ClearOutput()
    self.Run('compute networks subnets describe {0} --region {1}'
             .format(self.subnetwork_name, self.region))
    self.AssertNewOutputNotContains('10.11.13.0/24')

    # Delete the subnet.
    self.Run('compute networks subnets delete {0} --region {1}'
             .format(self.subnetwork_name, self.region))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))


if __name__ == '__main__':
  e2e_test_base.main()
