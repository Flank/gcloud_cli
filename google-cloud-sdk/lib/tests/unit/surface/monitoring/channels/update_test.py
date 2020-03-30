# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud monitoring channels update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.monitoring import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class NotificationChannelsUpdateTest(base.MonitoringTestBase,
                                     parameterized.TestCase):

  def PreSetUp(self):
    super(NotificationChannelsUpdateTest, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    super(NotificationChannelsUpdateTest, self).SetUp()
    self.user_labels_cls = self.messages.NotificationChannel.UserLabelsValue
    self.channel_labels_cls = self.messages.NotificationChannel.LabelsValue

  def _ExpectUpdate(self, channel_name, channel, old_channel=None,
                    field_masks=None):
    relative_name = 'projects/{0}/notificationChannels/{1}'.format(
        self.Project(), channel_name)
    if old_channel:
      get_req = self.messages.MonitoringProjectsNotificationChannelsGetRequest(
          name=relative_name)
      self.client.projects_notificationChannels.Get.Expect(get_req, old_channel)
    req = self.messages.MonitoringProjectsNotificationChannelsPatchRequest(
        name=relative_name,
        notificationChannel=channel,
        updateMask=field_masks)
    self.client.projects_notificationChannels.Patch.Expect(req, channel)

  def _RunLabelsTest(self, update_flags, old_user_labels=None,
                     old_channel_labels=None, new_user_labels=None,
                     new_channel_labels=None):
    channel_name = 'channel-id'
    field_masks = []
    if old_user_labels:
      old_user_labels = encoding.DictToAdditionalPropertyMessage(
          old_user_labels, self.user_labels_cls, sort_items=True)
    if new_user_labels:
      new_user_labels = encoding.DictToAdditionalPropertyMessage(
          new_user_labels, self.user_labels_cls, sort_items=True)
    if old_channel_labels:
      old_channel_labels = encoding.DictToAdditionalPropertyMessage(
          old_channel_labels, self.channel_labels_cls, sort_items=True)
    if new_channel_labels:
      new_channel_labels = encoding.DictToAdditionalPropertyMessage(
          new_channel_labels, self.channel_labels_cls, sort_items=True)

    if old_user_labels != new_user_labels:
      field_masks.append('user_labels')
    if old_channel_labels != new_channel_labels:
      field_masks.append('labels')

    old_channel = self.CreateChannel(
        name=channel_name,
        display_name='my-channel',
        user_labels=old_user_labels,
        channel_labels=old_channel_labels)
    new_channel = self.CreateChannel(
        name=channel_name,
        display_name='my-channel',
        user_labels=new_user_labels,
        channel_labels=new_channel_labels)
    self._ExpectUpdate(channel_name, new_channel, old_channel=old_channel,
                       field_masks=','.join(sorted(field_masks)))
    self.Run('monitoring channels update {0} {1}'.format(
        channel_name, update_flags))

  @parameterized.parameters('user', 'channel')
  def testUpdate_UpdateLabels(self, label_type):
    kwargs = {}
    kwargs['old_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple'}
    kwargs['new_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple', 'c': 'cairplane', 'd': 'dalert'}
    self._RunLabelsTest(
        '--update-{0}-labels c=cairplane,d=dalert'.format(label_type),
        **kwargs)

  @parameterized.parameters('user', 'channel')
  def testUpdate_RemoveLabels(self, label_type):
    kwargs = {}
    kwargs['old_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple', 'c': 'cairplane', 'd': 'dalert'}
    kwargs['new_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple'}
    self._RunLabelsTest(
        '--remove-{0}-labels c,d'.format(label_type), **kwargs)

  @parameterized.parameters('user', 'channel')
  def testUpdate_ClearAndUpdateLabels(self, label_type):
    kwargs = {}
    kwargs['old_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple'}
    kwargs['new_{}_labels'.format(label_type)] = {
        'c': 'cairplane', 'd': 'dalert'}
    self._RunLabelsTest(
        '--clear-{0}-labels --update-{0}-labels c=cairplane,d=dalert'
        .format(label_type),
        **kwargs)

  @parameterized.parameters('user', 'channel')
  def testUpdate_RemoveAndUpdateLabels(self, label_type):
    kwargs = {}
    kwargs['old_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'b': 'bapple'}
    kwargs['new_{}_labels'.format(label_type)] = {
        'a': 'aardvark', 'c': 'cairplane'}
    self._RunLabelsTest(
        '--remove-{0}-labels b --update-{0}-labels c=cairplane'
        .format(label_type),
        **kwargs)

  def testUpdate_UpdateUserAndChannelLabels(self):
    self._RunLabelsTest(
        '--remove-user-labels k2 --update-user-labels k3=v3 '
        '--clear-channel-labels --update-channel-labels k6=v6,k7=v7',
        old_user_labels={'k1': 'v1', 'k2': 'v2'},
        new_user_labels={'k1': 'v1', 'k3': 'v3'},
        old_channel_labels={'k4': 'v4', 'k5': 'v5'},
        new_channel_labels={'k6': 'v6', 'k7': 'v7'})

  def testUpdate_UpdateChannelLabelsWithExistingUserLabels(self):
    self._RunLabelsTest(
        '--remove-channel-labels k4,k5 --update-channel-labels k6=v6,k7=v7',
        old_user_labels={'k1': 'v1', 'k2': 'v2'},
        new_user_labels={'k1': 'v1', 'k2': 'v2'},
        old_channel_labels={'k4': 'v4', 'k5': 'v5'},
        new_channel_labels={'k6': 'v6', 'k7': 'v7'})

  @parameterized.parameters(True, False)
  def testUpdate_FromJsonFile(self, from_file):
    channel = self.CreateChannel(
        name='channel-id',
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms')
    channel_str = encoding.MessageToJson(channel)

    if from_file:
      channel_file = self.Touch(self.temp_path, 'channel.json',
                                contents=channel_str)
      flag = '--channel-content-from-file ' + channel_file
    else:
      flag = '--channel-content \'{}\''.format(channel_str)

    self._ExpectUpdate('channel-id', channel)
    self.Run('monitoring channels update channel-id ' + flag)

  def testUpdate_AlternativeLabelsName(self):
    channel_labels = encoding.DictToAdditionalPropertyMessage(
        {'k3': 'v3', 'k4': 'v4'}, self.channel_labels_cls)
    channel = self.CreateChannel(
        name='channel-id',
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms',
        channel_labels=channel_labels)

    channel_json = json.loads(encoding.MessageToJson(channel))
    channel_json['channelLabels'] = channel_json.pop('labels')
    channel_str = json.dumps(channel_json)

    self._ExpectUpdate('channel-id', channel)
    self.Run('monitoring channels update channel-id '
             '--channel-content \'{}\''.format(channel_str))

  def testUpdate_ModifyFromString(self):
    channel = self.CreateChannel(
        name='channel-id',
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms')
    channel_str = encoding.MessageToJson(channel)
    modified_channel = self.CreateChannel(
        name='channel-id',
        display_name='my-new-channel',
        description='My new description',
        enabled=True,
        channel_type='email')

    self._ExpectUpdate('channel-id', modified_channel)
    self.Run('monitoring channels update channel-id --channel-content \'{}\' '
             '--display-name my-new-channel --description "My new description" '
             '--enabled --type email'.format(channel_str))

  def testUpdate_ModifyExisting(self):
    channel = self.CreateChannel(
        name='channel-id',
        display_name='my-channel',
        description='My Description.',
        enabled=False,
        channel_type='sms')
    modified_channel = self.CreateChannel(
        name='channel-id',
        display_name='my-new-channel',
        description='My new description',
        enabled=True,
        channel_type='email')
    field_masks = ','.join(
        sorted(['display_name', 'description', 'enabled', 'type']))

    self._ExpectUpdate('channel-id', modified_channel, old_channel=channel,
                       field_masks=field_masks)
    self.Run('monitoring channels update channel-id '
             '--display-name my-new-channel --description "My new description" '
             '--enabled --type email')

  def testUpdate_EnabledIsUpdatedCorrectly(self):
    channel = self.CreateChannel(
        name='channel-id',
        display_name='my-channel',
        description='My Description.',
        enabled=True,
        channel_type='sms')
    modified_channel = self.CreateChannel(
        name='channel-id',
        display_name='my-new-channel',
        description='My new description',
        enabled=True,
        channel_type='email')
    field_masks = ','.join(sorted(['display_name', 'description', 'type']))

    self._ExpectUpdate('channel-id', modified_channel, old_channel=channel,
                       field_masks=field_masks)
    self.Run('monitoring channels update channel-id '
             '--display-name my-new-channel --description "My new description" '
             '--type email')

  def testUpdate_ProhibitedFieldMasks(self,):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --fields: At most one of --fields'):
      self.Run('monitoring channels update channel-id --channel-content "{}" '
               '--display-name my-channel --fields enabled')

  def testUpdate_FieldMaskWithoutChannel(self,):
    with self.AssertRaisesExceptionMatches(
        exceptions.OneOfArgumentsRequiredException,
        'One of arguments [--channel-content, --channel-content-from-file] is '
        'required: If --fields is specified.'):
      self.Run('monitoring channels update channel-id --fields enabled')

  def testUpdate_UpdateArgSpecified(self,):
    with self.AssertRaisesExceptionMatches(
        util.NoUpdateSpecifiedError,
        'Did not specify any flags for updating the channel.'):
      self.Run('monitoring channels update channel-id')


if __name__ == '__main__':
  test_case.main()
