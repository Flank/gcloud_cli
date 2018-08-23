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
"""Tests for the interconnect locations list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class InterconnectLocationsListTest(sdk_test_base.WithFakeAuth,
                                    cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

    self.location_ref1 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())
    self.location_ref2 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-test',
        project=self.Project())

  def _MakeInterconnectLocation(self,
                                name='default-name',
                                description='Bell-Canada',
                                peeringdb_facility_id='38',
                                address='111 8th Ave',
                                facility_provider='google-partner-provider',
                                facility_provider_facility_id='111 8th',
                                location_ref=None):

    return self.apis_messages.InterconnectLocation(
        name=name,
        description=description,
        peeringdbFacilityId=peeringdb_facility_id,
        address=address,
        facilityProvider=facility_provider,
        facilityProviderFacilityId=facility_provider_facility_id,
        selfLink=location_ref.SelfLink(),
    )

  def testSimpleCase(self):
    self.client.interconnectLocations.List.Expect(
        self.messages.ComputeInterconnectLocationsListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectLocationList(
            items=[
                self._MakeInterconnectLocation(
                    name='eap-lga07',
                    address='Bell Canada 111 8th Ave, Suite 831 New York, '
                    'NY 10011 New York United States',
                    location_ref=self.location_ref1),
                self._MakeInterconnectLocation(
                    name='eap-test',
                    address='Bell Canada 222 8th Ave, Suite 831 New York, '
                    'NY 10011 New York United States',
                    location_ref=self.location_ref2)
            ],))

    self.Run("""
          compute interconnects locations list
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME      DESCRIPTION FACILITY_PROVIDER
          eap-lga07 Bell-Canada google-partner-provider
          eap-test  Bell-Canada google-partner-provider
          """),
        normalize_space=True)
    self.AssertErrEquals('')


class InterconnectLocationsListBetaTest(InterconnectLocationsListTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

    self.location_ref1 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())
    self.location_ref2 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-test',
        project=self.Project())


class InterconnectLocationsListAlphaTest(InterconnectLocationsListTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

    self.location_ref1 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-lga07',
        project=self.Project())
    self.location_ref2 = self.resources.Create(
        'compute.interconnectLocations',
        interconnectLocation='eap-test',
        project=self.Project())


if __name__ == '__main__':
  test_case.main()
