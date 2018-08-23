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
"""Integration tests for instance redistribution type feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_managers_test_base
from tests.lib.surface.compute import e2e_test_base


class ManagedInstanceGroupsInstanceRedistributionTypeTest(
    e2e_managers_test_base.ManagedTestBase):

  def SetUp(self):
    self.prefix = 'mig-instance-redistribution-type'
    self.scope = e2e_test_base.REGIONAL
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateManagedInstanceGroupWithInstanceRedistributionType(self):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.region_instance_group_manager_names.append(igm_name)
    scope_flag = self.GetScopeFlag()
    self.Run('compute instance-groups managed create {0} '
             '{1} '
             '--base-instance-name {0} '
             '--template {2} '
             '--size 0 '
             '--instance-redistribution-type proactive'.format(
                 igm_name, scope_flag, instance_template_name))
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains('instanceRedistributionType: PROACTIVE')

  def testUpdateManagedInstanceGroupSettingInstanceRedistributionType(self):
    instance_template_name = self.CreateInstanceTemplate()
    igm_name = self.CreateInstanceGroupManager(instance_template_name, 0)
    scope_flag = self.GetScopeFlag()
    self.Run('compute instance-groups managed update {0} '
             '{1} '
             '--instance-redistribution-type none'.format(igm_name, scope_flag))
    self.DescribeManagedInstanceGroup(igm_name)
    self.AssertNewOutputContains('instanceRedistributionType: NONE')


if __name__ == '__main__':
  e2e_test_base.main()
