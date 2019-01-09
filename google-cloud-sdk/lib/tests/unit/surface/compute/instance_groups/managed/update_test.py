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
"""Tests for the instance-groups managed update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch

API_VERSION = 'alpha'


class InstanceGroupManagersUpdateZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)

    self.project_name = 'my-project'
    self.zone_name = 'us-central2-a'
    self.igm_name = 'group-1'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.scope_params = ('zone', self.zone_name)

  def _getGetRequestStub(self):
    return self.messages.ComputeInstanceGroupManagersGetRequest(
        instanceGroupManager=self.igm_name,
        project=self.project_name,
        zone=self.zone_name)

  def _getPatchRequestStub(self,
                           stateful_policy=None,
                           autohealing_policies=None):
    igm_resource = self.messages.InstanceGroupManager()
    if stateful_policy is not None:
      igm_resource.statefulPolicy = stateful_policy
    if autohealing_policies is not None:
      igm_resource.autoHealingPolicies = autohealing_policies
    return self.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=igm_resource,
        project=self.project_name,
        zone=self.zone_name)

  def _getUpdateRequestStub(self,
                            stateful_policy=None,
                            autohealing_policies=None):
    igm_resource = (
        self.messages.InstanceGroupManager(
            name=self.igm_name,
            zone=self.zone_name,
            # Update can be only send when we need to modify StatefulPolicy
            # so it's always set.
            statefulPolicy=stateful_policy))
    if autohealing_policies is not None:
      igm_resource.autoHealingPolicies = autohealing_policies
    return self.messages.ComputeInstanceGroupManagersUpdateRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=igm_resource,
        project=self.project_name,
        zone=self.zone_name)

  def _getStatefulPolicyWithDisks(self, disks=None):
    preserved_resources = None
    if disks:
      preserved_resources = self.messages.StatefulPolicyPreservedResources(
          disks=[
              self.messages.StatefulPolicyPreservedDisk(deviceName=device_name)
              for device_name in disks
          ])
    return self.messages.StatefulPolicy(preservedResources=preserved_resources)

  def _getAutohealingPolicy(self, health_check, initial_delay):
    return self.messages.InstanceGroupManagerAutoHealingPolicy(
        healthCheck=health_check, initialDelaySec=initial_delay)

  def _checkGetAndPatchRequests(self,
                                disks=None,
                                health_check=None,
                                initial_delay=None,
                                clear_autohealing=False):
    autohealing_policies = None
    if clear_autohealing or \
        health_check is not None or initial_delay is not None:
      autohealing_policies = [
          self.messages.InstanceGroupManagerAutoHealingPolicy()
      ]
      if health_check:
        autohealing_policies[0].healthCheck = health_check
      if initial_delay:
        autohealing_policies[0].initialDelaySec = initial_delay

    stateful_policy = None
    if disks is not None:
      stateful_policy = self._getStatefulPolicyWithDisks(disks)

    self.CheckRequests([
        (self.compute.instanceGroupManagers, 'Get', self._getGetRequestStub())
    ], [(self.compute.instanceGroupManagers, 'Patch',
         self._getPatchRequestStub(stateful_policy, autohealing_policies))])

  def _checkGetAndUpdateRequests(self,
                                 with_empty_stateful_policy=False,
                                 health_check=None,
                                 initial_delay=None):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._getStatefulPolicyWithDisks()
    autohealing_policies = None
    if health_check is not None or initial_delay is not None:
      autohealing_policies = [
          self.messages.InstanceGroupManagerAutoHealingPolicy()
      ]
      if health_check:
        autohealing_policies[0].healthCheck = health_check
      if initial_delay:
        autohealing_policies[0].initialDelaySec = initial_delay

    self.CheckRequests([
        (self.compute.instanceGroupManagers, 'Get', self._getGetRequestStub())
    ], [(self.compute.instanceGroupManagers, 'Update',
         self._getUpdateRequestStub(stateful_policy, autohealing_policies))])

  def _setInitialIgmNoStatefulPolicy(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone=self.zone_name,
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def _setInitialIgmWithAutohealingPolicy(self, health_check, initial_delay):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone=self.zone_name,
        autoHealingPolicies=[
            self._getAutohealingPolicy(health_check, initial_delay)
        ],
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def _setInitialIgmWithStatefulPolicy(self, *disks):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone=self.zone_name,
        statefulPolicy=self._getStatefulPolicyWithDisks(list(disks)),
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def _setNoInitialIgm(self):

    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield

    self.make_requests.side_effect = MakeRequests

  def testUpdateAddStatefulDisk(self):
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --add-stateful-disks disk-1
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-1'])

  def testUpdateAddStatefulMultipleDisks(self):
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --add-stateful-disks disk-1,disk-2,disk-3
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-1', 'disk-2', 'disk-3'])

  def testUpdateAddStatefulMultipleDisks_userProvidesDuplicates(self):
    self._setInitialIgmNoStatefulPolicy()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'When adding device names to Stateful Policy, please provide each '
        'name exactly once.'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --add-stateful-disks disk-1,disk-1,disk-3
          """.format(*self.scope_params))

  def testUpdateAddStatefulDiskToExistingPolicy(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --add-stateful-disks disk-2
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-1', 'disk-2'])

  def testUpdateAddStatefulDiskToExistingPolicy_sameDisk(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'are currently set as stateful, so they cannot be added to Stateful '
        'Policy'
    ):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --add-stateful-disks disk-1
          """.format(*self.scope_params))

  def testUpdateRemoveStatefulDiskWithoutStatefulPolicy_throws(self):
    self._setInitialIgmNoStatefulPolicy()
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'are not currently set as stateful, so they cannot be removed from '
        'Stateful Policy.'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --remove-stateful-disks disk-1
          """.format(*self.scope_params))

  def testUpdateRemoveStatefulDiskFromStatefulPolicy(self):
    self._setInitialIgmWithStatefulPolicy('disk-1', 'disk-2')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --remove-stateful-disks disk-1
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-2'])

  def testUpdateRemoveStatefulDiskWithStatefulPolicy_diskNotInPolicy_throws(
      self):
    self._setInitialIgmWithStatefulPolicy('disk-1')
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'are not currently set as stateful, so they cannot be removed from '
        'Stateful Policy.'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --remove-stateful-disks disk-2
          """.format(*self.scope_params))

  def testUpdateRemoveStatefulMultipleDisksFromStatefulPolicy(self):
    self._setInitialIgmWithStatefulPolicy('disk-1', 'disk-2', 'disk-3',
                                          'disk-4')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --remove-stateful-disks disk-1,disk-2,disk-3
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-4'])

  def testUpdateRemoveStatefulDisksFromStatefulPolicy_userProvidesDuplicates(
      self):
    self._setInitialIgmWithStatefulPolicy('disk-1', 'disk-2', 'disk-3')

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'When removing device names from Stateful Policy, please provide '
        'each name exactly once.'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --remove-stateful-disks disk-1,disk-1,disk-3
          """.format(*self.scope_params))

  def testUpdateAddAndRemoveStatefulDisk_throws(self):
    self._setInitialIgmNoStatefulPolicy()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'You cannot simultaneously add and remove the same device names'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --add-stateful-disks disk-1
            --remove-stateful-disks disk-1
          """.format(*self.scope_params))

  def testUpdateNoStatefulNamesNoStatefulPolicy_createsUpdateRequest(self):
    # TODO(b/70314588): Fix this test to expect Patch instead of Update.
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --no-stateful-names
        """.format(*self.scope_params))

    self._checkGetAndUpdateRequests()

  def testUpdateRemoveAndNoStatefulNames_createsUpdateRequest(self):
    # TODO(b/70314588): Fix this test to expect Patch instead of Update.
    self._setInitialIgmWithStatefulPolicy('disk-1')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --remove-stateful-disks disk-1
          --no-stateful-names
        """.format(*self.scope_params))

    self._checkGetAndUpdateRequests()

  def testUpdateRemoveAllStatefulDisksFromStatefulPolicy_createsUpdateRequest(
      self):
    # TODO(b/70314588): Fix this test to expect Patch instead of Update.
    self._setInitialIgmWithStatefulPolicy('disk-1', 'disk-2')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --remove-stateful-disks disk-1,disk-2
        """.format(*self.scope_params))

    self._checkGetAndUpdateRequests(with_empty_stateful_policy=True)

  def testUpdateNoStatefulNamesWithStatefulPolicy_throws(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'Stateful Policy is not empty, so you cannot mark instance names as '
        'non-stateful'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --no-stateful-names
          """.format(*self.scope_params))

  def testUpdateStatefulNamesWithoutStatefulPolicy_setsNames(self):
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-names
        """.format(*self.scope_params))

    self._checkGetAndUpdateRequests(with_empty_stateful_policy=True)

  def testUpdateStatefulNamesWithStatefulPolicy_preservesPolicy(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-names
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(['disk-1'])

  def testUpdateWhenIgmDoesNotExist_throws(self):
    self._setNoInitialIgm()

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --add-stateful-disks disk-1
          """.format(*self.scope_params))

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""compute instance-groups managed update group-1 --{} {}"""
               .format(*self.scope_params))

  def testUpdateWithHealthCheck(self):
    self._setInitialIgmNoStatefulPolicy()

    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --health-check health-check-1
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(health_check=health_check_uri)

  def testUpdateWithHttpHealthCheck(self):
    self._setInitialIgmNoStatefulPolicy()

    health_check_uri = (
        '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --http-health-check health-check-1
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(health_check=health_check_uri)

  def testUpdateWithHttpsHealthCheck(self):
    self._setInitialIgmNoStatefulPolicy()

    health_check_uri = (
        '{0}/projects/my-project/global/httpsHealthChecks/health-check-1'
        .format(self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --https-health-check health-check-1
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(health_check=health_check_uri)

  def testUpdateWithTwoHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --http-health-check: At most one of --health-check | '
        '--http-health-check | --https-health-check may be specified.'):
      self.Run("""
          compute instance-groups managed set-autohealing group-1
            --{} {}
            --http-health-check health-check-1
            --https-health-check health-check-2
          """.format(*self.scope_params))

  def testUpdateWithInitialDelay_patchSemantics(self):
    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self._setInitialIgmWithAutohealingPolicy(health_check_uri, 120)

    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --initial-delay 10m
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(
        health_check=health_check_uri, initial_delay=10 * 60)

  def testUpdateWithHealthCheck_patchSemantics(self):
    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self._setInitialIgmWithAutohealingPolicy(health_check_uri, 120)

    health_check_uri2 = (
        '{0}/projects/my-project/global/healthChecks/health-check-2'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --health-check health-check-2
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(
        health_check=health_check_uri2, initial_delay=120)

  def testUpdateWithClearAutohealing(self):
    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self._setInitialIgmWithAutohealingPolicy(health_check_uri, 120)

    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --clear-autohealing
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(clear_autohealing=True)

  def testUpdateWithHealthCheckAndStatefulDisk(self):
    self._setInitialIgmNoStatefulPolicy()

    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --health-check health-check-1
        --add-stateful-disks disk-1
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(
        disks=['disk-1'], health_check=health_check_uri)

  def testUpdateWithHealthCheckAndNoStatefulNames(self):
    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self._setInitialIgmWithAutohealingPolicy(health_check_uri, 120)

    health_check_uri2 = (
        '{0}/projects/my-project/global/healthChecks/health-check-2'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --health-check health-check-2
        --no-stateful-names
        """.format(*self.scope_params))
    self._checkGetAndUpdateRequests(
        health_check=health_check_uri2, initial_delay=120)


class InstanceGroupManagersUpdateRegionalTest(
    InstanceGroupManagersUpdateZonalTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)

    self.project_name = 'my-project'
    self.region_name = 'us-central2'
    self.igm_name = 'group-1'
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.scope_params = ('region', self.region_name)

  def _getGetRequestStub(self):
    return self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager=self.igm_name,
        project=self.project_name,
        region=self.region_name)

  def _getPatchRequestStub(self,
                           stateful_policy=None,
                           update_policy=None,
                           autohealing_policies=None):
    igm_resource = self.messages.InstanceGroupManager(
        updatePolicy=update_policy)
    if stateful_policy is not None:
      igm_resource.statefulPolicy = stateful_policy
    if autohealing_policies is not None:
      igm_resource.autoHealingPolicies = autohealing_policies
    return self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=igm_resource,
        project=self.project_name,
        region=self.region_name)

  def _getUpdateRequestStub(self,
                            stateful_policy=None,
                            update_policy=None,
                            autohealing_policies=None):
    igm_resource = (
        self.messages.InstanceGroupManager(
            name=self.igm_name,
            region=self.region_name,
            # Update can be only send when we need to modify StatefulPolicy
            # so it's always set.
            statefulPolicy=stateful_policy,
            updatePolicy=update_policy))
    if autohealing_policies is not None:
      igm_resource.autoHealingPolicies = autohealing_policies

    return self.messages.ComputeRegionInstanceGroupManagersUpdateRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=igm_resource,
        project=self.project_name,
        region=self.region_name)

  def _checkGetAndPatchRequests(self,
                                disks=None,
                                update_policy=None,
                                health_check=None,
                                initial_delay=None,
                                clear_autohealing=False):
    autohealing_policies = None
    if clear_autohealing or \
        health_check is not None or initial_delay is not None:
      autohealing_policies = [
          self.messages.InstanceGroupManagerAutoHealingPolicy()
      ]
      if health_check:
        autohealing_policies[0].healthCheck = health_check
      if initial_delay:
        autohealing_policies[0].initialDelaySec = initial_delay

    stateful_policy = None
    if disks is not None:
      stateful_policy = self._getStatefulPolicyWithDisks(disks)

    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.regionInstanceGroupManagers, 'Patch',
                         self._getPatchRequestStub(
                             stateful_policy=stateful_policy,
                             update_policy=update_policy,
                             autohealing_policies=autohealing_policies))])

  def _checkGetAndUpdateRequests(self,
                                 with_empty_stateful_policy=False,
                                 update_policy=None,
                                 health_check=None,
                                 initial_delay=None):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._getStatefulPolicyWithDisks()
    autohealing_policies = None
    if health_check is not None or initial_delay is not None:
      autohealing_policies = [
          self.messages.InstanceGroupManagerAutoHealingPolicy()
      ]
      if health_check:
        autohealing_policies[0].healthCheck = health_check
      if initial_delay:
        autohealing_policies[0].initialDelaySec = initial_delay

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Get',
          self._getGetRequestStub())],
        [(self.compute.regionInstanceGroupManagers, 'Update',
          self._getUpdateRequestStub(stateful_policy, update_policy,
                                     autohealing_policies))])

  def _setInitialIgmNoStatefulPolicy(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def _setInitialIgmWithStatefulPolicy(self, *disks):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
        statefulPolicy=self._getStatefulPolicyWithDisks(list(disks)),
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def _setInitialIgmWithAutohealingPolicy(self, health_check, initial_delay):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
        autoHealingPolicies=[
            self._getAutohealingPolicy(health_check, initial_delay)
        ],
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def testUpdateAddStatefulDiskAndChangeInstanceRedistributionType(self):
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --add-stateful-disks disk-1
          --instance-redistribution-type none
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(
        ['disk-1'],
        update_policy=self.messages.InstanceGroupManagerUpdatePolicy(
            instanceRedistributionType=self.messages.
            InstanceGroupManagerUpdatePolicy.
            InstanceRedistributionTypeValueValuesEnum.NONE))

  def testUpdateInstanceRedistributionType_createsUpdateRequest(self):
    # TODO(b/70314588): Fix this test to expect Patch instead of Update.
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --no-stateful-names
          --instance-redistribution-type none
        """.format(*self.scope_params))

    self._checkGetAndUpdateRequests(
        with_empty_stateful_policy=False,
        update_policy=self.messages.InstanceGroupManagerUpdatePolicy(
            instanceRedistributionType=self.messages.
            InstanceGroupManagerUpdatePolicy.
            InstanceRedistributionTypeValueValuesEnum.NONE))

  def testUpdateInstanceRedistributionTypeForZonalScope_throws(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Flag --instance-redistribution-type may be specified for regional '
        'managed instance groups only.'):
      self.Run("""
          compute instance-groups managed update group-1
            --zone us-central2-a
            --instance-redistribution-type proactive
          """)


if __name__ == '__main__':
  test_case.main()
