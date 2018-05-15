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
"""Tests for the interconnect create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InterconnectsCreateGATest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='my-location',
        project='my-project')

  def CreateTestInterconnectMessage(self, **kwargs):
    interconnect_msg = {
        'name':
            'my-interconnect',
        'interconnectType':
            self.messages.Interconnect.InterconnectTypeValueValuesEnum.
            DEDICATED,
        'linkType':
            self.messages.Interconnect.LinkTypeValueValuesEnum.
            LINK_TYPE_ETHERNET_10G_LR,
        'requestedLinkCount':
            5,
        'adminEnabled':
            True,
        'location':
            self.location_ref.SelfLink(),
        'customerName':
            'customer-name'
    }
    interconnect_msg.update(kwargs)
    return self.messages.Interconnect(**interconnect_msg)

  def ExpectInterconnectRequest(self, **kwargs):
    self.make_requests.side_effect = iter(
        [[self.CreateTestInterconnectMessage(**kwargs)]])

  def CheckInterconnectRequest(self, **kwargs):
    self.CheckRequests(
        [(self.compute_v1.interconnects, 'Insert',
          self.messages.ComputeInterconnectsInsertRequest(
              project='my-project',
              interconnect=self.CreateTestInterconnectMessage(**kwargs)))])

  def testCreateInterconnect(self):
    self.ExpectInterconnectRequest()

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type DEDICATED '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest()
    self.AssertOutputEquals('')

  def testDescription(self):
    self.ExpectInterconnectRequest(description='this is my interconnect')

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type DEDICATED --admin-enabled '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --description "this is my interconnect" '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(description='this is my interconnect')
    self.AssertOutputEquals('')

  def testCreateWithUri(self):
    self.ExpectInterconnectRequest(description='this is my interconnect')

    self_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect',
        project='my-project')
    self.Run('compute interconnects create ' + self_ref.SelfLink() +
             ' --interconnect-type DEDICATED --admin-enabled --location '
             'my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --description "this is my interconnect" '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(description='this is my interconnect')
    self.AssertOutputEquals('')

  def testWithUnsupportedEnumValue(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('compute interconnects create my-interconnect '
               '--interconnect-type IT_PRIVATE '
               '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
               '--requested-link-count 5 --admin-enabled '
               '--customer-name customer-name')


class InterconnectsCreateBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='my-location',
        project='my-project')

  def CreateTestInterconnectMessage(self, **kwargs):
    interconnect_msg = {
        'name':
            'my-interconnect',
        'interconnectType':
            self.messages.Interconnect.InterconnectTypeValueValuesEnum.
            IT_PRIVATE,
        'linkType':
            self.messages.Interconnect.LinkTypeValueValuesEnum.
            LINK_TYPE_ETHERNET_10G_LR,
        'requestedLinkCount':
            5,
        'adminEnabled':
            True,
        'location':
            self.location_ref.SelfLink(),
        'customerName':
            'customer-name'
    }
    interconnect_msg.update(kwargs)
    return self.messages.Interconnect(**interconnect_msg)

  def ExpectInterconnectRequest(self, **kwargs):
    self.make_requests.side_effect = iter(
        [[self.CreateTestInterconnectMessage(**kwargs)]])

  def CheckInterconnectRequest(self, **kwargs):
    self.CheckRequests(
        [(self.compute_beta.interconnects, 'Insert',
          self.messages.ComputeInterconnectsInsertRequest(
              project='my-project',
              interconnect=self.CreateTestInterconnectMessage(**kwargs)))])

  def testCreateInterconnect(self):
    self.ExpectInterconnectRequest()

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type IT_PRIVATE '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest()
    self.AssertOutputEquals('')
    self.AssertErrEquals('WARNING: IT_PRIVATE will be deprecated for '
                         'interconnect-type. Please use DEDICATED instead.\n')

  def testCreateInterconnect_dedicated(self):
    self.ExpectInterconnectRequest(interconnectType=self.messages.Interconnect.
                                   InterconnectTypeValueValuesEnum.DEDICATED)

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type DEDICATED '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(interconnectType=self.messages.Interconnect.
                                  InterconnectTypeValueValuesEnum.DEDICATED)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testDescription(self):
    self.ExpectInterconnectRequest(description='this is my interconnect')

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type IT_PRIVATE --admin-enabled '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --description "this is my interconnect" '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(description='this is my interconnect')
    self.AssertOutputEquals('')
    self.AssertErrEquals('WARNING: IT_PRIVATE will be deprecated for '
                         'interconnect-type. Please use DEDICATED instead.\n')

  def testCreateWithUri(self):
    self.ExpectInterconnectRequest(description='this is my interconnect')

    self_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect',
        project='my-project')
    self.Run('compute interconnects create ' + self_ref.SelfLink() +
             ' --interconnect-type IT_PRIVATE --admin-enabled --location '
             'my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --description "this is my interconnect" '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(description='this is my interconnect')
    self.AssertOutputEquals('')

  def testCreateInterconnect_partner(self):
    self.ExpectInterconnectRequest(interconnectType=self.messages.Interconnect.
                                   InterconnectTypeValueValuesEnum.PARTNER)

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type PARTNER '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(interconnectType=self.messages.Interconnect.
                                  InterconnectTypeValueValuesEnum.PARTNER)
    self.AssertOutputEquals('')

  def testCreateInterconnect_private(self):
    self.ExpectInterconnectRequest()

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type IT_PRIVATE '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest()
    self.AssertOutputEquals('')
    self.AssertErrEquals('WARNING: IT_PRIVATE will be deprecated for '
                         'interconnect-type. Please use DEDICATED instead.\n')


class InterconnectsCreateAlphaTest(InterconnectsCreateBetaTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.location_ref = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='my-location',
        project='my-project')

  def CheckInterconnectRequest(self, **kwargs):
    self.CheckRequests(
        [(self.compute_alpha.interconnects, 'Insert',
          self.messages.ComputeInterconnectsInsertRequest(
              project='my-project',
              interconnect=self.CreateTestInterconnectMessage(**kwargs)))])

  def testCreateInterconnect_dedicated(self):
    self.ExpectInterconnectRequest(interconnectType=self.messages.Interconnect.
                                   InterconnectTypeValueValuesEnum.DEDICATED)

    self.Run('compute interconnects create my-interconnect '
             '--interconnect-type DEDICATED '
             '--location my-location --link-type LINK_TYPE_ETHERNET_10G_LR '
             '--requested-link-count 5 --admin-enabled '
             '--customer-name customer-name')

    self.CheckInterconnectRequest(interconnectType=self.messages.Interconnect.
                                  InterconnectTypeValueValuesEnum.DEDICATED)
    self.AssertOutputEquals('')
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
