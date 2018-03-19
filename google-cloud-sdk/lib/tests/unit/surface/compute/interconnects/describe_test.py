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
"""Tests for the interconnects describe subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.interconnects import test_resource_util


class InterconnectsDescribeGATest(test_base.BaseTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.api_version = 'v1'
    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='my-location',
        project=self.Project())

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [
            test_resource_util.MakeInterconnectGA(
                name='my-interconnect1',
                description='description',
                interconnect_type=self.v1_messages.Interconnect.
                InterconnectTypeValueValuesEnum.DEDICATED,
                link_type=self.v1_messages.Interconnect.LinkTypeValueValuesEnum.
                LINK_TYPE_ETHERNET_10G_LR,
                requested_link_count=5,
                location=self.location_ref.SelfLink(),
                interconnect_ref=self.interconnect_ref)
        ],
    ])
    result = self.Run("""
        compute interconnects describe my-interconnect1
        """)

    self.CheckRequests(
        [(self.compute_v1.interconnects, 'Get',
          self.messages.ComputeInterconnectsGetRequest(
              project='my-project', interconnect='my-interconnect1'))],)
    self.assertEquals(result.description, 'description')
    self.assertEquals(result.name, 'my-interconnect1')
    self.assertEquals(str(result.interconnectType), 'DEDICATED')
    self.assertEquals(str(result.linkType), 'LINK_TYPE_ETHERNET_10G_LR')
    self.assertEquals(result.requestedLinkCount, 5)
    self.assertEquals(
        result.selfLink,
        'https://www.googleapis.com/compute/v1/projects/my-project/global/'
        'interconnects/my-interconnect1')
    self.assertEquals(
        result.location,
        'https://www.googleapis.com/compute/v1/projects/my-project/global/'
        'interconnectLocations/my-location')

  def testDescribeWithUri(self):
    self.make_requests.side_effect = iter([
        [
            test_resource_util.MakeInterconnectGA(
                name='my-interconnect1',
                description='description',
                interconnect_type=self.v1_messages.Interconnect.
                InterconnectTypeValueValuesEnum.DEDICATED,
                link_type=self.v1_messages.Interconnect.LinkTypeValueValuesEnum.
                LINK_TYPE_ETHERNET_10G_LR,
                requested_link_count=5,
                location=self.location_ref.SelfLink(),
                interconnect_ref=self.interconnect_ref)
        ],
    ])
    result = self.Run(
        'compute interconnects describe https://www.googleapis.com/compute/'
        'v1/projects/my-project/global/interconnects/my-interconnect1')

    self.CheckRequests(
        [(self.compute_v1.interconnects, 'Get',
          self.messages.ComputeInterconnectsGetRequest(
              project='my-project', interconnect='my-interconnect1'))],)
    self.assertEquals(result.description, 'description')
    self.assertEquals(result.name, 'my-interconnect1')
    self.assertEquals(str(result.interconnectType), 'DEDICATED')
    self.assertEquals(str(result.linkType), 'LINK_TYPE_ETHERNET_10G_LR')
    self.assertEquals(result.requestedLinkCount, 5)
    self.assertEquals(
        result.selfLink,
        'https://www.googleapis.com/compute/v1/projects/my-project/global/'
        'interconnects/my-interconnect1')
    self.assertEquals(
        result.location,
        'https://www.googleapis.com/compute/v1/projects/my-project/global/'
        'interconnectLocations/my-location')


class InterconnectsDescribeBetaTest(test_base.BaseTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.api_version = self.track.prefix
    self.beta_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='my-location',
        project=self.Project())

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [
            test_resource_util.MakeInterconnectBeta(
                name='my-interconnect1',
                description='description',
                interconnect_type=self.beta_messages.Interconnect.
                InterconnectTypeValueValuesEnum.IT_PRIVATE,
                link_type=self.beta_messages.Interconnect.
                LinkTypeValueValuesEnum.LINK_TYPE_ETHERNET_10G_LR,
                requested_link_count=5,
                location=self.location_ref.SelfLink(),
                interconnect_ref=self.interconnect_ref)
        ],
    ])
    result = self.Run("""
        compute interconnects describe my-interconnect1
        """)

    self.CheckRequests(
        [(self.compute_beta.interconnects, 'Get',
          self.messages.ComputeInterconnectsGetRequest(
              project='my-project', interconnect='my-interconnect1'))],)
    self.assertEquals(result.description, 'description')
    self.assertEquals(result.name, 'my-interconnect1')
    self.assertEquals(str(result.interconnectType), 'IT_PRIVATE')
    self.assertEquals(str(result.linkType), 'LINK_TYPE_ETHERNET_10G_LR')
    self.assertEquals(result.requestedLinkCount, 5)
    self.assertEquals(
        result.selfLink,
        'https://www.googleapis.com/compute/beta/projects/my-project/global/'
        'interconnects/my-interconnect1')
    self.assertEquals(
        result.location,
        'https://www.googleapis.com/compute/beta/projects/my-project/global/'
        'interconnectLocations/my-location')

  def testDescribeWithUri(self):
    self.make_requests.side_effect = iter([
        [
            test_resource_util.MakeInterconnectBeta(
                name='my-interconnect1',
                description='description',
                interconnect_type=self.beta_messages.Interconnect.
                InterconnectTypeValueValuesEnum.IT_PRIVATE,
                link_type=self.beta_messages.Interconnect.
                LinkTypeValueValuesEnum.LINK_TYPE_ETHERNET_10G_LR,
                requested_link_count=5,
                location=self.location_ref.SelfLink(),
                interconnect_ref=self.interconnect_ref)
        ],
    ])
    result = self.Run(
        'compute interconnects describe https://www.googleapis.com/compute/'
        'beta/projects/my-project/global/interconnects/my-interconnect1')

    self.CheckRequests(
        [(self.compute_beta.interconnects, 'Get',
          self.messages.ComputeInterconnectsGetRequest(
              project='my-project', interconnect='my-interconnect1'))],)
    self.assertEquals(result.description, 'description')
    self.assertEquals(result.name, 'my-interconnect1')
    self.assertEquals(str(result.interconnectType), 'IT_PRIVATE')
    self.assertEquals(str(result.linkType), 'LINK_TYPE_ETHERNET_10G_LR')
    self.assertEquals(result.requestedLinkCount, 5)
    self.assertEquals(
        result.selfLink,
        'https://www.googleapis.com/compute/beta/projects/my-project/global/'
        'interconnects/my-interconnect1')
    self.assertEquals(
        result.location,
        'https://www.googleapis.com/compute/beta/projects/my-project/global/'
        'interconnectLocations/my-location')


if __name__ == '__main__':
  test_case.main()
