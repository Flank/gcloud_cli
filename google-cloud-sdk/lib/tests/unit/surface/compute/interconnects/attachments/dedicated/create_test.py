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
"""Tests for the interconnect attachment dedicated create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import parser_errors
from tests.lib.surface.compute import test_base


class InterconnectAttachmentsDedicatedCreateGaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def CheckInterconnectAttachmentRequest(self, **kwargs):
    interconnect_attachment_msg = {}
    interconnect_attachment_msg.update(kwargs)
    if 'validateOnly' in kwargs:
      validate_only = interconnect_attachment_msg.pop('validateOnly')
      self.CheckRequests(
          [(self.message_version.interconnectAttachments, 'Insert',
            self.messages.ComputeInterconnectAttachmentsInsertRequest(
                project='my-project',
                region='us-central1',
                validateOnly=validate_only,
                interconnectAttachment=self.messages.InterconnectAttachment(
                    **interconnect_attachment_msg)))],)
    else:
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
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'DEDICATED'),
                adminEnabled=True,
                vlanTag8021q=400,
                candidateSubnets=[
                    '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                ])
        ],
    ])

    self.Run('compute interconnects attachments dedicated create my-attachment '
             '--region us-central1 --interconnect my-interconnect --router '
             'my-router --description "this is my attachment" --vlan 400 '
             '--admin-enabled --candidate-subnets '
             '169.254.0.0/29,169.254.4.0/28,169.254.8.0/27')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('DEDICATED'),
        adminEnabled=True,
        vlanTag8021q=400,
        candidateSubnets=['169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'])
    self.AssertOutputEquals('')
    self.AssertErrContains('You must configure your Google Cloud Router with '
                           'an interface and BGP peer for your created VLAN '
                           'attachment. See also https://cloud.google.com'
                           '/interconnect/docs/how-to/dedicated'
                           '/creating-vlan-attachments for more detailed help.')

  def testCreateInterconnectAttachmentWithUri(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'DEDICATED'),
                adminEnabled=True,
                vlanTag8021q=400,
                candidateSubnets=[
                    '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                ]),
        ],
    ])

    self.Run('compute interconnects attachments dedicated create ' +
             self.compute_uri +
             '/projects/my-project/regions/us-central1/interconnectAttachments/'
             'my-attachment --interconnect my-interconnect --router my-router '
             '--description "this is my attachment" --vlan 400 --admin-enabled '
             '--candidate-subnets 169.254.0.0/29,169.254.4.0/28,169.254.8.0/27')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('DEDICATED'),
        adminEnabled=True,
        vlanTag8021q=400,
        candidateSubnets=['169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'])

  def testWithRouterRegionDifferentAsAttachment(self):
    with self.assertRaises(parser_errors.ArgumentException):
      self.Run(
          'compute interconnects attachments dedicated create my-attachment '
          '--region us-central1 --interconnect my-interconnect --router '
          'my-router --router-region us-east1 --vlan 400 --admin-enabled '
          '--candidate-subnets 169.254.0.0/29,169.254.4.0/28,169.254.8.0/27')

  def testSimpleInvocationWithRegionPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    messages = self.messages

    self.WriteInput('2\n')
    self.make_requests.side_effect = iter(
        [[
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],
         [
             messages.InterconnectAttachment(
                 name='my-attachment',
                 description='',
                 region='region-2',
                 interconnect=self.compute_uri +
                 '/projects/my-project/global/interconnects/'
                 'my-interconnect',
                 router=self.compute_uri + '/projects/my-project/regions/'
                 'region-2/routers/my-router',
                 type=messages.InterconnectAttachment.TypeValueValuesEnum(
                     'DEDICATED'),
                 adminEnabled=True,
                 vlanTag8021q=400,
                 candidateSubnets=[
                     '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                 ]),
         ]])

    self.Run(
        'compute interconnects attachments dedicated create my-attachment '
        '--interconnect my-interconnect --router my-router --description "this'
        ' is my attachment"  --vlan 400 --admin-enabled --candidate-subnets '
        '169.254.0.0/29,169.254.4.0/28,169.254.8.0/27')

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
                  interconnect=self.compute_uri +
                  '/projects/my-project/global/interconnects/my-interconnect',
                  router=self.compute_uri +
                  '/projects/my-project/regions/region-2/'
                  'routers/my-router',
                  type=messages.InterconnectAttachment.TypeValueValuesEnum(
                      'DEDICATED'),
                  adminEnabled=True,
                  vlanTag8021q=400,
                  candidateSubnets=[
                      '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                  ])))],
    )
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["region-1", "region-2", "region-3"]')
    self.AssertOutputEquals('')

  def testCreateInterconnectAttachmentWithBandwidth(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'DEDICATED'),
                adminEnabled=True,
                vlanTag8021q=400,
                candidateSubnets=[
                    '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                ],
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_50G')),
        ],
    ])

    self.Run('compute interconnects attachments dedicated create my-attachment '
             '--region us-central1 --interconnect my-interconnect --router '
             'my-router --description "this is my attachment" --vlan 400 '
             '--admin-enabled --candidate-subnets '
             '169.254.0.0/29,169.254.4.0/28,169.254.8.0/27 --bandwidth 50g')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('DEDICATED'),
        adminEnabled=True,
        vlanTag8021q=400,
        candidateSubnets=['169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'],
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_50G'))
    self.AssertOutputEquals('')
    self.AssertErrContains('You must configure your Google Cloud Router with '
                           'an interface and BGP peer for your created VLAN '
                           'attachment. See also https://cloud.google.com'
                           '/interconnect/docs/how-to/dedicated'
                           '/creating-vlan-attachments for more detailed help.')


class InterconnectAttachmentsDedicatedCreateBetaTest(
    InterconnectAttachmentsDedicatedCreateGaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta


class InterconnectAttachmentsDedicatedCreateAlphaTest(
    InterconnectAttachmentsDedicatedCreateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha

  def testCreateInterconnectAttachmentValidateOnly(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'DEDICATED'),
                adminEnabled=True,
                vlanTag8021q=400,
                candidateSubnets=[
                    '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                ],
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_50G')),
        ],
    ])

    self.Run(
        'compute interconnects attachments dedicated create my-attachment '
        '--region us-central1 --interconnect my-interconnect --router '
        'my-router --description "this is my attachment" --vlan 400 '
        '--admin-enabled --candidate-subnets '
        '169.254.0.0/29,169.254.4.0/28,169.254.8.0/27 --bandwidth 50g --dry-run'
    )

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('DEDICATED'),
        adminEnabled=True,
        vlanTag8021q=400,
        candidateSubnets=['169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'],
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_50G'),
        validateOnly=True)
    self.AssertOutputEquals('')
    self.AssertErrContains('You must configure your Google Cloud Router with '
                           'an interface and BGP peer for your created VLAN '
                           'attachment. See also https://cloud.google.com'
                           '/interconnect/docs/how-to/dedicated'
                           '/creating-vlan-attachments for more detailed help.')

  def testCreateInterconnectAttachmentWithMtu(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'DEDICATED'),
                adminEnabled=True,
                vlanTag8021q=400,
                mtu=1500),
        ],
    ])

    self.Run(
        'compute interconnects attachments dedicated create my-attachment '
        '--region us-central1 --interconnect my-interconnect --router '
        'my-router --description "this is my attachment" --vlan 400 '
        '--admin-enabled --mtu 1500')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        router=self.compute_uri + '/projects/my-project/regions/us-central1/'
        'routers/my-router',
        type=messages.InterconnectAttachment.TypeValueValuesEnum('DEDICATED'),
        adminEnabled=True,
        vlanTag8021q=400,
        mtu=1500)
