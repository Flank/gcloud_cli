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
"""Tests for the instance-groups managed update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch

import six


class InstanceGroupManagersUpdateZonalTestGA(test_base.BaseTest,
                                             sdk_test_base.WithLogCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1')
    self.project_name = 'my-project'
    self.zone_name = 'us-central2-a'
    self.igm_name = 'group-1'
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

  def _getAutohealingPolicy(self, health_check, initial_delay):
    return self.messages.InstanceGroupManagerAutoHealingPolicy(
        healthCheck=health_check, initialDelaySec=initial_delay)

  def _checkGetAndPatchRequests(self,
                                disks=None,
                                health_check=None,
                                initial_delay=None,
                                clear_autohealing=False,
                                with_empty_stateful_policy=False):
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

    stateful_policy = (
        self._GetStatefulPolicyWithDisks(disks=[]) if with_empty_stateful_policy
        else None)
    if disks is not None:
      stateful_policy = self._GetStatefulPolicyWithDisks(disks)

    self.CheckRequests([
        (self.compute.instanceGroupManagers, 'Get', self._getGetRequestStub())
    ], [(self.compute.instanceGroupManagers, 'Patch',
         self._getPatchRequestStub(stateful_policy, autohealing_policies))])

  def _setInitialIgm(self):
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

  def _setNoInitialIgm(self):

    def MakeRequests(*_, **kwargs):
      kwargs['errors'].append((404, 'Not Found'))
      yield

    self.make_requests.side_effect = MakeRequests

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

  def _MakePreservedStateDisksMapEntry(self, stateful_disk):
    auto_delete_map = {
        'never':
            self.messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum.NEVER,
        'on-permanent-instance-deletion':
            self.messages.StatefulPolicyPreservedStateDiskDevice
            .AutoDeleteValueValuesEnum.ON_PERMANENT_INSTANCE_DELETION
    }
    disk_proto = self.messages.StatefulPolicyPreservedState \
        .DisksValue.AdditionalProperty(
            key=stateful_disk['device_name'],
            value=self.messages.StatefulPolicyPreservedStateDiskDevice())
    if 'auto_delete' in stateful_disk:
      disk_proto.value.autoDelete = (
          auto_delete_map[stateful_disk['auto_delete']])
    return disk_proto

  def _GetStatefulPolicyWithDisks(self, disks=None):
    preserved_state = self.messages.StatefulPolicyPreservedState(
        disks=self.messages.StatefulPolicyPreservedState.DisksValue(
            additionalProperties=[]))
    if disks:
      preserved_state.disks.additionalProperties = [
          self._MakePreservedStateDisksMapEntry(stateful_disk)
          for stateful_disk in disks
      ]
    return self.messages.StatefulPolicy(preservedState=preserved_state)

  def _checkGetAndUpdateRequests(self,
                                 with_empty_stateful_policy=False,
                                 health_check=None,
                                 initial_delay=None):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._GetStatefulPolicyWithDisks(disks=[])
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

  def _createStatefulDiskDict(self, device_name, auto_delete=None):
    stateful_dict = {'device_name': device_name}
    if auto_delete:
      stateful_dict['auto_delete'] = auto_delete
    return stateful_dict

  def _ParseDiskDictArgs(self, disks):
    stateful_disk_dicts = []
    for disk in disks:
      arg_dict = disk
      if isinstance(disk, six.string_types):
        arg_dict = {'device_name': disk}
      stateful_disk_dicts.append(arg_dict)
    return stateful_disk_dicts

  def _setInitialIgmWithStatefulPolicy(self, *disks):
    """Set intial IGM with stateful policy.

    Args:
      *disks: A list of Strings (device_names) or a list of dicts (in the format
        {'device_name': 'disk1', 'auto_delete':
          'on-permanent-instance-deletion'}) of disks to set in the stateful
          policy
    """
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone=self.zone_name,
        statefulPolicy=self._GetStatefulPolicyWithDisks(
            self._ParseDiskDictArgs(disks)))
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def testUpdateAddStatefulDisk(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-1,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(disks=[
        self._createStatefulDiskDict('disk-1', 'on-permanent-instance-deletion')
    ])

  def testUpdateAddStatefulMultipleDisks(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-1
          --stateful-disk device-name=disk-2,auto-delete=never
          --stateful-disk device-name=disk-3,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(disks=[
        self._createStatefulDiskDict('disk-1'),
        self._createStatefulDiskDict('disk-2', 'never'),
        self._createStatefulDiskDict('disk-3', 'on-permanent-instance-deletion')
    ])

  def testUpdateAddStatefulMultipleDisks_userProvidesDuplicates(self):
    self._setInitialIgm()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'Invalid value for [--stateful-disk]: '
        '[device-name] `disk-1` is not unique in the collection'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --stateful-disk device-name=disk-1
            --stateful-disk device-name=disk-1,auto-delete=never
            --stateful-disk device-name=disk-3,auto-delete=never
          """.format(*self.scope_params))

  def testUpdateAddStatefulDiskToExistingPolicy(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-2,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(disks=[
        self._createStatefulDiskDict('disk-1'),
        self._createStatefulDiskDict('disk-2', 'on-permanent-instance-deletion')
    ])

  def testUpdateStatefulDiskPatchesAutoDelete(self):
    self._setInitialIgmWithStatefulPolicy({
        'device_name': 'disk-1',
        'auto_delete': 'on-permanent-instance-deletion'
    })
    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-1
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(disks=[
        self._createStatefulDiskDict('disk-1', 'on-permanent-instance-deletion')
    ])

  def testUpdateAddStatefulDiskToExistingPolicy_sameDisk(self):
    self._setInitialIgmWithStatefulPolicy('disk-1')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-1,auto-delete=on-permanent-instance-deletion
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(disks=[
        self._createStatefulDiskDict('disk-1', 'on-permanent-instance-deletion')
    ])

  def testUpdateRemoveStatefulDiskWithoutStatefulPolicy_throws(self):
    self._setInitialIgm()
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

    self._checkGetAndPatchRequests(
        disks=[self._createStatefulDiskDict('disk-2')])

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

    self._checkGetAndPatchRequests(
        disks=[self._createStatefulDiskDict('disk-4')])

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
    self._setInitialIgm()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'You cannot simultaneously add and remove the same device names'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --stateful-disk device-name=disk-1
            --remove-stateful-disks disk-1
          """.format(*self.scope_params))

  def testUpdateNoStatefulPolicy_createsUpdateRequest(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests()

  def testUpdateRemoveAllStatefulDisksFromStatefulPolicy_createsPatchRequest(
      self):
    self._setInitialIgmWithStatefulPolicy('disk-1', 'disk-2')

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --remove-stateful-disks disk-1,disk-2
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(with_empty_stateful_policy=True)

  def testUpdateWithHealthCheckAndStatefulDisk(self):
    self._setInitialIgm()

    health_check_uri = (
        '{0}/projects/my-project/global/healthChecks/health-check-1'.format(
            self.compute_uri))
    self.Run("""
        compute instance-groups managed update group-1
        --{} {}
        --health-check health-check-1
        --stateful-disk device-name=disk-1
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(
        disks=[self._createStatefulDiskDict('disk-1')],
        health_check=health_check_uri)

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
        """.format(*self.scope_params))
    self._checkGetAndPatchRequests(
        health_check=health_check_uri2, initial_delay=120)

  def testUpdateWhenIgmDoesNotExist_throws(self):
    self._setNoInitialIgm()

    with self.assertRaisesRegex(
        managed_instance_groups_utils.ResourceNotFoundException,
        'Could not fetch resource:'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
          """.format(*self.scope_params))

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run(
          """compute instance-groups managed update group-1 --{} {}""".format(
              *self.scope_params))

  def testUpdateWithHealthCheck(self):
    self._setInitialIgm()

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
    self._setInitialIgm()

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
    self._setInitialIgm()

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
          compute instance-groups managed update group-1
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


class InstanceGroupManagersUpdateZonalTestBeta(
    InstanceGroupManagersUpdateZonalTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    InstanceGroupManagersUpdateZonalTestGA.SetUp(self)
    self.SelectApi('beta')


class InstanceGroupManagersUpdateZonalTestAlpha(
    InstanceGroupManagersUpdateZonalTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    InstanceGroupManagersUpdateZonalTestBeta.SetUp(self)
    self.SelectApi('alpha')

  def testUpdateSetDistributionTargetShapeForZonalScope_throws(self):
    self._setInitialIgm()

    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Flag --target-distribution-shape may be specified for regional '
        'managed instance groups only.'):
      self.Run("""
          compute instance-groups managed update group-1
            --zone us-central2-a
            --target-distribution-shape ANY
          """)


class InstanceGroupManagersUpdateRegionalTestGA(
    InstanceGroupManagersUpdateZonalTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1')
    self.project_name = 'my-project'
    self.region_name = 'us-central2'
    self.igm_name = 'group-1'
    self.scope_params = ('region', self.region_name)

  def testUpdateChangeInstanceRedistributionType(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --instance-redistribution-type NONE
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(
        update_policy=self.messages.InstanceGroupManagerUpdatePolicy(
            instanceRedistributionType=self.messages
            .InstanceGroupManagerUpdatePolicy
            .InstanceRedistributionTypeValueValuesEnum.NONE))

  def testUpdateInstanceRedistributionTypeForZonalScope_throws(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1', zone=self.zone_name)
    self.make_requests.side_effect = iter([[igm], []])
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Flag --instance-redistribution-type may be specified for regional '
        'managed instance groups only.'):
      self.Run("""
          compute instance-groups managed update group-1
            --zone us-central2-a
            --instance-redistribution-type PROACTIVE
          """)

  def _getGetRequestStub(self):
    return self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager=self.igm_name,
        project=self.project_name,
        region=self.region_name)

  def _getPatchRequestStub(self,
                           stateful_policy=None,
                           update_policy=None,
                           autohealing_policies=None,
                           distribution_policy=None):
    igm_resource = self.messages.InstanceGroupManager(
        updatePolicy=update_policy)
    if stateful_policy is not None:
      igm_resource.statefulPolicy = stateful_policy
    if autohealing_policies is not None:
      igm_resource.autoHealingPolicies = autohealing_policies
    if distribution_policy is not None:
      igm_resource.distributionPolicy = distribution_policy
    return self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=igm_resource,
        project=self.project_name,
        region=self.region_name)

  def _checkGetAndPatchRequests(self,
                                disks=None,
                                update_policy=None,
                                health_check=None,
                                initial_delay=None,
                                clear_autohealing=False,
                                with_empty_stateful_policy=False,
                                distribution_policy=None):
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

    stateful_policy = (
        self._GetStatefulPolicyWithDisks(disks=[]) if with_empty_stateful_policy
        else None)
    if disks is not None:
      stateful_policy = self._GetStatefulPolicyWithDisks(
          self._ParseDiskDictArgs(disks))

    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.regionInstanceGroupManagers, 'Patch',
                         self._getPatchRequestStub(
                             stateful_policy=stateful_policy,
                             update_policy=update_policy,
                             autohealing_policies=autohealing_policies,
                             distribution_policy=distribution_policy))])

  def _setInitialIgm(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
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

  def _checkGetAndUpdateRequests(self,
                                 with_empty_stateful_policy=False,
                                 update_policy=None,
                                 health_check=None,
                                 initial_delay=None):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._GetStatefulPolicyWithDisks()
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

  def _setInitialIgmWithStatefulPolicy(self, *disks):
    """Set intial IGM with stateful policy.

    Args:
      *disks: A list of Strings (device_names) or a list of dicts (in the format
        {'device_name': 'disk1', 'auto_delete':
          'on-permanent-instance-deletion'}) of disks to set in the stateful
          policy
    """
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
        statefulPolicy=self._GetStatefulPolicyWithDisks(
            self._ParseDiskDictArgs(disks)),
    )
    self.make_requests.side_effect = iter([[
        igm,
    ], []])

  def testUpdateAddStatefulDiskAndChangeInstanceRedistributionType(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --stateful-disk device-name=disk-1
          --instance-redistribution-type NONE
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(
        disks=[self._createStatefulDiskDict('disk-1')],
        update_policy=self.messages.InstanceGroupManagerUpdatePolicy(
            instanceRedistributionType=self.messages
            .InstanceGroupManagerUpdatePolicy
            .InstanceRedistributionTypeValueValuesEnum.NONE))

  def testUpdateAddStatefulDiskWhenInstanceRedistributionTypeProactive(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
        updatePolicy=self.messages.InstanceGroupManagerUpdatePolicy(
            instanceRedistributionType=self.messages.
            InstanceGroupManagerUpdatePolicy.
            InstanceRedistributionTypeValueValuesEnum.PROACTIVE))
    self.make_requests.side_effect = iter([[igm], []])
    with self.assertRaisesRegex(
        exceptions.Error,
        'Stateful regional IGMs cannot use proactive instance redistribution'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --stateful-disk device-name=disk-1
          """.format(*self.scope_params))

  def testUpdateAddStatefulDiskWhenReplacementMethodSubstitute(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        region=self.region_name,
        updatePolicy=self.messages.InstanceGroupManagerUpdatePolicy(
            type=self.messages.
            InstanceGroupManagerUpdatePolicy.TypeValueValuesEnum.PROACTIVE,
            replacementMethod=self.messages.InstanceGroupManagerUpdatePolicy.
            ReplacementMethodValueValuesEnum.SUBSTITUTE))
    self.make_requests.side_effect = iter([[igm], []])
    with self.assertRaisesRegex(
        exceptions.Error,
        'Stateful IGMs cannot use SUBSTITUTE replacement method'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
            --stateful-disk device-name=disk-1
          """.format(*self.scope_params))


class InstanceGroupManagersUpdateRegionalTestBeta(
    InstanceGroupManagersUpdateRegionalTestGA,
    InstanceGroupManagersUpdateZonalTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    InstanceGroupManagersUpdateRegionalTestGA.SetUp(self)
    self.SelectApi('beta')


class InstanceGroupManagersUpdateRegionalTestAlpha(
    InstanceGroupManagersUpdateRegionalTestBeta,
    InstanceGroupManagersUpdateZonalTestAlpha):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    InstanceGroupManagersUpdateRegionalTestBeta.SetUp(self)
    self.SelectApi('alpha')

  def _createDistributionPolicy(self, target_shape):
    distribution_policy = self.messages.DistributionPolicy()
    distribution_policy.targetShape = target_shape
    return distribution_policy

  def testUpdateSetDistributionTargetShape(self):
    self._setInitialIgm()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --target-distribution-shape ANY
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests(
        distribution_policy=self._createDistributionPolicy(
            target_shape=self.messages.DistributionPolicy
            .TargetShapeValueValuesEnum.ANY))


if __name__ == '__main__':
  test_case.main()
