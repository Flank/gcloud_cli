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
"""Tests for `gcloud monitoring policies describe`."""
import json

from apitools.base.py import encoding
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class MonitoringDescribeTest(base.MonitoringTestBase, parameterized.TestCase,
                             sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.service = self.client.projects_notificationChannels
    self.project_name = 'projects/' + self.Project()
    self.user_labels_cls = self.messages.NotificationChannel.UserLabelsValue
    self.channel_labels_cls = self.messages.NotificationChannel.LabelsValue

  def _ExpectCreate(self, channel, response):
    req = self.messages.MonitoringProjectsNotificationChannelsCreateRequest(
        name=self.project_name,
        notificationChannel=channel)
    self.service.Create.Expect(req, response)

  @parameterized.parameters(
      (True, True),
      (True, False),
      (False, True),
      (False, False)
  )
  def testCreate_FromString(self, use_yaml, from_file):
    user_labels = encoding.DictToAdditionalPropertyMessage(
        {'k1': 'v1', 'k2': 'v2'}, self.user_labels_cls)
    channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k3': 'v3', 'k4': 'v4'}, self.channel_labels_cls)
    channel = self.CreateChannel(
        display_name='my-str-channel',
        description='This will be imported as a string.',
        enabled=True,
        channel_type='email',
        user_labels=user_labels,
        channel_labels=channel_labels)

    channel_str = encoding.MessageToJson(channel)
    if use_yaml:
      channel_json = json.loads(channel_str)
      channel_str = yaml.dump(channel_json)

    if from_file:
      channel_file = self.Touch(self.temp_path, 'channel',
                                contents=channel_str)
      flag = '--channel-content-from-file ' + channel_file
    else:
      flag = '--channel-content \'{}\''.format(channel_str)

    self._ExpectCreate(channel, channel)
    self.Run('monitoring channels create '+ flag)

  def testCreate_FromStringGetsModified(self):
    user_labels = encoding.DictToAdditionalPropertyMessage(
        {'k1': 'v1', 'k2': 'v2'}, self.user_labels_cls)
    channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k3': 'v3', 'k4': 'v4'}, self.channel_labels_cls)
    channel = self.CreateChannel(
        display_name='my-str-channel',
        description='This will be imported as a string.',
        enabled=True,
        channel_type='email',
        user_labels=user_labels,
        channel_labels=channel_labels)
    channel_str = encoding.MessageToJson(channel)
    new_user_labels = encoding.DictToAdditionalPropertyMessage(
        {'k5': 'v5', 'k6': 'v6'}, self.user_labels_cls, sort_items=True)
    new_channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k7': 'v7', 'k8': 'v8'}, self.channel_labels_cls, sort_items=True)
    modified_channel = self.CreateChannel(
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms',
        user_labels=new_user_labels,
        channel_labels=new_channel_labels)

    self._ExpectCreate(modified_channel, modified_channel)
    self.Run('monitoring channels create --channel-content \'{}\' '
             '--display-name my-channel --description "My Description." '
             '--no-enabled --type sms --user-labels k5=v5,k6=v6 '
             '--channel-labels k7=v7,k8=v8'.format(channel_str))

  def testCreate_FromFlagsOnly(self):
    user_labels = encoding.DictToAdditionalPropertyMessage(
        {'k1': 'v1', 'k2': 'v2'}, self.user_labels_cls, sort_items=True)
    channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k3': 'v3', 'k4': 'v4'}, self.channel_labels_cls, sort_items=True)
    channel = self.CreateChannel(
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms',
        user_labels=user_labels,
        channel_labels=channel_labels)
    output_channel = encoding.CopyProtoMessage(channel)
    output_channel.name = 'channel-id'

    self._ExpectCreate(channel, output_channel)
    self.Run('monitoring channels create --channel-content \'{}\' '
             '--display-name my-channel --description "My Description." '
             '--no-enabled --type sms --user-labels k1=v1,k2=v2 '
             '--channel-labels k3=v3,k4=v4')
    self.AssertLogContains('Created notification channel [channel-id]')

  def testCreate_MinimumArgs(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.MinimumArgumentException,
        'One of [--display-name, --channel-content, '
        '--channel-content-from-file] must be supplied'):
      self.Run('monitoring channels create --description "My Channel"')

  def testCreate_AlternativeLabelsName(self):
    channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k3': 'v3', 'k4': 'v4'}, self.channel_labels_cls)
    channel = self.CreateChannel(
        display_name='my-str-channel',
        description='This will be imported as a string.',
        enabled=True,
        channel_type='email',
        channel_labels=channel_labels)

    # Rename labels in json to userLabels
    channel_json = json.loads(encoding.MessageToJson(channel))
    channel_json['channelLabels'] = channel_json.pop('labels')
    channel_str = json.dumps(channel_json)

    self._ExpectCreate(channel, channel)
    self.Run('monitoring channels create --channel-content \'{}\''.format(
        channel_str))


if __name__ == '__main__':
  test_case.main()
