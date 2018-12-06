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
"""Tests for the interconnect attachment partner create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from tests.lib.surface.compute import test_base


class InterconnectAttachmentsPartnerCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha

  def CheckInterconnectAttachmentRequest(self, **kwargs):
    interconnect_attachment_msg = {}
    interconnect_attachment_msg.update(kwargs)
    self.CheckRequests(
        [(self.message_version.interconnectAttachments, 'Insert',
          self.messages.ComputeInterconnectAttachmentsInsertRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment=self.messages.InterconnectAttachment(
                  **interconnect_attachment_msg)))],)

  def testCreateInterconnectAttachment(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'PARTNER'),
                edgeAvailabilityDomain=messages.InterconnectAttachment.
                EdgeAvailabilityDomainValueValuesEnum('AVAILABILITY_DOMAIN_2'),
                adminEnabled=True)
        ],
    ])

    self.Run(
        'compute interconnects attachments partner create my-attachment '
        '--region us-central1 --router my-router --description "this is my '
        'attachment" --edge-availability-domain availability-domain-2 '
        '--admin-enabled')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('PARTNER'),
        edgeAvailabilityDomain=messages.InterconnectAttachment.
        EdgeAvailabilityDomainValueValuesEnum('AVAILABILITY_DOMAIN_2'),
        adminEnabled=True,
    )
    self.AssertErrContains('Please use the pairing key to provision the '
                           'attachment with your partner:')

  def testWithRouterRegionDifferentAsAttachment(self):
    with self.assertRaises(parser_errors.ArgumentException):
      self.Run(
          'compute interconnects attachments partner create my-attachment '
          '--region us-central1 --router my-router --router-region us-east1 '
          '--edge-availability-domain availability-domain-1 --admin-enabled')

  def testSimpleInvocationWithRegionPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    messages = self.messages

    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([[
        self.messages.Region(name='region-1'),
        self.messages.Region(name='region-2'),
        self.messages.Region(name='region-3'),
    ], [
        messages.InterconnectAttachment(
            name='my-attachment',
            description='',
            region='region-2',
            router=self.compute_uri + '/projects/my-project/regions/'
            'region-2/routers/my-router',
            type=messages.InterconnectAttachment.TypeValueValuesEnum('PARTNER'),
            edgeAvailabilityDomain=messages.InterconnectAttachment.
            EdgeAvailabilityDomainValueValuesEnum('AVAILABILITY_DOMAIN_ANY'),
            adminEnabled=True),
    ]])

    self.Run('compute interconnects attachments partner create my-attachment '
             '--router my-router --description "this is my attachment" '
             '--edge-availability-domain any --admin-enabled')

    self.CheckRequests(
        [(self.compute.regions, 'List',
          messages.ComputeRegionsListRequest(
              project='my-project', maxResults=500))],
        [(self.message_version.interconnectAttachments, 'Insert',
          self.messages.ComputeInterconnectAttachmentsInsertRequest(
              project='my-project',
              region='region-2',
              interconnectAttachment=self.messages.InterconnectAttachment(
                  name='my-attachment',
                  description='this is my attachment',
                  router=self.compute_uri +
                  '/projects/my-project/regions/region-2/'
                  'routers/my-router',
                  type=messages.InterconnectAttachment.TypeValueValuesEnum(
                      'PARTNER'),
                  edgeAvailabilityDomain=messages.InterconnectAttachment.
                  EdgeAvailabilityDomainValueValuesEnum(
                      'AVAILABILITY_DOMAIN_ANY'),
                  adminEnabled=True),
          ))],
    )
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["region-1", "region-2", "region-3"]')
    self.AssertOutputEquals('')


class InterconnectAttachmentsPartnerCreateBetaTest(
    InterconnectAttachmentsPartnerCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta


class InterconnectAttachmentsPartnerCreateGaTest(
    InterconnectAttachmentsPartnerCreateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1
