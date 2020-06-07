# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for the instance-groups managed list-errors subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.compute import test_resources


class InstanceGroupsListErrorsZonalTestBase(sdk_test_base.WithFakeAuth,
                                            cli_test_base.CliTestBase):

  API_VERSION = 'v1'

  def SetUp(self):
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.API_VERSION))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.API_VERSION)
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.endpoint_uri = (
        'https://www.googleapis.com/compute/{api_version}/').format(
            api_version=self.API_VERSION)
    self.project_uri = '{endpoint_uri}projects/fake-project'.format(
        endpoint_uri=self.endpoint_uri)


class InstanceGroupsListErrorsZonalTest(
    InstanceGroupsListErrorsZonalTestBase):

  API_VERSION = 'v1'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testListErrorsNoPagination(self):
    request = self.messages.ComputeInstanceGroupManagersListErrorsRequest(
        instanceGroupManager=u'igm-1',
        zone=u'central2-a',
        project=u'fake-project',
    )
    response = self.messages.InstanceGroupManagersListErrorsResponse(
        items=test_resources.MakeErrorsInManagedInstanceGroup(
            self.messages, 'beta'),)
    self.client.instanceGroupManagers.ListErrors.Expect(
        request,
        response=response,
    )

    self.Run("""
        compute instance-groups managed list-errors igm-1
          --zone central2-a
          --project fake-project
        """)

  def testListErrorsWithPagination(self):
    request = self.messages.ComputeInstanceGroupManagersListErrorsRequest(
        instanceGroupManager=u'igm-1',
        zone=u'central2-a',
        project=u'fake-project',
        maxResults=1,
    )
    items = test_resources.MakeErrorsInManagedInstanceGroup(
        self.messages, 'beta')
    response = self.messages.InstanceGroupManagersListErrorsResponse(
        items=[items[0]], nextPageToken='token-1')
    self.client.instanceGroupManagers.ListErrors.Expect(
        request,
        response=response,
    )

    request = self.messages.ComputeInstanceGroupManagersListErrorsRequest(
        instanceGroupManager=u'igm-1',
        zone=u'central2-a',
        project=u'fake-project',
        maxResults=1,
        pageToken='token-1')

    response = self.messages.InstanceGroupManagersListErrorsResponse(
        items=[items[1]],)

    self.client.instanceGroupManagers.ListErrors.Expect(
        request,
        response=response,
    )

    self.Run("""
        compute instance-groups managed list-errors igm-1
          --zone central2-a
          --project fake-project
          --page-size=1
        """)


class InstanceGroupsListErrorsBetaZonalTest(InstanceGroupsListErrorsZonalTest):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupsListErrorsAlphaZonalTest(
    InstanceGroupsListErrorsBetaZonalTest):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
