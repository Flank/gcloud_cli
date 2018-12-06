# -*- coding: utf-8 -*- #
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
"""Tests for the instance-groups managed resize subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch


class InstanceGroupManagersResizeTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))

  def testWithTwoInstances(self):
    self.Run('compute instance-groups managed resize group-1 --zone '
             'central2-a --size 3')

    request = self.messages.ComputeInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        zone='central2-a'
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'Resize', request)],
    )

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    self.Run('compute instance-groups managed resize {0} --zone central2-a '
             '--size 3'.format(igm_uri))

    request = self.messages.ComputeInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        zone='central2-a'
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'Resize', request)],
    )

  def testZonePrompt(self):
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
    self.WriteInput('3\n')
    self.Run('compute instance-groups managed resize group-1 --size 3')
    request = self.messages.ComputeInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        zone='central1-a'
    )
    zones_list_request = self.messages.ComputeZonesListRequest(
        maxResults=500,
        project='my-project')
    regions_list_request = self.messages.ComputeRegionsListRequest(
        maxResults=500,
        project='my-project')
    self.CheckRequests(
        [(self.compute.regions, 'List', regions_list_request)],
        [(self.compute.zones, 'List', zones_list_request)],
        [(self.compute.instanceGroupManagers, 'Resize', request)],
    )

  def testNegativeSize(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --size: Value must be greater than or equal to 0; '
        'received: -3'):
      self.Run(
          'compute instance-groups managed resize group-1 --size -3')

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run('compute instance-groups managed resize group-1 '
               '--zone central2-a --size 1')


class InstanceGroupManagersResizeZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))

  def testZonePrompt(self):
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
    self.WriteInput('3\n')
    self.Run('compute instance-groups managed resize group-1 --size 3')
    request = self.messages.ComputeInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        zone='central1-a'
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.instanceGroupManagers, 'Resize', request)],
    )


class InstanceGroupManagersResizeRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
            self.messages.Region(name='central2'),
        ],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))

  def testWithTwoInstances(self):
    self.Run("""
        compute instance-groups managed resize group-1
            --region central2
            --size 3
        """)

    request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        region='central2'
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Resize', request)],
    )

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/regions/central2/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    self.Run("""
        compute instance-groups managed resize {0}
            --region central2
            --size 3
        """.format(igm_uri))

    request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        region='central2'
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Resize', request)],
    )

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
    self.Run("""
        compute instance-groups managed resize group-1
            --size 3
        """)
    request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        region='central2'
    )
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'Resize', request)],
    )


class InstanceGroupManagersResizeBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
            self.messages.Region(name='central2'),
        ],
    ])
    self.template_1_uri = (
        '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
            self.compute_uri))

  def testRegional(self):
    self.Run("""
        compute instance-groups managed resize group-1
            --region central2
            --size 3
        """)

    request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
        instanceGroupManager='group-1',
        size=3,
        project='my-project',
        region='central2'
    )
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers, 'Resize', request)],
    )

  def testWithNoCreationRetries(self):
    self.Run('compute instance-groups managed resize group-1 --zone '
             'central2-a --size 3 --no-creation-retries')

    request = self.messages.ComputeInstanceGroupManagersResizeAdvancedRequest(
        instanceGroupManager='group-1',
        instanceGroupManagersResizeAdvancedRequest=(
            self.messages.InstanceGroupManagersResizeAdvancedRequest(
                targetSize=3,
                noCreationRetries=True,
            )
        ),
        project='my-project',
        zone='central2-a'
    )
    self.CheckRequests(
        [(self.compute.instanceGroupManagers, 'ResizeAdvanced', request)],
    )

  def testRegionalResizeNoCreationRetries(self):
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run('compute instance-groups managed resize group-1 --region '
               'central2-a --size 3 --no-creation-retries')


if __name__ == '__main__':
  test_case.main()
