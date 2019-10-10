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
"""Tests for the interconnect attachment partner provider update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import test_base


class InterconnectAttachmentsPartnerUpdateGaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def CheckInterconnectAttachmentRequest(self, **kwargs):
    interconnect_attachment_msg = {}
    interconnect_attachment_msg.update(kwargs)
    self.CheckRequests(
        [(self.message_version.interconnectAttachments, 'Patch',
          self.messages.ComputeInterconnectAttachmentsPatchRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment=kwargs.get('name'),
              interconnectAttachmentResource=self.messages.
              InterconnectAttachment(**interconnect_attachment_msg)))],)

  def testUpdateInterconnectAttachment(self):
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
                vlanTag8021q=400,
                candidateSubnets=[
                    '169.254.0.0/29', '169.254.4.0/28', '169.254.8.0/27'
                ]),
        ],
    ])

    self.Run('compute interconnects attachments provider update my-attachment '
             '--region us-central1 --description "this is my attachment" '
             '--bandwidth 10g --partner-interconnect-name '
             '"Test Update Partner Interconnect" --partner-name '
             '"Test Update Partner Name" '
             '--partner-portal-url https://update.example.com/portal-url')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_10G'),
        partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
            interconnectName='Test Update Partner Interconnect',
            partnerName='Test Update Partner Name',
            portalUrl='https://update.example.com/portal-url'))


class InterconnectAttachmentsPartnerUpdateBetaTest(
    InterconnectAttachmentsPartnerUpdateGaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta

  def testUpdateInterconnectAttachmentLabels(self):
    messages = self.messages
    labels_cls = messages.InterconnectAttachment.LabelsValue
    old_labels = labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key='key1', value='value1'),
        labels_cls.AdditionalProperty(key='key2', value='value2'),
    ])
    labels = labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key='key1', value='value1'),
        labels_cls.AdditionalProperty(key='key2', value='new_value'),
        labels_cls.AdditionalProperty(key='key3', value='value3'),
    ])
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                labelFingerprint=b'abcd',
                labels=old_labels),
        ],
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='this is my attachment',
                region='us-central1',
                labels=labels),
        ],
    ])

    self.Run('compute interconnects attachments provider update my-attachment '
             '--region us-central1 --description "this is my attachment" '
             '--update-labels key3=value3,key2=new_value')

    self.CheckRequests(
        [(self.message_version.interconnectAttachments, 'Get',
          self.messages.ComputeInterconnectAttachmentsGetRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment='my-attachment'))],
        [(self.message_version.interconnectAttachments, 'Patch',
          self.messages.ComputeInterconnectAttachmentsPatchRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment='my-attachment',
              interconnectAttachmentResource=self.messages.
              InterconnectAttachment(
                  name='my-attachment',
                  description='this is my attachment',
                  labels=labels,
                  labelFingerprint=b'abcd')))],
    )

  def testUpdateInterconnectAttachmentClearLabels(self):
    messages = self.messages
    labels_cls = messages.InterconnectAttachment.LabelsValue
    old_labels = labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key='key1', value='value1'),
    ])
    labels = labels_cls(additionalProperties=[])
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                labelFingerprint=b'abcd',
                labels=old_labels),
        ],
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='this is my attachment',
                region='us-central1',
                labels=labels,
                adminEnabled=False),
        ],
    ])

    self.Run('compute interconnects attachments provider update my-attachment '
             '--region us-central1 --description "this is my attachment" '
             '--clear-labels')

    self.CheckRequests(
        [(self.message_version.interconnectAttachments, 'Get',
          self.messages.ComputeInterconnectAttachmentsGetRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment='my-attachment'))],
        [(self.message_version.interconnectAttachments, 'Patch',
          self.messages.ComputeInterconnectAttachmentsPatchRequest(
              project='my-project',
              region='us-central1',
              interconnectAttachment='my-attachment',
              interconnectAttachmentResource=self.messages.
              InterconnectAttachment(
                  name='my-attachment',
                  description='this is my attachment',
                  labels=labels,
                  labelFingerprint=b'abcd')))],
    )


class InterconnectAttachmentsPartnerUpdateAlphaTest(
    InterconnectAttachmentsPartnerUpdateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha
