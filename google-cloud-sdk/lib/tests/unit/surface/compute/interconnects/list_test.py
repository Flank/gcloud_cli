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
"""Tests for the interconnects list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute.interconnects import test_resource_util


class InterconnectsListGATest(sdk_test_base.WithFakeAuth,
                              cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect1_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.interconnect2_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect2',
        project=self.Project())

  def testSimpleCase(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref)
            ],))

    self.Run("""
          compute interconnects list
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME             LOCATION    OPERATIONAL_STATUS  ADMIN_ENABLED
          my-interconnect1 my-location OS_ACTIVE           True
          my-interconnect2 my-location OS_UNPROVISIONED    False
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testWithUriFlag(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref)
            ],))

    self.Run("""
          compute interconnects list --uri
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          https://compute.googleapis.com/compute/v1/projects/fake-project/global/interconnects/my-interconnect1
          https://compute.googleapis.com/compute/v1/projects/fake-project/global/interconnects/my-interconnect2
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testWithFilterFlag(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            filter='location eq ".*\\bmy\\-location\\b.*"',
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref),
                test_resource_util.MakeInterconnectGA(
                    name='my-interconnect3',
                    location='my-location',
                    operational_status=self.v1_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref),
            ],))

    self.Run("""
          compute interconnects list --filter "location:my-location"
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME             LOCATION    OPERATIONAL_STATUS  ADMIN_ENABLED
          my-interconnect1 my-location OS_ACTIVE           True
          my-interconnect2 my-location OS_UNPROVISIONED    False
          my-interconnect3 my-location OS_UNPROVISIONED    False
          """),
        normalize_space=True)
    self.AssertErrEquals('')


class InterconnectsListBetaTest(sdk_test_base.WithFakeAuth,
                                cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = self.track.prefix
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

    self.beta_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect1_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.interconnect2_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect2',
        project=self.Project())

  def testSimpleCase(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref)
            ],))

    self.Run("""
          compute interconnects list
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME             LOCATION    OPERATIONAL_STATUS  ADMIN_ENABLED
          my-interconnect1 my-location OS_ACTIVE           True
          my-interconnect2 my-location OS_UNPROVISIONED    False
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testWithUriFlag(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref)
            ],))

    self.Run("""
          compute interconnects list --uri
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          https://compute.googleapis.com/compute/beta/projects/fake-project/global/interconnects/my-interconnect1
          https://compute.googleapis.com/compute/beta/projects/fake-project/global/interconnects/my-interconnect2
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testWithFilterFlag(self):
    self.client.interconnects.List.Expect(
        self.messages.ComputeInterconnectsListRequest(
            filter='location eq ".*\\bmy\\-location\\b.*"',
            pageToken=None,
            project=self.Project(),
        ),
        response=self.messages.InterconnectList(
            items=[
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect1',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_ACTIVE,
                    admin_enabled=True,
                    interconnect_ref=self.interconnect1_ref),
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect2',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref),
                test_resource_util.MakeInterconnectBeta(
                    name='my-interconnect3',
                    location='my-location',
                    operational_status=self.beta_messages.Interconnect.
                    OperationalStatusValueValuesEnum.OS_UNPROVISIONED,
                    admin_enabled=False,
                    interconnect_ref=self.interconnect2_ref),
            ],))

    self.Run("""
          compute interconnects list --filter "location:my-location"
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME             LOCATION    OPERATIONAL_STATUS  ADMIN_ENABLED
          my-interconnect1 my-location OS_ACTIVE           True
          my-interconnect2 my-location OS_UNPROVISIONED    False
          my-interconnect3 my-location OS_UNPROVISIONED    False
          """),
        normalize_space=True)
    self.AssertErrEquals('')


if __name__ == '__main__':
  test_case.main()
