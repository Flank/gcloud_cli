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

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base

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

  def _getPatchRequestStub(self, stateful_policy=None):
    return self.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=(
            self.messages.InstanceGroupManager(statefulPolicy=stateful_policy)),
        project=self.project_name,
        zone=self.zone_name)

  def _getUpdateRequestStub(self, stateful_policy=None):
    return self.messages.ComputeInstanceGroupManagersUpdateRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            name=self.igm_name,
            zone=self.zone_name,
            statefulPolicy=stateful_policy)),
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

  def _checkGetAndPatchRequests(self, *disks):
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.instanceGroupManagers, 'Patch',
                         self._getPatchRequestStub(
                             self._getStatefulPolicyWithDisks(list(disks))))])

  def _checkGetAndUpdateRequests(self, with_empty_stateful_policy=False):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._getStatefulPolicyWithDisks()
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.instanceGroupManagers, 'Update',
                         self._getUpdateRequestStub(stateful_policy))])

  def _setInitialIgmNoStatefulPolicy(self):
    igm = self.messages.InstanceGroupManager(
        name='group-1',
        zone=self.zone_name,
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

    self._checkGetAndPatchRequests('disk-1')

  def testUpdateAddStatefulMultipleDisks(self):
    self._setInitialIgmNoStatefulPolicy()

    self.Run("""
        compute instance-groups managed update group-1
          --{} {}
          --add-stateful-disks disk-1,disk-2,disk-3
        """.format(*self.scope_params))

    self._checkGetAndPatchRequests('disk-1', 'disk-2', 'disk-3')

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

    self._checkGetAndPatchRequests('disk-1', 'disk-2')

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

    self._checkGetAndPatchRequests('disk-2')

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

    self._checkGetAndPatchRequests('disk-4')

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

    self._checkGetAndPatchRequests('disk-1')

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

  def testUpdateNoChanges_throws(self):
    self._setInitialIgmWithStatefulPolicy()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'No update specified, you need to use at least one flag from:'
        ' --add-stateful-disks, --remove-stateful-disks, --stateful-names,'
        ' --no-stateful-names'):
      self.Run("""
          compute instance-groups managed update group-1
            --{} {}
          """.format(*self.scope_params))


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

  def _getPatchRequestStub(self, stateful_policy=None):
    return self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=(
            self.messages.InstanceGroupManager(statefulPolicy=stateful_policy)),
        project=self.project_name,
        region=self.region_name)

  def _getUpdateRequestStub(self, stateful_policy=None):
    return self.messages.ComputeRegionInstanceGroupManagersUpdateRequest(
        instanceGroupManager=self.igm_name,
        instanceGroupManagerResource=(self.messages.InstanceGroupManager(
            name=self.igm_name,
            region=self.region_name,
            statefulPolicy=stateful_policy)),
        project=self.project_name,
        region=self.region_name)

  def _checkGetAndPatchRequests(self, *disks):
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.regionInstanceGroupManagers, 'Patch',
                         self._getPatchRequestStub(
                             self._getStatefulPolicyWithDisks(list(disks))))])

  def _checkGetAndUpdateRequests(self, with_empty_stateful_policy=False):
    stateful_policy = None
    if with_empty_stateful_policy:
      stateful_policy = self._getStatefulPolicyWithDisks()
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Get',
                         self._getGetRequestStub())],
                       [(self.compute.regionInstanceGroupManagers, 'Update',
                         self._getUpdateRequestStub(stateful_policy))])

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


if __name__ == '__main__':
  test_case.main()
