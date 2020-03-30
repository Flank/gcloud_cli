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
"""Tests for `gcloud monitoring channels delete`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class ChannelsDeleteTest(base.MonitoringTestBase):

  def PreSetUp(self):
    super(ChannelsDeleteTest, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def _ExpectDelete(self, force=False):
    channel_name = ('projects/{}/'
                    'notificationChannels/channel-id').format(self.Project())
    self.client.projects_notificationChannels.Delete.Expect(
        self.messages.MonitoringProjectsNotificationChannelsDeleteRequest(
            name=channel_name,
            force=force,
        ),
        self.messages.Empty())

  def testDelete(self):
    self._ExpectDelete()
    self.WriteInput('y')
    self.Run('monitoring channels delete channel-id')

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_Force(self):
    self._ExpectDelete(force=True)
    self.WriteInput('y')
    self.Run('monitoring channels delete channel-id --force')

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_Cancel(self):
    self.WriteInput('n')

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('monitoring channels delete channel-id')

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_Uri(self):
    self._ExpectDelete()
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')
    self.WriteInput('y')

    url = ('http://monitoring.googleapis.com/v3/projects/{}'
           '/notificationChannels/channel-id').format(self.Project())
    self.Run('monitoring channels delete ' + url)

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDescribe_RelativeNameOverridesProjectProperty(self):
    self._ExpectDelete()
    self.addCleanup(properties.VALUES.core.project.Set, self.Project())
    properties.VALUES.core.project.Set('other-project')
    self.WriteInput('y')

    relative_name = ('projects/{}/notificationChannels/'
                     'channel-id').format(self.Project())
    self.Run('monitoring channels delete ' + relative_name)

    self.AssertOutputEquals('')
    self.AssertErrContains('PROMPT_CONTINUE')


if __name__ == '__main__':
  test_case.main()
