# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for gcloud create-instance (CreateInstances API call)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute.operations.poller import OperationErrors
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsCreateInstanceGAZonalTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.prefix = 'mig-update-instances-zonal'
    self.scope = e2e_test_base.ZONAL

  @staticmethod
  def _ExtractInstanceNameFromUri(uri):
    return re.search(r'/instances/([^/]+)', uri).group(1)

  def GetInstanceNames(self, igm_name):
    return [
        self._ExtractInstanceNameFromUri(uri)
        for uri in self.GetInstanceUris(igm_name)
    ]

  def testCreateInstanceWithInstanceNameOnly(self):
    instance_template = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template, size=1)
    self.WaitUntilStable(igm_name)
    new_instance_name = igm_name + 'ci-test1'
    self.Run("""\
        compute instance-groups managed create-instance {group_name} \
          {scope_flag} \
          --instance {instance}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=new_instance_name))
    self.WaitUntilStable(igm_name)
    instance_names = self.GetInstanceNames(igm_name)
    self.assertEqual(len(instance_names), 2)
    self.assertIn(new_instance_name, instance_names)

  def _UpdateTemplate(self, igm_name, template_name):
    """Update instance template for group to template_name."""
    self.Run("""\
        compute instance-groups managed set-instance-template \
          {group_name} \
          {scope_flag} \
          --template {template}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        template=template_name))

  def _DescribeInstance(self, instance_uri):
    self.Run("""\
        compute instances describe {instance} \
    """.format(instance=self._ExtractInstanceNameFromUri(instance_uri)))

  def _GetInstanceId(self, instance_uri):
    self._DescribeInstance(instance_uri)
    new_output = self.GetNewOutput(reset=True)
    return re.search(r"id: '([0-9]+)'", new_output).group(1)

  def _ListInstanceConfigs(self, group_name):
    self.Run("""\
        compute instance-groups managed instance-configs list \
          {group_name} \
          {scope_flag}
    """.format(group_name=group_name, scope_flag=self.GetScopeFlag()))

  def testCreateInstanceWithStatefulDiskAndMetadata(self):
    instance_template = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template, size=1)
    self.WaitUntilStable(igm_name)
    old_instance_name = self.GetInstanceNames(igm_name)[0]
    new_instance_name = igm_name + 'ci-test2'
    instance_zone = self.ExtractZoneFromUri(self.GetInstanceUris(igm_name)[0])
    new_disk_uri = self.CreateDiskForStateful(zone=instance_zone)
    self.Run("""\
        compute instance-groups managed create-instance {group_name} \
          {scope_flag} \
          --instance {instance} \
          --stateful-disk=device-name={disk_name},mode=ro,source={source} \
          --stateful-metadata={metadata_key}={metadata_value} \
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=new_instance_name,
        disk_name=igm_name + 'ci-test2-disk',
        source=new_disk_uri,
        metadata_key=igm_name + 'ci-test2-md-key',
        metadata_value=igm_name + 'ci-test2-md-value'))
    self.WaitUntilStable(igm_name)
    self._ListInstanceConfigs(igm_name)
    self.AssertNewOutputContainsAll([
        new_instance_name, igm_name + 'ci-test2-disk',
        'source: {disk_source}'.format(disk_source=new_disk_uri),
        'mode: READ_ONLY', '{metadata_key}: {metadata_value}'.format(
            metadata_key=igm_name + 'ci-test2-md-key',
            metadata_value=igm_name + 'ci-test2-md-value')
    ],
                                    normalize_space=True)
    self.AssertOutputNotContains(
        'name: {old_instance_name}'.format(old_instance_name=old_instance_name))

  def testCreateInstanceAlreadyExistingInstanceError(self):
    instance_template = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template, size=1)
    self.WaitUntilStable(igm_name)
    existing_instance_name = self.GetInstanceNames(igm_name)[0]
    with self.AssertRaisesExceptionRegexp(
        OperationErrors,
        r'Resource .*{instance_name} is already a member of .*'.format(
            instance_name=existing_instance_name)):
      self.Run("""\
        compute instance-groups managed create-instance {group_name} \
          {scope_flag} \
          --instance {instance}
      """.format(
          group_name=igm_name,
          scope_flag=self.GetScopeFlag(),
          instance=existing_instance_name))

  @e2e_test_base.test_case.Filters.skip('Error not as expected', 'b/168818741')
  def testCreateInstanceNonExistingDiskError(self):
    instance_template = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template, size=1)
    self.WaitUntilStable(igm_name)
    fake_disk_uri = re.sub(r'/instances/([^/]+)', r'/disks/non-existent-disk',
                           self.GetInstanceUris(igm_name)[0])
    with self.AssertRaisesHttpExceptionRegexp(
        r"""HTTPError 400.*"""):
      self.Run("""\
          compute instance-groups managed create-instance {group_name} \
            {scope_flag} \
            --instance {instance}
            --stateful-disk=device-name=device-name-1,mode=ro,source={source} \
      """.format(
          group_name=igm_name,
          scope_flag=self.GetScopeFlag(),
          instance=self.GetInstanceNames(igm_name)[0],
          source=fake_disk_uri))

  def testCreateAndDescribeInstance(self):
    instance_template = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManagerStateful(
        instance_template, size=1)
    self.WaitUntilStable(igm_name)
    new_instance_name = igm_name + 'ci-test1'
    self.Run("""\
        compute instance-groups managed create-instance {group_name} \
          {scope_flag} \
          --instance {instance}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=new_instance_name))
    self.WaitUntilStable(igm_name)
    self.Run("""\
        compute instance-groups managed describe-instance {group_name} \
          {scope_flag} \
          --instance {instance}
    """.format(
        group_name=igm_name,
        scope_flag=self.GetScopeFlag(),
        instance=new_instance_name))
    self.AssertNewOutputContainsAll([new_instance_name, instance_template],
                                    normalize_space=True)


class ManagedInstanceGroupsCreateInstanceGARegionalTest(
    ManagedInstanceGroupsCreateInstanceGAZonalTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.prefix = 'mig-instance-configs-regional'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
