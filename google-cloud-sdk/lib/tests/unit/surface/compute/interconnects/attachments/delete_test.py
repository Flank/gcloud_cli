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
"""Tests for the interconnect attachments delete subcommand."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InterconnectAttachmentDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def testWithSingleInterconnectAttachment(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute interconnects attachments delete my-attachment
        --region us-central1
        """)

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment'))],)

  def testWithManyInterconnectAttachments(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run("""
        compute interconnects attachments delete my-attachment my-attachment2
        my-attachment3 --region us-central1
        """)

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment')),
                        (self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment2')),
                        (self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment3'))],)

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute interconnects attachments delete my-attachment1 my-attachment2
        my-attachment3 --region us-central1
        """)

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment1')),
                        (self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment2')),
                        (self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment3'))],)
    self.AssertErrContains(
        textwrap.dedent("""\
        The following interconnect attachments will be deleted:
         - [my-attachment1] in [us-central1]
         - [my-attachment2] in [us-central1]
         - [my-attachment3] in [us-central1]


        Do you want to continue (Y/n)? """))

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
            compute interconnects attachments delete my-attachment1
            my-attachment2 my-attachment3 --region us-central1
            """)

    self.CheckRequests()

  def testDeleteWithUri(self):
    properties.VALUES.core.disable_prompts.Set(True)
    messages = self.messages
    self.Run('compute interconnects attachments delete ' + self.compute_uri +
             '/projects/my-project/'
             'regions/us-central1/interconnectAttachments/my-attachment')

    self.CheckRequests([(self.message_version.interconnectAttachments, 'Delete',
                         messages.ComputeInterconnectAttachmentsDeleteRequest(
                             project='my-project',
                             region='us-central1',
                             interconnectAttachment='my-attachment'))],)

  def testWithRegionPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    messages = self.messages
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([[
        self.messages.Region(name='region-1'),
        self.messages.Region(name='region-2'),
        self.messages.Region(name='region-3'),
    ], []])

    self.Run("""
        compute interconnects attachments delete my-attachment
        """)

    self.CheckRequests(
        [(self.compute.regions, 'List', messages.ComputeRegionsListRequest(
            project='my-project', maxResults=500))],
        [(self.message_version.interconnectAttachments, 'Delete',
          messages.ComputeInterconnectAttachmentsDeleteRequest(
              project='my-project',
              region='region-2',
              interconnectAttachment='my-attachment'))],
    )
    self.AssertErrContains(
        textwrap.dedent("""\
          For the following interconnect attachment:
           - [my-attachment]
          choose a region:
           [1] region-1
           [2] region-2
           [3] region-3
          Please enter your numeric choice:  """))
    self.AssertOutputEquals('')

  if __name__ == '__main__':
    test_case.main()


class InterconnectAttachmentDeleteBetaTest(InterconnectAttachmentDeleteTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta


class InterconnectAttachmentDeleteAlphaTest(InterconnectAttachmentDeleteTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha
