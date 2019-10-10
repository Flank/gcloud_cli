# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Test calliope_base for compute resource policies unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib.surface.compute import test_base


class TestBase(test_base.BaseTest):
  """Base class for resource policies tests."""

  def SetUpTrack(self, track):
    if track == calliope_base.ReleaseTrack.ALPHA:
      self.api_version = 'alpha'
    elif track == calliope_base.ReleaseTrack.BETA:
      self.api_version = 'beta'
    else:
      self.api_version = 'v1'
    self.SelectApi(self.api_version)
    self.track = track
    self.region = 'us-central1'
    self.reg = resources.REGISTRY.Clone()
    self.reg.RegisterApiByName('compute', self.api_version)

    if track == calliope_base.ReleaseTrack.ALPHA:
      self.resource_policies = [
          self.MakeResourcePolicy(
              'pol1',
              2,
              '04:00',
              creation_timestamp='2017-10-26T17:54:10.636-07:00',
              support_vm_maintenance_policy=True),
          self.MakeResourcePolicy(
              'pol2',
              3,
              '08:00',
              description='desc',
              creation_timestamp='2017-10-27T17:54:10.636-07:00',
              support_vm_maintenance_policy=True)
      ]
    else:
      self.resource_policies = [
          self.MakeResourcePolicy(
              'pol1',
              2,
              '04:00',
              creation_timestamp='2017-10-26T17:54:10.636-07:00'),
          self.MakeResourcePolicy(
              'pol2',
              3,
              '08:00',
              description='desc',
              creation_timestamp='2017-10-27T17:54:10.636-07:00')
      ]

  def SetUp(self):
    self.SetUpTrack(self.track)

  def MakeResourcePolicy(self,
                         name,
                         days_in_cycle,
                         start_time,
                         description=None,
                         creation_timestamp=None,
                         support_vm_maintenance_policy=False):
    m = self.messages
    if support_vm_maintenance_policy:
      vm_policy = m.ResourcePolicyVmMaintenancePolicy(
          maintenanceWindow=m
          .ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
              dailyMaintenanceWindow=m.ResourcePolicyDailyCycle(
                  daysInCycle=days_in_cycle, startTime=start_time)))
      return m.ResourcePolicy(
          creationTimestamp=creation_timestamp,
          name=name,
          description=description,
          region=self.region,
          vmMaintenancePolicy=vm_policy)
    return m.ResourcePolicy(
        creationTimestamp=creation_timestamp,
        name=name,
        description=description,
        region=self.region)
