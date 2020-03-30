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

"""Tests for the instance-groups managed set-autohealing subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.cli_test_base import MockArgumentError
from tests.lib.surface.compute import test_base
from mock import patch

API_VERSION = 'beta'


class InstanceGroupManagersSetAutohealingZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA

  def testSetAutohealing_HealthCheck(self):
    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --health-check health-check-1
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testSetAutohealing_HttpHealthCheck(self):
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --http-health-check health-check-1
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testSetAutohealing_HttpsHealthCheck(self):
    health_check_uri = (
        '{0}/projects/my-project/global/httpsHealthChecks/'
        'health-check-2'.format(self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --https-health-check health-check-2
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testSetAutohealing_InitialDelay(self):
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --initial-delay 10m
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        initialDelaySec=10 * 60),
                ],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testSetAutohealing_EmptyPolicy(self):
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testSetAutohealing_BothHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --http-health-check: At most one of --health-check | '
        '--http-health-check | --https-health-check may be specified.'):
      self.Run("""
          compute instance-groups managed set-autohealing group-1
            --zone central2-a
            --http-health-check health-check-1
            --https-health-check health-check-2
          """)

  def testUriSupport(self):
    igm_uri = (
        '{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
        'group-1'.format(self.compute_uri))
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing {0}
          --zone central2-a
          --http-health-check {1}
        """.format(igm_uri, health_check_uri))

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testScopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('5\n')
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --http-health-check health-check-1
        """)

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, 'Patch', request)],
    )

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --http-health-check health-check-1
        """)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidInitialDelay(self):
    with self.assertRaisesRegex(
        MockArgumentError,
        '.*value of initial delay must be between 0 and 1y.*'):
      self.Run("""
        compute instance-groups managed set-autohealing group-1
          --zone central2-a
          --initial-delay 2018y
        """)


class InstanceGroupManagersSetAutohealingRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA

  def testSetAutohealing_HttpHealthCheck(self):
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --region central2
          --http-health-check health-check-1
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testSetAutohealing_HttpsHealthCheck(self):
    health_check_uri = (
        '{0}/projects/my-project/global/httpsHealthChecks/'
        'health-check-2'.format(self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --region central2
          --https-health-check health-check-2
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testSetAutohealing_InitialDelay(self):
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --region central2
          --initial-delay 10m
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        initialDelaySec=10 * 60),
                ],))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testSetAutohealing_EmptyPolicy(self):
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --region central2
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[],))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testSetAutohealing_BothHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --http-health-check: At most one of --health-check | '
        '--http-health-check | --https-health-check may be specified.'):
      self.Run("""
          compute instance-groups managed set-autohealing group-1
            --region central2
            --http-health-check health-check-1
            --https-health-check health-check-2
          """)

  def testUriSupport(self):
    igm_uri = (
        '{0}/projects/my-project/regions/central2/instanceGroupManagers/'
        'group-1'.format(self.compute_uri))
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing {0}
          --region central2
          --http-health-check {1}
        """.format(igm_uri, health_check_uri))

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testScopePrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('2\n')
    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed set-autohealing group-1
          --http-health-check health-check-1
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                autoHealingPolicies=[
                    self.messages.InstanceGroupManagerAutoHealingPolicy(
                        healthCheck=health_check_uri),
                ],))))
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'Patch', request)],
    )


if __name__ == '__main__':
  test_case.main()
