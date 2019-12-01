# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the packet mirrorings update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class UpdateTestBeta(test_base.BaseTest):
  _PM_NAME = 'my-pm'
  _REGION = 'us-central1'
  _ZONE = 'us-central1-a'
  _PROJECT = 'my-project'
  _DEFAULT_FORWARDING_RULE = 'fr1'
  _DEFAULT_NETWORK = 'default'

  def SetUp(self):
    self.api_version = 'beta'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.compute = self.compute_beta

  def testUpdate(self):
    self._SetNextGetResult(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1'],
            instances=[],
            subnetworks=[],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
    )

    self.Run("""\
        compute packet-mirrorings update my-pm --region us-central1
        --priority 1 --no-enable --description 'Mirror the packets'
        """)

    self._CheckGetAndPatchRequests(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1'],
            instances=[],
            subnetworks=[],
        ),
        filter=self.messages.PacketMirroringFilter(),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.FALSE,
        priority=1,
        description='Mirror the packets')

  def testUpdate_AddRepeatedFields(self):
    self._SetNextGetResult()

    self.Run("""\
    compute packet-mirrorings update my-pm --region us-central1
    --add-mirrored-instances
    projects/my-project/zones/us-central1-a/instances/i1
    --add-mirrored-tags t1,t2 --add-mirrored-subnets sn1
    --add-filter-protocols tcp,udp --add-filter-cidr-ranges 11.22.0.0/16
    """)

    self._CheckGetAndPatchRequests(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1', 't2'],
            instances=[self._MakeInstanceInfo('i1')],
            subnetworks=[self._MakeSubnetInfo('sn1')],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=self.messages.PacketMirroringFilter(
            cidrRanges=['11.22.0.0/16'], IPProtocols=['tcp', 'udp']))

  def testUpdate_RemoveRepeatedFields(self):
    self._SetNextGetResult(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1', 't2'],
            instances=[
                self._MakeInstanceInfo('i1'),
                self._MakeInstanceInfo('i2')
            ],
            subnetworks=[
                self._MakeSubnetInfo('sn1'),
                self._MakeSubnetInfo('sn2')
            ],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=self.messages.PacketMirroringFilter(
            cidrRanges=['11.22.33.0/24', '22.33.0.0/16'],
            IPProtocols=['tcp', 'icmp']))

    self.Run("""\
    compute packet-mirrorings update my-pm --region us-central1
    --remove-mirrored-instances
    projects/my-project/zones/us-central1-a/instances/i1
    --remove-mirrored-tags t1 --remove-mirrored-subnets sn1
    --remove-filter-protocols tcp --remove-filter-cidr-ranges 11.22.33.0/24
    """)

    self._CheckGetAndPatchRequests(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t2'],
            instances=[self._MakeInstanceInfo('i2')],
            subnetworks=[self._MakeSubnetInfo('sn2')],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=self.messages.PacketMirroringFilter(
            cidrRanges=['22.33.0.0/16'], IPProtocols=['icmp']))

  def testUpdate_ClearRepeatedFields(self):
    self._SetNextGetResult(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1', 't2'],
            instances=[
                self._MakeInstanceInfo('i1'),
                self._MakeInstanceInfo('i2')
            ],
            subnetworks=[
                self._MakeSubnetInfo('sn1'),
                self._MakeSubnetInfo('sn2')
            ],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=self.messages.PacketMirroringFilter(
            cidrRanges=['11.22.33.0/24', '22.33.0.0/16'],
            IPProtocols=['tcp', 'icmp']))

    self.Run("""\
    compute packet-mirrorings update my-pm --region us-central1
    --clear-mirrored-instances --clear-mirrored-tags --clear-mirrored-subnets
    --clear-filter-protocols --clear-filter-cidr-ranges
    """)

    self._CheckGetAndPatchRequests(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=[],
            instances=[],
            subnetworks=[],
        ),
        filter=self.messages.PacketMirroringFilter(),
    )

  def testUpdate_SetRepeatedFields(self):
    self._SetNextGetResult()

    self.Run("""\
    compute packet-mirrorings update my-pm --region us-central1
    --set-mirrored-instances
    projects/my-project/zones/us-central1-a/instances/i1
    --set-mirrored-tags t1,t2 --set-mirrored-subnets sn1
    --set-filter-protocols tcp,udp --set-filter-cidr-ranges 11.22.0.0/16
    """)

    self._CheckGetAndPatchRequests(
        mirroredResources=self.messages.PacketMirroringMirroredResourceInfo(
            tags=['t1', 't2'],
            instances=[self._MakeInstanceInfo('i1')],
            subnetworks=[self._MakeSubnetInfo('sn1')],
        ),
        enable=self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=self.messages.PacketMirroringFilter(
            cidrRanges=['11.22.0.0/16'], IPProtocols=['tcp', 'udp']))

  def _SetNextGetResult(self, **kwargs):
    pm = self._MakeBasicPacketMirroring()
    pm.update(kwargs)
    self.make_requests.side_effect = iter(
        [[self.messages.PacketMirroring(**pm)], []])

  def _CheckGetAndPatchRequests(self, **kwargs):
    expected_get_request = [
        (self.compute.packetMirrorings, 'Get',
         self.messages.ComputePacketMirroringsGetRequest(
             project=self._PROJECT,
             region=self._REGION,
             packetMirroring=self._PM_NAME))
    ]

    pm = self._MakeBasicPacketMirroring()
    pm.update(kwargs)
    expected_update_request = [
        (self.compute.packetMirrorings, 'Patch',
         self.messages.ComputePacketMirroringsPatchRequest(
             project=self._PROJECT,
             region=self._REGION,
             packetMirroring=self._PM_NAME,
             packetMirroringResource=self.messages.PacketMirroring(**pm)))
    ]
    self.CheckRequests(expected_get_request, expected_update_request)

  def _MakeBasicPacketMirroring(self):
    return {
        'name':
            self._PM_NAME,
        'network':
            self.messages.PacketMirroringNetworkInfo(
                url=('https://compute.googleapis.com/compute/%s/'
                     'projects/%s/global/networks/%s' %
                     (self.api_version, self._PROJECT, self._DEFAULT_NETWORK))),
        'collectorIlb':
            self.messages.PacketMirroringForwardingRuleInfo(
                url=('https://compute.googleapis.com/compute/%s/'
                     'projects/%s/regions/%s/forwardingRules/%s' %
                     (self.api_version, self._PROJECT, self._REGION,
                      self._DEFAULT_FORWARDING_RULE))),
        'mirroredResources':
            self.messages.PacketMirroringMirroredResourceInfo(
                tags=[],
                instances=[],
                subnetworks=[],
            ),
        'filter':
            self.messages.PacketMirroringFilter(),
        'enable':
            self.messages.PacketMirroring.EnableValueValuesEnum.TRUE,
    }

  def _MakeInstanceInfo(self, instance):
    return self.messages.PacketMirroringMirroredResourceInfoInstanceInfo(
        url='https://compute.googleapis.com/compute/%s/'
        'projects/%s/zones/%s/instances/%s' %
        (self.api_version, self._PROJECT, self._ZONE, instance))

  def _MakeSubnetInfo(self, subnet):
    return self.messages.PacketMirroringMirroredResourceInfoSubnetInfo(
        url='https://compute.googleapis.com/compute/%s/'
        'projects/%s/regions/%s/subnetworks/%s' %
        (self.api_version, self._PROJECT, self._REGION, subnet))


class UpdateTestAlpha(UpdateTestBeta):

  def SetUp(self):
    self.api_version = 'alpha'
    self.SelectApi(self.api_version)
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.compute = self.compute_alpha


if __name__ == '__main__':
  test_case.main()
