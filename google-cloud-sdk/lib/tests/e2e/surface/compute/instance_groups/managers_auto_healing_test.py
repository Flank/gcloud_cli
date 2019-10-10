# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Integration tests for auto healing feature of instance group managers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class InstanceGroupsAutoHealingTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.prefix = 'managed-instance-group-auto-healing'

    # Containers for created resources.
    self.instance_template_names = []
    self.instance_group_manager_names = []
    self.region_instance_group_manager_names = []
    self.health_check_names = []
    self.http_health_check_names = []
    self.https_health_check_names = []

    self.scope = e2e_test_base.ZONAL

  def TearDown(self):
    self.DeleteResources(self.instance_group_manager_names,
                         self.DeleteInstanceGroupManager,
                         'instance group manager')
    self.DeleteResources(self.region_instance_group_manager_names,
                         self.DeleteRegionalInstanceGroupManager,
                         'regional instance group manager')
    self.DeleteResources(self.instance_template_names,
                         self.DeleteInstanceTemplate, 'instance template')
    self.DeleteResources(self.health_check_names,
                         self.DeleteHealthCheck, 'health check')
    self.DeleteResources(self.http_health_check_names,
                         self.DeleteHttpHealthCheck, 'http health check')
    self.DeleteResources(self.https_health_check_names,
                         self.DeleteHttpsHealthCheck, 'https health check')

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

  def CreateHealthCheck(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute health-checks create tcp {0} --global'.format(name))
    self.health_check_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateHttpHealthCheck(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute http-health-checks create {0} '
             '--port {1} --request-path {2}'.format(name, 12345, '/healthz'))
    self.http_health_check_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateHttpsHealthCheck(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute https-health-checks create {0} '
             '--port {1} --request-path {2}'.format(name, 12345, '/healthz'))
    self.https_health_check_names.append(name)
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

  def DeleteHealthCheck(self, name):
    # Update seek position
    self.GetNewErr()
    self.Run('compute health-checks delete {0} --global --quiet'.format(name))
    stderr = self.GetNewErr()
    self.AssertErrContains(stderr, 'Deleted')
    return stderr

  def _RunAutohealingTest(self):
    igm_name = self.CreateInstanceTemplateAndInstanceGroupManager()
    http_hc_name = self.CreateHttpHealthCheck()
    https_hc_name = self.CreateHttpsHealthCheck()
    hc_name = self.CreateHealthCheck()

    self.Run('compute instance-groups managed describe {0} '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewOutputNotContains(http_hc_name, reset=False)
    self.AssertNewOutputNotContains(https_hc_name, reset=False)
    self.AssertNewOutputNotContains('initialDelaySec')

    self.Run('compute instance-groups managed set-autohealing {0} '
             '--http-health-check {1} '
             '--initial-delay {2} '
             '{3}'.format(igm_name, http_hc_name, '10m', self.GetScopeFlag()))
    self.ClearOutput()
    self.Run('compute instance-groups managed describe {0} '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewOutputContains(http_hc_name, reset=False)
    self.AssertNewOutputNotContains(https_hc_name, reset=False)
    self.AssertNewOutputContains('initialDelaySec: 600')

    self.Run('compute instance-groups managed set-autohealing {0} '
             '--https-health-check {1} '
             '--initial-delay {2} '
             '{3}'.format(igm_name, https_hc_name, '15m', self.GetScopeFlag()))
    self.ClearOutput()
    self.Run('compute instance-groups managed describe {0} '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewOutputNotContains(http_hc_name, reset=False)
    self.AssertNewOutputContains(https_hc_name, reset=False)
    self.AssertNewOutputContains('initialDelaySec: 900')

    self.Run('compute instance-groups managed set-autohealing {0} '
             '--health-check {1} '
             '--initial-delay {2} '
             '{3}'.format(igm_name, hc_name, '12m', self.GetScopeFlag()))
    self.ClearOutput()
    mig_description = self.Run('compute instance-groups managed describe {0} '
                               '{1} --no-user-output-enabled'.format(
                                   igm_name, self.GetScopeFlag()))
    self.assertEqual(
        mig_description['autoHealingPolicies'][0]['healthCheck'],
        'https://www.googleapis.com/compute/{}/'
        'projects/{}/global/healthChecks/{}'.format(
            self.track.prefix or 'v1', self.Project(), hc_name))

  def testAutohealingZonal(self):
    self._RunAutohealingTest()

  def testAutohealingRegional(self):
    self.scope = e2e_test_base.REGIONAL
    self._RunAutohealingTest()


if __name__ == '__main__':
  e2e_test_base.main()
