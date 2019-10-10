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
"""Tests for the packet mirrorings create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import utils

messages = core_apis.GetMessagesModule('compute', 'alpha')


class CreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreate(self):
    expected = messages.PacketMirroring(
        name='my-pm',
        priority=999,
        network=messages.PacketMirroringNetworkInfo(
            url=('https://compute.googleapis.com/compute/alpha/'
                 'projects/my-project/global/networks/default')),
        collectorIlb=messages.PacketMirroringForwardingRuleInfo(
            url=('https://compute.googleapis.com/compute/alpha/'
                 'projects/my-project/regions/us-central1/'
                 'forwardingRules/fr1')),
        mirroredResources=messages.PacketMirroringMirroredResourceInfo(
            tags=['t1', 't2'],
            instances=[
                messages.PacketMirroringMirroredResourceInfoInstanceInfo(
                    url='https://compute.googleapis.com/compute/alpha/'
                    'projects/my-project/zones/us-central1-a/'
                    'instances/i1')
            ],
            subnetworks=[
                messages.PacketMirroringMirroredResourceInfoSubnetInfo(
                    url='https://compute.googleapis.com/compute/alpha/'
                    'projects/my-project/regions/us-central1/'
                    'subnetworks/subnet1'),
                messages.PacketMirroringMirroredResourceInfoSubnetInfo(
                    url='https://compute.googleapis.com/compute/alpha/'
                    'projects/other-project/regions/us-central1/'
                    'subnetworks/subnet2')
            ],
        ),
        enable=messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=messages.PacketMirroringFilter(
            cidrRanges=['1.2.3.0/24', '4.5.0.0/16'], IPProtocols=['udp',
                                                                  'tcp']))

    self.Run("""\
        compute packet-mirrorings create my-pm --region us-central1
        --network default --priority 999
        --mirrored-tags t1,t2
        --mirrored-instances
        projects/my-project/zones/us-central1-a/instances/i1
        --mirrored-subnets
        subnet1,projects/other-project/regions/us-central1/subnetworks/subnet2
        --filter-cidr-ranges 1.2.3.0/24,4.5.0.0/16 --filter-protocols udp,tcp
        --enable --collector-ilb fr1
        """)

    self.CheckRequests([(self.compute_alpha.packetMirrorings, 'Insert',
                         messages.ComputePacketMirroringsInsertRequest(
                             packetMirroring=expected,
                             project='my-project',
                             region='us-central1',
                         ))])

  def testAsync(self):
    expected = messages.PacketMirroring(
        name='my-pm',
        network=messages.PacketMirroringNetworkInfo(
            url=('https://compute.googleapis.com/compute/alpha/'
                 'projects/my-project/global/networks/default')),
        collectorIlb=messages.PacketMirroringForwardingRuleInfo(
            url=('https://compute.googleapis.com/compute/alpha/'
                 'projects/my-project/regions/us-central1/'
                 'forwardingRules/fr1')),
        mirroredResources=messages.PacketMirroringMirroredResourceInfo(
            tags=['t1'],
            instances=[],
            subnetworks=[],
        ),
        enable=messages.PacketMirroring.EnableValueValuesEnum.TRUE,
        filter=messages.PacketMirroringFilter()
    )
    api_mock = utils.ComputeApiMock(
        'alpha', project=self.Project()).Start()
    api_mock.batch_responder.ExpectBatch([
        ((self.compute_alpha.packetMirrorings, 'Insert',
          messages.ComputePacketMirroringsInsertRequest(
              packetMirroring=expected,
              project='my-project',
              region='us-central1',
          )),
         self.messages.Operation(
             name='operation-X',
             status=self.messages.Operation.StatusValueValuesEnum.PENDING))
    ])

    result = self.Run("""
        compute packet-mirrorings create my-pm --region us-central1
        --network default --collector-ilb fr1 --mirrored-tags t1 --async
        """)

    self.assertEqual('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Create in progress for packet mirroring [my-pm] '
        '[https://compute.googleapis.com/compute/v1/'
        'projects/my-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n')
    api_mock.Stop()


if __name__ == '__main__':
  test_case.main()
