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

"""Tests of the 'gcloud meta apis discovery describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class ListTest(sdk_test_base.WithFakeAuth,
               cli_test_base.CliTestBase):

  def SetUp(self):
    self.client = mock.Client(
        apis.GetClientClass('discovery', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def testList(self):
    messages = self.client.MESSAGES_MODULE
    entry = messages.DirectoryList.ItemsValueListEntry
    self.client.apis.List.Expect(
        messages.DiscoveryApisListRequest(),
        messages.DirectoryList(items=[
            entry(
                name='discovery',
                version='v1',
                title='APIs Discovery Service',
                preferred=True,
                discoveryRestUrl='https://www.googleapis.com/discovery/v1/'
                                 'apis/discovery/v1/rest',
                labels=['limited_availability'],
            )
        ])
    )

    self.Run('meta apis discovery list')
    self.AssertOutputEquals("""\
NAME       VERSION  TITLE                   PREFERRED  LABELS
discovery  v1       APIs Discovery Service  *          limited_availability
""")

  def testListUri(self):
    messages = self.client.MESSAGES_MODULE
    entry = messages.DirectoryList.ItemsValueListEntry
    self.client.apis.List.Expect(
        messages.DiscoveryApisListRequest(),
        messages.DirectoryList(items=[
            entry(
                name='discovery',
                version='v1',
                title='APIs Discovery Service',
                preferred=True,
                discoveryRestUrl='https://www.googleapis.com/discovery/v1/'
                                 'apis/discovery/v1/rest',
                labels=['limited_availability'],
            )
        ])
    )

    self.Run('meta apis discovery list --uri')
    self.AssertOutputEquals(
        'https://www.googleapis.com/discovery/v1/apis/discovery/v1/rest\n')

if __name__ == '__main__':
  cli_test_base.main()

