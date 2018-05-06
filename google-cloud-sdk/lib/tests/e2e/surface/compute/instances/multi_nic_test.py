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
"""Integration tests for creating/using/deleting instances."""
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class MultiNicTestBase(e2e_instances_test_base.InstancesTestBase):
  """Base class for tests that use the new multi-nic command line."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-template', sequence_start=1)
    self._created_resources = []

  def TearDown(self):
    for name, res_type, scope in self._created_resources[::-1]:
      self.CleanUpResource(name, res_type, scope=scope)

  def _CreateResourceScheduleCleanUp(self, name, res_type, scope, creation_args,
                                     **additional_kwargs):
    self._created_resources.append((name, res_type, scope,))
    return self.Run('compute {0} create {1} {2}'.format(
        res_type, name, creation_args), **additional_kwargs)

  def _CreateSubnetAlphaBeta(self, cidr_range):
    name = self._name_generator.next()
    self._CreateResourceScheduleCleanUp(name, 'networks', e2e_test_base.GLOBAL,
                                        '--subnet-mode custom')
    self._CreateResourceScheduleCleanUp(
        name, 'networks subnets',
        e2e_test_base.REGIONAL, '--network {0} --range {1} --region {2}'.format(
            name, cidr_range, self.region))
    return name

  def _CreateSubnetGA(self, cidr_range):
    name = self._name_generator.next()
    self._CreateResourceScheduleCleanUp(name, 'networks', e2e_test_base.GLOBAL,
                                        '--subnet-mode custom')
    self._CreateResourceScheduleCleanUp(
        name, 'networks subnets', e2e_test_base.REGIONAL,
        '--network {0} --range {1} --region {2}'.format(
            name, cidr_range, self.region))
    return name

  def _InstanceUrl(self, name):
    return ('https://www.googleapis.com/'
            'compute/{0}/'
            'projects/cloud-sdk-integration-testing/'
            'zones/{1}/'
            'instances/{2}'.format(self.track.prefix or 'v1', self.zone, name))

  def _SubnetUrl(self, name, prefix=None):
    return ('https://www.googleapis.com/'
            'compute/{0}/'
            'projects/cloud-sdk-integration-testing/'
            'regions/{1}/'
            'subnetworks/{2}'.format(prefix or self.track.prefix or 'v1',
                                     self.region, name))


class MultiNicAlphaTest(MultiNicTestBase):
  """Test create instance command in alpha track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-instance', sequence_start=1)
    self._created_resources = []

  def testCreateMultiNicInstance(self):
    name = self._name_generator.next()
    subnet_1 = self._CreateSubnetAlphaBeta('10.0.1.0/24')
    subnet_2 = self._CreateSubnetAlphaBeta('10.0.2.0/24')
    # If the test passes the instance will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # instance clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instances', e2e_test_base.ZONAL, '--zone {0} '
        '--network-interface subnet={1} '
        '--network-interface subnet={2},address=\'\''.format(
            self.zone, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run(
        'compute instances describe {0} --zone {1}'.format(name, self.zone))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))

    self.ClearErr()
    self.Run('compute instances delete {0} --zone {1} --quiet'.format(
        name, self.zone))
    self.AssertErrContains('Deleted [{0}].'.format(self._InstanceUrl(name)))


class MultiNicBetaTest(MultiNicTestBase):
  """Test create instance command in beta track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-instance', sequence_start=1)
    self._created_resources = []

  def testCreateMultiNicInstance(self):
    name = self._name_generator.next()
    subnet_1 = self._CreateSubnetAlphaBeta('10.0.1.0/24')
    subnet_2 = self._CreateSubnetAlphaBeta('10.0.2.0/24')
    # If the test passes the instance will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # instance clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instances', e2e_test_base.ZONAL, '--zone {0} '
        '--network-interface subnet={1} '
        '--network-interface subnet={2},address=\'\''.format(
            self.zone, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run(
        'compute instances describe {0} --zone {1}'.format(name, self.zone))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))

    self.ClearErr()
    self.Run('compute instances delete {0} --zone {1} --quiet'.format(
        name, self.zone))
    self.AssertErrContains('Deleted [{0}].'.format(self._InstanceUrl(name)))


class MultiNicGATest(MultiNicTestBase):
  """Test create instance command in GA track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-instance', sequence_start=1)
    self._created_resources = []

  def testCreateMultiNicInstance(self):
    name = self._name_generator.next()
    subnet_1 = self._CreateSubnetGA('10.0.1.0/24')
    subnet_2 = self._CreateSubnetGA('10.0.2.0/24')
    # If the test passes the instance will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # instance clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instances', e2e_test_base.ZONAL,
        '--zone {0} '
        '--network-interface subnet={1} '
        '--network-interface subnet={2},address=\'\''.format(
            self.zone, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run('compute instances describe {0} --zone {1}'.format(name,
                                                                self.zone))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))

    self.ClearErr()
    self.Run('compute instances delete {0} --zone {1} --quiet'.format(
        name, self.zone))
    self.AssertErrContains('Deleted [{0}].'.format(
        self._InstanceUrl(name)))


class AliasIpRangeTest(MultiNicTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-instance', sequence_start=1)
    self._created_resources = []

  def testCreateInstanceWithAliasIpRange(self):
    name = self._name_generator.next()
    subnet = self._CreateSubnetAlphaBeta('10.0.3.0/24')
    self._CreateResourceScheduleCleanUp(
        name,
        'instances',
        e2e_test_base.ZONAL,
        '--zone {0} '
        '--network-interface subnet={1},aliases=/32'.format(self.zone, subnet),
        track=calliope_base.ReleaseTrack.GA)

    self.ClearOutput()
    self.Run(
        'compute instances describe {0} --zone {1}'.format(name, self.zone),
        track=calliope_base.ReleaseTrack.GA)
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(
        subnet, prefix='v1'))
    # The IP allocated must be 10.0.3.x.
    self.AssertOutputContains('ipCidrRange: 10.0.3.')

    # Ensure network-interfaces update to "" clears the range.
    self.Run('compute instances network-interfaces update {0} --zone {1} '
             '--aliases ""'.format(name, self.zone))
    self.ClearOutput()
    self.Run(
        'compute instances describe {0} --zone {1}'.format(name, self.zone))
    self.AssertNewOutputNotContains('aliasIpRanges')

    # Ensure network-interfaces update to /32 re-obtains IP range.
    self.Run('compute instances network-interfaces update {0} --zone {1} '
             '--aliases /32'.format(name, self.zone))
    result = self.Run(
        'compute instances describe {0} --zone {1}'.format(name, self.zone))
    self.assertEqual(1, len(result.networkInterfaces[0].aliasIpRanges))
    self.assertIn('/32',
                  result.networkInterfaces[0].aliasIpRanges[0].ipCidrRange)

    self.ClearErr()
    self.Run('compute instances delete {0} --zone {1} --quiet'.format(
        name, self.zone))
    self.AssertErrContains('Deleted [{0}].'.format(
        self._InstanceUrl(name)))


if __name__ == '__main__':
  e2e_test_base.main()
