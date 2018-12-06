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
"""Integration tests for instance group managers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class InstanceTemplatesTestBase(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-template', sequence_start=1)
    self._created_resources = []

  def TearDown(self):
    for name, res_type, scope in self._created_resources[::-1]:
      self.CleanUpResource(name, res_type, scope=scope)

  def _CreateResourceScheduleCleanUp(
      self, name, res_type, scope, creation_args):
    self._created_resources.append((name, res_type, scope,))
    return iter(self.Run('compute {0} create {1} {2} --format=disable'.format(
        res_type, name, creation_args)))

  def _CreateSubnetAlphaBeta(self, cidr_range):
    name = next(self._name_generator)
    self._CreateResourceScheduleCleanUp(name, 'networks', e2e_test_base.GLOBAL,
                                        '--subnet-mode custom')
    self._CreateResourceScheduleCleanUp(
        name, 'networks subnets',
        e2e_test_base.REGIONAL, '--network {0} --range {1} --region {2}'.format(
            name, cidr_range, self.region))
    return name

  def _CreateSubnetGA(self, cidr_range):
    name = next(self._name_generator)
    self._CreateResourceScheduleCleanUp(name, 'networks', e2e_test_base.GLOBAL,
                                        '--subnet-mode custom')
    self._CreateResourceScheduleCleanUp(
        name, 'networks subnets', e2e_test_base.REGIONAL,
        '--network {0} --range {1} --region {2}'.format(
            name, cidr_range, self.region))
    return name

  def _SubnetUrl(self, name):
    return ('https://www.googleapis.com/'
            'compute/{0}/'
            'projects/{1}/'
            'regions/{2}/'
            'subnetworks/{3}'.format(self.track.prefix or 'v1',
                                     self.Project(), self.region, name))

  def _InstanceTemplateUrl(self, name):
    return ('https://www.googleapis.com/'
            'compute/{0}/'
            'projects/{1}/'
            'global/'
            'instanceTemplates/{2}'.format(self.track.prefix or 'v1',
                                           self.Project(), name))

  def _CreateInstanceTemplate(self, creation_args):
    """Creates an instance template with the specified arguments.

    Args:
      creation_args: (string) arguments to the instance-templates
      create command.
    Returns:
      (string) the name of the newly created template.
    """
    name = next(self._name_generator)
    self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL, creation_args)
    return name


class InstanceTemplatesAlphaTest(InstanceTemplatesTestBase):
  """Test create instance template command in alpha track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-template', sequence_start=1)
    self._created_resources = []

  def testMultiNic(self):
    subnet_1 = self._CreateSubnetAlphaBeta('10.0.1.0/24')
    subnet_2 = self._CreateSubnetAlphaBeta('10.0.2.0/24')
    name = next(self._name_generator)
    # If the test passes the template will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # template clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL,
        '--region {0} '
        '--network-interface subnet={1},aliases=/32 '
        '--network-interface subnet={2},address=\'\''.format(
            self.region, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run('compute instance-templates describe {0}'.format(name))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))
    self.AssertOutputContains('ipCidrRange: /32')

    self.ClearErr()
    self.Run('compute instance-templates delete {0} --quiet'.format(name))
    self.AssertErrContains(
        'Deleted [{0}].'.format(self._InstanceTemplateUrl(name)))

  def testMinCpuPlatform(self):
    name = next(self._name_generator)

    result = next(self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL,
        '--min-cpu-platform "Intel Broadwell" '
        '--format=disable'))

    self.assertEqual(result.properties.minCpuPlatform, 'Intel Broadwell')


class InstanceTemplatesBetaTest(InstanceTemplatesTestBase):
  """Test create instance template command in beta track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='instance-template-beta', sequence_start=1)
    self._created_resources = []

  def testMultiNic(self):
    subnet_1 = self._CreateSubnetAlphaBeta('10.0.1.0/24')
    subnet_2 = self._CreateSubnetAlphaBeta('10.0.2.0/24')
    name = next(self._name_generator)
    # If the test passes the template will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # template clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL,
        '--region {0} '
        '--network-interface subnet={1},aliases=/32 '
        '--network-interface subnet={2},address=\'\''.format(
            self.region, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run('compute instance-templates describe {0}'.format(name))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))
    self.AssertOutputContains('ipCidrRange: /32')

    self.ClearErr()
    self.Run('compute instance-templates delete {0} --quiet'.format(name))
    self.AssertErrContains(
        'Deleted [{0}].'.format(self._InstanceTemplateUrl(name)))

  def testMinCpuPlatform(self):
    name = next(self._name_generator)

    result = next(self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL,
        '--min-cpu-platform "Intel Broadwell" '
        '--format=disable'))

    self.assertEqual(result.properties.minCpuPlatform, 'Intel Broadwell')

  def testCreateTemplateWithLabels(self):
    name = self._CreateInstanceTemplate(
        '--labels x=y,abc=xyz --disk name=boot-disk,boot=yes')
    self.ClearOutput()
    self.Run('compute instance-templates describe {0}'.format(name))
    self.AssertOutputContains('abc: xyz')
    self.AssertOutputContains('x: y')


class InstanceTemplatesGATest(InstanceTemplatesTestBase):
  """Test create instance template command in GA track."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='multi-nic-template', sequence_start=1)
    self._created_resources = []

  def testMultiNic(self):
    subnet_1 = self._CreateSubnetGA('10.0.1.0/24')
    subnet_2 = self._CreateSubnetGA('10.0.2.0/24')
    name = next(self._name_generator)
    # If the test passes the template will be deleted and the clean up will have
    # nothing to delete (but that's ok since CleanUpResource swallows all
    # exceptions.
    # However if test fails for any reason other than problems with deleting
    # template clean up is necessary for cleaning up networks and subnets.
    self._CreateResourceScheduleCleanUp(
        name, 'instance-templates', e2e_test_base.GLOBAL, '--region {0} '
        '--network-interface subnet={1},aliases=/32 '
        '--network-interface subnet={2},address=\'\''.format(
            self.region, subnet_1, subnet_2))
    self.ClearOutput()
    self.Run('compute instance-templates describe {0}'.format(name))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_1))
    self.AssertOutputContains('subnetwork: ' + self._SubnetUrl(subnet_2))
    self.AssertOutputContains('ipCidrRange: /32')

    self.ClearErr()
    self.Run('compute instance-templates delete {0} --quiet'.format(name))
    self.AssertErrContains(
        'Deleted [{0}].'.format(self._InstanceTemplateUrl(name)))

  def testCreateWithContainer(self):
    name = next(self._name_generator)
    self.Run('compute instance-templates create-with-container {} '
             '--container-image=gcr.io/google-containers/busybox'.format(name))
    try:
      self.ClearOutput()
      self.Run('compute instance-templates describe {}'.format(name))
      self.AssertOutputContains('containers')
      self.AssertOutputContains('image: gcr.io/google-containers/busybox')
    finally:
      self.Run('compute instance-templates delete ' + name)


if __name__ == '__main__':
  e2e_test_base.main()
