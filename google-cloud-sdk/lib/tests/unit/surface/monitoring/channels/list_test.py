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
"""Tests for `gcloud monitoring channels list`."""
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.monitoring import base


class ChannelsListTest(base.MonitoringTestBase):

  def _MakeChannels(self, project=None, n=10):
    project = project or self.Project()
    channels = []
    for i in range(n):
      channel_name = ('projects/{0}/'
                      'notificationChannels/channel-id{1}').format(project, i)
      channel = self.messages.NotificationChannel(
          name=channel_name,
          type='email',
          displayName='Channel Display Name',
      )
      channels.append(channel)
    return channels

  def _ExpectList(self, channels, project=None, page_size=None, page_token=None,
                  next_page_token=None, list_filter=None, order_by=None):
    project = project or self.Project()
    self.client.projects_notificationChannels.List.Expect(
        self.messages.MonitoringProjectsNotificationChannelsListRequest(
            name='projects/{}'.format(project),
            pageToken=page_token,
            pageSize=page_size,
            filter=list_filter,
            orderBy=order_by
        ),
        self.messages.ListNotificationChannelsResponse(
            notificationChannels=channels,
            nextPageToken=next_page_token))

  def testList(self):
    channels = self._MakeChannels()
    self._ExpectList(channels)

    results = self.Run('monitoring channels list')

    self.assertEqual(channels, results)

  def testList_Uri(self):
    jobs = self._MakeChannels(n=3)
    self._ExpectList(jobs)
    properties.VALUES.core.user_output_enabled.Set(True)

    self.Run('monitoring channels list --uri')

    self.AssertOutputEquals(
        """\
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannels/channel-id0
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannels/channel-id1
https://monitoring.googleapis.com/v3/projects/{project}/notificationChannels/channel-id2
        """.format(project=self.Project()), normalize_space=True)

  def testList_DifferentProject(self):
    project = 'other-project'
    channels = self._MakeChannels(project=project)
    self._ExpectList(channels, project=project)

    results = self.Run('monitoring channels list --project ' + project)

    self.assertEqual(channels, results)

  def testList_MultiplePages(self):
    channels = self._MakeChannels(n=10)
    self._ExpectList(channels[:5], page_size=5, next_page_token='token')
    self._ExpectList(channels[5:], page_size=5, page_token='token')

    results = self.Run('monitoring channels list --page-size 5')

    self.assertEqual(channels, results)

  def testList_WithTypeFlag(self):
    channels = self._MakeChannels(self)
    self._ExpectList(channels, list_filter='type="email"')

    results = self.Run('monitoring channels list --type email')

    self.assertEqual(channels, results)

  def testList_WithTypeFlagAndFilter(self):
    channels = self._MakeChannels(self)
    self._ExpectList(channels, list_filter='type="email" AND (name:channel-id)')

    results = self.Run('monitoring channels list --type email '
                       '--filter name:channel-id')

    self.assertEqual(channels, results)

  def testList_WithFilter(self):
    channels = self._MakeChannels(self)
    self._ExpectList(channels, list_filter='name:channel-id')

    results = self.Run('monitoring channels list --filter name:channel-id')
    self.assertEqual(channels, results)

  def testList_WithTypeAndSortByFlag(self):
    channels = self._MakeChannels(self)
    self._ExpectList(channels, list_filter='type="email"',
                     order_by='-displayName,type')

    results = self.Run('monitoring channels list --type email '
                       '--sort-by ~displayName,type')

    self.assertEqual(channels, results)


if __name__ == '__main__':
  test_case.main()
