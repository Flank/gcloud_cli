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
"""Tests for the interconnects describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InterconnectsDescribeTest(test_base.BaseTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.api_version = 'v1'
    self.message_version = self.compute_v1
    self.api_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.router_ref = self.resources.Create(
        'compute.routers',
        router='my-router1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')

  def _MakeInterconnectAttachment(self,
                                  name='my-attachment',
                                  description='description',
                                  interconnect_ref=None,
                                  router_ref=None,
                                  attachment_ref=None,
                                  region='us-central1'):
    return self.api_messages.InterconnectAttachment(
        name=name,
        description=description,
        interconnect=interconnect_ref.SelfLink(),
        router=router_ref.SelfLink(),
        region=region,
        selfLink=attachment_ref.SelfLink())

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [
            self._MakeInterconnectAttachment(
                name='my-attachment1',
                description='description',
                router_ref=self.router_ref,
                region='us-central1',
                interconnect_ref=self.interconnect_ref,
                attachment_ref=self.attachment_ref)
        ],
    ])
    result = self.Run("""
        compute interconnects attachments describe my-attachment1
        --region us-central1
        """)

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Get',
                         self.messages.ComputeInterconnectAttachmentsGetRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment1'))],)
    self.assertEqual(result.description, 'description')
    self.assertEqual(result.interconnect,
                     self.compute_uri + '/projects/my-project/global/'
                     'interconnects/my-interconnect1')
    self.assertEqual(result.name, 'my-attachment1')
    self.assertEqual(result.region, 'us-central1')
    self.assertEqual(result.router,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/routers/my-router1')
    self.assertEqual(result.selfLink,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/interconnectAttachments/my-attachment1')

  def testSimpleCaseWithUri(self):
    self.make_requests.side_effect = iter([
        [
            self._MakeInterconnectAttachment(
                name='my-attachment1',
                description='description',
                router_ref=self.router_ref,
                region='us-central1',
                interconnect_ref=self.interconnect_ref,
                attachment_ref=self.attachment_ref)
        ],
    ])
    result = self.Run('compute interconnects attachments describe ' +
                      self.compute_uri + '/projects/'
                      'my-project/regions/us-central1/interconnectAttachments/'
                      'my-attachment1')

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Get',
                         self.messages.ComputeInterconnectAttachmentsGetRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment1'))],)
    self.assertEqual(result.description, 'description')
    self.assertEqual(result.interconnect,
                     self.compute_uri + '/projects/my-project/global/'
                     'interconnects/my-interconnect1')
    self.assertEqual(result.name, 'my-attachment1')
    self.assertEqual(result.region, 'us-central1')
    self.assertEqual(result.router,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/routers/my-router1')
    self.assertEqual(result.selfLink,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/interconnectAttachments/my-attachment1')

  def testWithRegionPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
            self.messages.Region(name='us-central3'),
        ],
        [
            self._MakeInterconnectAttachment(
                name='my-attachment1',
                description='description',
                router_ref=self.router_ref,
                region='us-central1',
                interconnect_ref=self.interconnect_ref,
                attachment_ref=self.attachment_ref)
        ],
    ])
    result = self.Run("""
        compute interconnects attachments describe my-attachment1
        """)

    self.CheckRequests(
        [(self.compute.regions, 'List', self.messages.ComputeRegionsListRequest(
            project='my-project', maxResults=500))],
        [(self.message_version.interconnectAttachments, 'Get',
          self.messages.ComputeInterconnectAttachmentsGetRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment='my-attachment1'))],
    )
    self.assertEqual(result.description, 'description')
    self.assertEqual(result.interconnect,
                     'https://www.googleapis.com/compute/' + self.api_version +
                     '/projects/my-project/global/'
                     'interconnects/my-interconnect1')
    self.assertEqual(result.name, 'my-attachment1')
    self.assertEqual(result.region, 'us-central1')
    self.assertEqual(result.router,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/routers/my-router1')
    self.assertEqual(result.selfLink,
                     self.compute_uri + '/projects/my-project/regions/'
                     'us-central1/interconnectAttachments/my-attachment1')
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["us-central1", "us-central2", "us-central3"]')


class InterconnectsDescribeBetaTest(InterconnectsDescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.api_version = 'beta'
    self.message_version = self.compute_beta
    self.api_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.router_ref = self.resources.Create(
        'compute.routers',
        router='my-router1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')

  def _MakeInterconnectAttachment(self,
                                  name='my-attachment',
                                  description='description',
                                  interconnect_ref=None,
                                  router_ref=None,
                                  attachment_ref=None,
                                  region='us-central1'):
    return self.api_messages.InterconnectAttachment(
        name=name,
        description=description,
        interconnect=interconnect_ref.SelfLink(),
        router=router_ref.SelfLink(),
        region=region,
        selfLink=attachment_ref.SelfLink())


class InterconnectsDescribeAlphaTest(InterconnectsDescribeTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.api_version = 'alpha'
    self.message_version = self.compute_alpha
    self.api_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.interconnect_ref = self.resources.Create(
        'compute.interconnects',
        interconnect='my-interconnect1',
        project=self.Project())
    self.router_ref = self.resources.Create(
        'compute.routers',
        router='my-router1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')

  def _MakeInterconnectAttachment(self,
                                  name='my-attachment',
                                  description='description',
                                  interconnect_ref=None,
                                  router_ref=None,
                                  attachment_ref=None,
                                  region='us-central1'):
    return self.api_messages.InterconnectAttachment(
        name=name,
        description=description,
        interconnect=interconnect_ref.SelfLink(),
        router=router_ref.SelfLink(),
        region=region,
        selfLink=attachment_ref.SelfLink())


if __name__ == '__main__':
  test_case.main()
