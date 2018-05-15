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
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base


class InstanceGroupsAutoscalingTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.prefix = 'managed-instance-group-autoscaling'
    self.track = calliope_base.ReleaseTrack.ALPHA

    # Containers for created resources.
    self.instance_template_names = []
    self.instance_group_manager_names = []
    self.region_instance_group_manager_names = []
    self.scope = e2e_test_base.ZONAL

  def TearDown(self):
    self.DeleteResources(self.instance_group_manager_names,
                         self.DeleteInstanceGroupManager,
                         'instance group manager')
    self.DeleteResources(self.region_instance_group_manager_names,
                         self.DeleteRegionalInstanceGroupManager,
                         'regional instance group manager')
    try:
      self.DeleteResources(self.instance_template_names,
                           self.DeleteInstanceTemplate, 'instance template')
    except AssertionError:
      # Cleanup script should handle teardown issues
      pass

  def GetScopeFlag(self, plural=False):
    if self.scope == e2e_test_base.ZONAL:
      flag_name = 'zone'
      flag_value = self.zone
    elif self.scope == e2e_test_base.REGIONAL:
      flag_name = 'region'
      flag_value = self.region
    elif self.scope == e2e_test_base.EXPLICIT_GLOBAL:
      flag_name = 'global'
      flag_value = ''
    else:
      return ''
    if plural:
      flag_name += 's'
    return '--' + flag_name + ' ' + flag_value

  def CreateInstanceTemplate(self, machine_type='n1-standard-1'):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute instance-templates create {0} --machine-type {1}'
             .format(name, machine_type))
    self.instance_template_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceGroupManager(self, instance_template_name, size=0):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    if self.scope == e2e_test_base.ZONAL:
      self.instance_group_manager_names.append(name)
    elif self.scope == e2e_test_base.REGIONAL:
      self.region_instance_group_manager_names.append(name)

    self.Run('compute instance-groups managed create {0} '
             '{1} '
             '--base-instance-name {2} '
             '--size {3} '
             '--template {4}'
             .format(name,
                     self.GetScopeFlag(), name, size, instance_template_name))
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceTemplateAndInstanceGroupManager(self, size=0):
    instance_template_name = self.CreateInstanceTemplate()
    return self.CreateInstanceGroupManager(instance_template_name, size)

  def testAutoscaling(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager()
    autoscaler_name_prefix = igm_name

    # Add autoscaler with everything.
    self.Run('compute instance-groups managed set-autoscaling {0} '
             '--zone {1} '
             '--mode on '
             '--cool-down-period 1m '
             '--description whatever '
             '--min-num-replicas 5 '
             '--max-num-replicas 10 '
             '--scale-based-on-cpu --target-cpu-utilization 0.5 '
             '--scale-based-on-load-balancing '
             '--target-load-balancing-utilization 0.8 '
             '--custom-metric-utilization metric=foo.googleapis.com/metric1,'
             'utilization-target=1,utilization-target-type=GAUGE '
             '--custom-metric-utilization metric=foo.googleapis.com/metric2,'
             'utilization-target=2,'
             'utilization-target-type=DELTA_PER_SECOND '
             '--custom-metric-utilization metric=foo.googleapis.com/metric3,'
             'utilization-target=3,'
             'utilization-target-type=DELTA_PER_MINUTE '
             .format(igm_name, self.zone))
    self.AssertNewErrContainsAll(
        ['Created', 'autoscalers/{0}'.format(autoscaler_name_prefix)])
    self.ClearOutput()

    self.Run('compute instance-groups managed describe {0} --zone {1}'
             .format(igm_name, self.zone))
    # Get output and drop spaces after newlines.
    self.AssertOutputContains('coolDownPeriodSec: 60', normalize_space=True)
    self.AssertOutputContains('cpuUtilization:\n'
                              'utilizationTarget: 0.5', normalize_space=True)
    self.AssertOutputContains('metric: foo.googleapis.com/metric1\n'
                              'utilizationTarget: 1.0\n'
                              'utilizationTargetType: GAUGE',
                              normalize_space=True)
    self.AssertOutputContains('metric: foo.googleapis.com/metric2\n'
                              'utilizationTarget: 2.0\n'
                              'utilizationTargetType: DELTA_PER_SECOND',
                              normalize_space=True)
    self.AssertOutputContains('metric: foo.googleapis.com/metric3\n'
                              'utilizationTarget: 3.0\n'
                              'utilizationTargetType: DELTA_PER_MINUTE',
                              normalize_space=True)
    self.AssertOutputContains('loadBalancingUtilization:\n'
                              'utilizationTarget: 0.8', normalize_space=True)
    self.AssertOutputContains('minNumReplicas: 5', normalize_space=True)
    self.AssertOutputContains('maxNumReplicas: 10', normalize_space=True)
    self.AssertOutputContains('description: whatever', normalize_space=True)
    self.ClearErr()
    self.ClearOutput()

    # Stop autoscaling.
    self.Run('compute instance-groups managed stop-autoscaling {0} '
             '--zone {1}'.format(igm_name, self.zone))
    self.AssertNewErrContainsAll(
        ['Deleted', 'autoscalers/{0}'.format(autoscaler_name_prefix)])
    self.ClearOutput()

    # Make sure autoscaler is removed.
    self.Run('compute instance-groups managed describe {0} --zone {1}'
             .format(igm_name, self.zone))
    self.AssertNewOutputNotContains('autoscaler')
    self.ClearErr()


if __name__ == '__main__':
  e2e_test_base.main()
