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
"""Tests for the instance-groups managed set-instance-template subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from mock import patch

API_VERSION = 'beta'


class InstanceGroupManagersSetInstanceTemplatesZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
    ])

  def testWithName(self):
    self.Run('compute instance-groups managed set-instance-template group-1 '
             '--zone central2-a --template template-1')

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri)))),
        ))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/zones/central2-a/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    template_uri = ('{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri))
    self.Run('compute instance-groups managed set-instance-template {0} --zone '
             'central2-a --template {1}'.format(igm_uri, template_uri))

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri)))),
        ))
    self.CheckRequests([(self.compute.instanceGroupManagers, 'Patch', request)])

  def testZonePrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter(
        [[
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
         [
             self.messages.Zone(name='central1-a'),
             self.messages.Zone(name='central1-b'),
             self.messages.Zone(name='central2-a'),
         ], []])
    self.WriteInput('5\n')
    self.Run('compute instance-groups managed set-instance-template group-1 '
             ' --template template-1')

    request = (
        self.messages.ComputeInstanceGroupManagersPatchRequest(
            project='my-project',
            zone='central2-a',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri)))),
        ))
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
      self.Run('compute instance-groups managed set-instance-template group-1 '
               '--zone central2-a --template template-1')


class InstanceGroupManagersSetInstanceTemplatesRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [],
    ])

  def testWithName(self):
    self.Run("""
        compute instance-groups managed set-instance-template group-1
            --region central2 --template template-1
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri))))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testWithUri(self):
    igm_uri = ('{0}/projects/my-project/regions/central2/instanceGroupManagers/'
               'group-1'.format(self.compute_uri))
    template_uri = ('{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri))
    self.Run("""
        compute instance-groups managed set-instance-template {0}
            --region central2 --template {1}
        """.format(igm_uri, template_uri))

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri))))))
    self.CheckRequests([(self.compute.regionInstanceGroupManagers, 'Patch',
                         request)])

  def testZonePrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter(
        [[
            self.messages.Region(name='central1'),
            self.messages.Region(name='central2'),
        ],
         [
             self.messages.Zone(name='central1-a'),
             self.messages.Zone(name='central1-b'),
             self.messages.Zone(name='central2-a'),
         ], []])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed set-instance-template group-1
            --template template-1
        """)

    request = (
        self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
            project='my-project',
            region='central2',
            instanceGroupManager='group-1',
            instanceGroupManagerResource=(self.messages.InstanceGroupManager(
                instanceTemplate=(
                    '{0}/projects/my-project/global/instanceTemplates/'
                    'template-1'.format(self.compute_uri))))))
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers, 'Patch', request)],
    )


if __name__ == '__main__':
  test_case.main()
