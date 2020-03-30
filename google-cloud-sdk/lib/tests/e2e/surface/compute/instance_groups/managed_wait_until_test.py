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
"""Integration tests for instance-configs (MIG subresources)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_managers_stateful_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsWaitUntilZonalTest(
    e2e_managers_stateful_test_base.ManagedStatefulTestBase):

  def SetUp(self):
    self.prefix = 'mig-wait-until'
    self.scope = e2e_test_base.ZONAL
    self.track = calliope_base.ReleaseTrack.GA

  def testWaitUntilStable(self):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManager(instance_template_name, size=1)
    self.Run('compute instance-groups managed resize {0} {1} '
             '--size 2'.format(igm_name, self.GetScopeFlag()))
    self.Run('compute instance-groups managed wait-until --stable {0} {1} '
             '--timeout 600'.format(igm_name, self.GetScopeFlag()))
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains('isStable: false')
    self.AssertOutputContains('Group is stable')
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains('isStable: true')

  def testWaitUntilVersionTargetReached(self):
    instance_template = self.CreateInstanceTemplate()
    instance_template_new = self.CreateInstanceTemplate(machine_type='f1-micro')
    igm_name = self.CreateInstanceGroupManager(instance_template, size=1)
    self.WaitUntilStable(igm_name)
    self.Run(
        'compute instance-groups managed rolling-action start-update {0} '
        '--type proactive --version template={1} '
        '{2}'.format(igm_name, instance_template_new, self.GetScopeFlag()))
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains(
        'versionTarget: isReached: false', normalize_space=' \n')
    self.Run('compute instance-groups managed wait-until '
             '--version-target-reached {0} {1} '
             '--timeout 600'.format(igm_name, self.GetScopeFlag()))
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains(
        'versionTarget: isReached: true', normalize_space=' \n')


class ManagedInstanceGroupsWaitUntilRegionalTest(
    ManagedInstanceGroupsWaitUntilZonalTest):

  def SetUp(self):
    self.prefix = 'mig-regional-wait-until'
    self.scope = e2e_test_base.REGIONAL


if __name__ == '__main__':
  e2e_test_base.main()
