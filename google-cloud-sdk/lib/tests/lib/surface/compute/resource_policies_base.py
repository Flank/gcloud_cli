# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Test base for compute resource policies unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib.surface.compute import test_base


class TestBase(test_base.BaseTest):
  """Base class for resource policies tests."""

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = base.ReleaseTrack.ALPHA
    self.region = 'us-central1'
    self.reg = resources.REGISTRY.Clone()
    self.reg.RegisterApiByName('compute', 'alpha')

    self.resource_policies = [
        self.MakeResourcePolicy(
            'pol1', 2, '04:00',
            creation_timestamp='2017-10-26T17:54:10.636-07:00'),
        self.MakeResourcePolicy(
            'pol2', 3, '08:00', description='desc',
            creation_timestamp='2017-10-27T17:54:10.636-07:00')
    ]

  def MakeResourcePolicy(self, name, days_in_cycle, start_time,
                         description=None, creation_timestamp=None):
    m = self.messages
    vm_policy = m.ResourcePolicyVmMaintenancePolicy(
        maintenanceWindow=m.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
            dailyMaintenanceWindow=m.ResourcePolicyDailyCycle(
                daysInCycle=days_in_cycle,
                startTime=start_time)))
    return m.ResourcePolicy(
        creationTimestamp=creation_timestamp,
        name=name,
        description=description,
        region=self.region,
        vmMaintenancePolicy=vm_policy)
