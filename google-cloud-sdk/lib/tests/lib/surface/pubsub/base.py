# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Base class for all Cloud Pub/Sub tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class CloudPubsubTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):
  """Base class for Cloud Pub/Sub command unit tests."""

  def PreSetUp(self):
    # Store API messages here so we can use them throughout all tests
    # without tying them into a specific version
    self.msgs = apis.GetMessagesModule('pubsub', 'v1')

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(False)

    self.client = mock.Client(client_class=apis.GetClientClass('pubsub', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    # List of test message IDs
    self.message_ids = ['123456', '654321', '987654']

    # List of message data
    self.message_data = ['Hello, World!', 'World on Fire!', b'Hello \xAA']

    attributes = self.msgs.PubsubMessage.AttributesValue(
        additionalProperties=[])

    # List of actual Cloud Pub/Sub message objects
    self.messages = [
        self.msgs.PubsubMessage(
            data=self.message_data[0].encode('utf8'), attributes=attributes),
        self.msgs.PubsubMessage(
            data=self.message_data[1].encode('utf8'), attributes=attributes),
        self.msgs.PubsubMessage(
            data=self.message_data[2], attributes=attributes)
    ]

    # Policy object used for IAM tests.
    self.policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.msgs.Binding(
                role='roles/viewer', members=['allUsers'])
        ])

  def GetSnapshotUri(self, snapshot_name, project=None):
    return util.ParseSnapshot(
        snapshot_name, project or self.Project()).SelfLink()

  def GetSubscriptionUri(self, subscription_name, project=None):
    return util.ParseSubscription(
        subscription_name, project or self.Project()).SelfLink()

  def GetTopicUri(self, topic_name, project=None):
    return util.ParseTopic(
        topic_name, project or self.Project()).SelfLink()

  def CreatePolicy(self, create_file=True):
    policy = self.msgs.Policy(
        version=1,
        bindings=[
            self.msgs.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.msgs.Binding(role='roles/viewer', members=['allUsers'])
        ],
        etag=b'abcde')
    f = None
    if create_file:
      policy_json = encoding.MessageToJson(policy)
      f = self.Touch(self.temp_path, 'policy.yaml', contents=policy_json)
    return policy, f
