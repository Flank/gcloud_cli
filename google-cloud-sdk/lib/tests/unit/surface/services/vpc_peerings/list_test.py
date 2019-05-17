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
"""Unit tests for service-management enable command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.services import unit_test_base
import mock


class ListTest(unit_test_base.SNUnitTestBase):
  """Unit tests for services vpc-peerings connect command."""
  NETWORK = 'hello'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testList(self):
    want = [
        self.services_messages.Connection(
            network='projects/%s/global/networks/%s' % (self.PROJECT_NUMBER,
                                                        self.NETWORK),
            peering='servicenetworking-googleapis-com',
            reservedPeeringRanges=['google1', 'google2']),
        self.services_messages.Connection(
            network='projects/%s/global/networks/%s' % (self.PROJECT_NUMBER,
                                                        self.NETWORK),
            peering='cloudsql-googleapis-com',
            reservedPeeringRanges=['google1', 'google2']),
    ]
    self.ExpectListConnections(self.NETWORK, want)
    self.SetProjectNumber()

    self.Run('services vpc-peerings list --service=%s --network=%s' %
             (self.service, self.NETWORK))
    self.AssertOutputEquals(
        """\
---
network: projects/12481632/global/networks/hello
peering: servicenetworking-googleapis-com
reservedPeeringRanges:
- google1
- google2
---
network: projects/12481632/global/networks/hello
peering: cloudsql-googleapis-com
reservedPeeringRanges:
- google1
- google2
""",
        normalize_space=True)

  def testListWithDefaultService(self):
    self.service = '-'
    want = [
        self.services_messages.Connection(
            network='projects/%s/global/networks/%s' % (self.PROJECT_NUMBER,
                                                        self.NETWORK),
            peering='servicenetworking-googleapis-com',
            reservedPeeringRanges=['google1', 'google2']),
        self.services_messages.Connection(
            network='projects/%s/global/networks/%s' % (self.PROJECT_NUMBER,
                                                        self.NETWORK),
            peering='cloudsql-googleapis-com',
            reservedPeeringRanges=['google1', 'google2']),
    ]
    self.ExpectListConnections(self.NETWORK, want)
    self.SetProjectNumber()

    self.Run('services vpc-peerings list --network=%s' % self.NETWORK)
    self.AssertOutputEquals(
        """\
---
network: projects/12481632/global/networks/hello
peering: servicenetworking-googleapis-com
reservedPeeringRanges:
- google1
- google2
---
network: projects/12481632/global/networks/hello
peering: cloudsql-googleapis-com
reservedPeeringRanges:
- google1
- google2
""",
        normalize_space=True)

  def SetProjectNumber(self):
    mock_get = self.StartObjectPatch(projects_api, 'Get')
    p = mock.Mock()
    p.projectNumber = self.PROJECT_NUMBER
    mock_get.return_value = p


class ListAlphaTest(ListTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class ListBetaTest(ListTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
