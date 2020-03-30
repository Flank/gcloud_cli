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
"""Tests for `gcloud monitoring channels describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class ChannelsDescribeTest(base.MonitoringTestBase):

  def PreSetUp(self):
    super(ChannelsDescribeTest, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def _MakeChannel(self):
    channel_name = ('projects/{}/notificationChannels/'
                    'my-channel').format(self.Project())
    return self.messages.NotificationChannel(
        name=channel_name,
        type='my-channel',
    )

  def _ExpectDescribe(self, channel):
    self.client.projects_notificationChannels.Get.Expect(
        self.messages.MonitoringProjectsNotificationChannelsGetRequest(
            name=channel.name,
        ),
        channel)

  def testDescribe(self):
    channel = self._MakeChannel()
    self._ExpectDescribe(channel)

    result = self.Run('monitoring channels describe my-channel')
    self.assertEqual(channel, result)

  def testDescribe_Uri(self):
    channel = self._MakeChannel()
    self._ExpectDescribe(channel)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    url = ('http://monitoring.googleapis.com/v3/projects/{}'
           '/notificationChannels/my-channel').format(self.Project())
    self.Run('monitoring channels describe ' + url)

  def testDescribe_RelativeNameOverridesProjectProperty(self):
    channel = self._MakeChannel()
    self._ExpectDescribe(channel)
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')

    relative_name = ('projects/{}/notificationChannels/'
                     'my-channel').format(self.Project())
    self.Run('monitoring channels describe ' + relative_name)


if __name__ == '__main__':
  test_case.main()
