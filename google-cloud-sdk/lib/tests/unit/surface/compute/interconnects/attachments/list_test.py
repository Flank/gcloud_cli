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
"""Tests for the interconnect attachments list subcommand."""

import textwrap

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class InterconnectAttachmentsListTest(sdk_test_base.WithFakeAuth,
                                      cli_test_base.CliTestBase):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.GA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.api_version = 'v1'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.attachment_ref1 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref2 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment2',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref3 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment3',
        project=self.Project(),
        region='us-east1')

  def _GetInterconnectAttachmentAggregatedListResponse(
      self, scoped_interconnect_attachments=None, next_page_token=None):
    additional_properties = []
    for scope, interconnect_attachments in scoped_interconnect_attachments:
      interconnect_attachments_scoped_list = (
          self.messages.InterconnectAttachmentsScopedList(
              interconnectAttachments=interconnect_attachments))
      additional_property = (self.messages.InterconnectAttachmentAggregatedList.
                             ItemsValue.AdditionalProperty)(
                                 key=scope,
                                 value=interconnect_attachments_scoped_list,
                             )
      additional_properties.append(additional_property)
    return self.messages.InterconnectAttachmentAggregatedList(
        items=self.messages.InterconnectAttachmentAggregatedList.ItemsValue(
            additionalProperties=additional_properties,),
        nextPageToken=next_page_token,
    )

  def testSimpleCase(self):
    scoped_interconnect_attachments = [('regions/us-central1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment1',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref1.SelfLink()),
        self.apis_messages.InterconnectAttachment(
            name='my-attachment2',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref2.SelfLink())
    ]), ('regions/us-east1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment3',
            description='description',
            interconnect='my-interconnect',
            router='my-router3',
            region='us-east1',
            selfLink=self.attachment_ref3.SelfLink())
    ])]
    self.client.interconnectAttachments.AggregatedList.Expect(
        self.messages.ComputeInterconnectAttachmentsAggregatedListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self._GetInterconnectAttachmentAggregatedListResponse(
            scoped_interconnect_attachments=scoped_interconnect_attachments))

    self.Run("""
          compute interconnects attachments list
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME           REGION      INTERCONNECT    ROUTER
          my-attachment1 us-central1 my-interconnect my-router
          my-attachment2 us-central1 my-interconnect my-router
          my-attachment3 us-east1    my-interconnect my-router3
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testSimpleCaseWithUri(self):
    scoped_interconnect_attachments = [('regions/us-central1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment1',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref1.SelfLink()),
        self.apis_messages.InterconnectAttachment(
            name='my-attachment2',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref2.SelfLink())
    ]), ('regions/us-east1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment3',
            description='description',
            interconnect='my-interconnect',
            router='my-router3',
            region='us-east1',
            selfLink=self.attachment_ref3.SelfLink())
    ])]
    self.client.interconnectAttachments.AggregatedList.Expect(
        self.messages.ComputeInterconnectAttachmentsAggregatedListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self._GetInterconnectAttachmentAggregatedListResponse(
            scoped_interconnect_attachments=scoped_interconnect_attachments))

    self.Run("""
          compute interconnects attachments list --uri
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          https://www.googleapis.com/compute/""" + self.api_version +
                        """/projects/my-project/regions/us-central1/""" +
                        """interconnectAttachments/my-attachment1
          https://www.googleapis.com/compute/""" + self.api_version +
                        """/projects/my-project/regions/us-central1""" +
                        """/interconnectAttachments/my-attachment2
          https://www.googleapis.com/compute/""" + self.api_version +
                        """/projects/my-project/regions/us-east1/""" +
                        """interconnectAttachments/my-attachment3
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testSimpleCaseWithFilter(self):
    scoped_interconnect_attachments = [('regions/us-central1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment1',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref1.SelfLink()),
        self.apis_messages.InterconnectAttachment(
            name='my-attachment2',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref2.SelfLink())
    ])]
    self.client.interconnectAttachments.AggregatedList.Expect(
        self.messages.ComputeInterconnectAttachmentsAggregatedListRequest(
            pageToken=None,
            filter=u'region eq ".*\\bus\\-central1\\b.*"',
            project=self.Project(),
        ),
        response=self._GetInterconnectAttachmentAggregatedListResponse(
            scoped_interconnect_attachments=scoped_interconnect_attachments))

    self.Run("""
          compute interconnects attachments list --filter "region:us-central1"
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME           REGION      INTERCONNECT    ROUTER
          my-attachment1 us-central1 my-interconnect my-router
          my-attachment2 us-central1 my-interconnect my-router
          """),
        normalize_space=True)
    self.AssertErrEquals('')

  def testSimpleCaseWithNextPageToken(self):
    scoped_interconnect_attachments = [('regions/us-central1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment1',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref1.SelfLink()),
        self.apis_messages.InterconnectAttachment(
            name='my-attachment2',
            description='description',
            interconnect='my-interconnect',
            router='my-router',
            region='us-central1',
            selfLink=self.attachment_ref2.SelfLink())
    ]), ('regions/us-east1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment3',
            description='description',
            interconnect='my-interconnect',
            router='my-router3',
            region='us-east1',
            selfLink=self.attachment_ref3.SelfLink())
    ])]
    self.client.interconnectAttachments.AggregatedList.Expect(
        self.messages.ComputeInterconnectAttachmentsAggregatedListRequest(
            pageToken=None,
            project=self.Project(),
        ),
        response=self._GetInterconnectAttachmentAggregatedListResponse(
            scoped_interconnect_attachments=scoped_interconnect_attachments,
            next_page_token=u'1396059067464'))

    scoped_interconnect_attachments_2 = [('regions/asian-east1', [
        self.apis_messages.InterconnectAttachment(
            name='my-attachment5',
            description='description',
            interconnect='my-interconnect',
            router='my-router5',
            region='asian-east1',
            selfLink=self.attachment_ref1.SelfLink()),
        self.apis_messages.InterconnectAttachment(
            name='my-attachment6',
            description='description',
            interconnect='my-interconnect',
            router='my-router6',
            region='asian-east1',
            selfLink=self.attachment_ref2.SelfLink())
    ])]

    self.client.interconnectAttachments.AggregatedList.Expect(
        self.messages.ComputeInterconnectAttachmentsAggregatedListRequest(
            pageToken=u'1396059067464',
            project=self.Project(),
        ),
        response=self._GetInterconnectAttachmentAggregatedListResponse(
            scoped_interconnect_attachments=scoped_interconnect_attachments_2,
            next_page_token=None))

    self.Run("""
          compute interconnects attachments list
          """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
          NAME           REGION      INTERCONNECT    ROUTER
          my-attachment1 us-central1 my-interconnect my-router
          my-attachment2 us-central1 my-interconnect my-router
          my-attachment3 us-east1    my-interconnect my-router3
          my-attachment5 asian-east1 my-interconnect my-router5
          my-attachment6 asian-east1 my-interconnect my-router6
          """),
        normalize_space=True)
    self.AssertErrEquals('')


class InterconnectAttachmentsListBetaTest(InterconnectAttachmentsListTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'beta'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.api_version = 'beta'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.attachment_ref1 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref2 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment2',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref3 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment3',
        project=self.Project(),
        region='us-east1')


class InterconnectAttachmentsListAlphaTest(InterconnectAttachmentsListTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'alpha'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.api_version = 'alpha'
    self.apis_messages = core_apis.GetMessagesModule('compute',
                                                     self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.attachment_ref1 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment1',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref2 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment2',
        project=self.Project(),
        region='us-central1')
    self.attachment_ref3 = self.resources.Create(
        'compute.interconnectAttachments',
        interconnectAttachment='my-attachment3',
        project=self.Project(),
        region='us-east1')


if __name__ == '__main__':
  test_case.main()
