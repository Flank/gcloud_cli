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
"""Integration tests for creating/deleting firewalls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class AddressesBetaTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.address_names_used = []

  def GetAddressName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up
    self.address_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='beta-gcloud-compute-test-address'))
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
    self.Run('compute addresses list')
    self.AssertNewOutputContains(
        '/24 INTERNAL VPC_PEERING default', normalize_space=True)


class AddressesAlphaTest(AddressesBetaTest):

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


if __name__ == '__main__':
  e2e_instances_test_base.main()
