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
"""Tests for the instances add-tags subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesAddTagsTest(test_base.BaseTest):

  def testNoTagsSpecified(self):
    # See b/20548479. Should *not* crash, but rather exit gracefully with
    # helpful message.
    with self.AssertRaisesArgumentErrorMatches(
        'argument --tags: Must be specified.'
        ):
      self.Run('compute instances add-tags my-instance')

  def testWithNoExistingTags(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            tags=messages.Tags(
                fingerprint='my-fingerprint'))],
        [],
    ])

    self.Run("""
        compute instances add-tags my-instance
          --tags foo,bar
          --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetTags',
          messages.ComputeInstancesSetTagsRequest(
              instance='my-instance',
              tags=messages.Tags(
                  fingerprint='my-fingerprint',
                  items=['bar', 'foo']),
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithExistingTags(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            tags=messages.Tags(
                fingerprint='my-fingerprint',
                items=['foo', 'bar']))],
        [],
    ])

    self.Run("""
        compute instances add-tags my-instance
          --tags foo,bar,bot
          --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetTags',
          messages.ComputeInstancesSetTagsRequest(
              instance='my-instance',
              tags=messages.Tags(
                  fingerprint='my-fingerprint',
                  items=['bar', 'bot', 'foo']),
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithSameTags(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            tags=messages.Tags(
                fingerprint='my-fingerprint',
                items=['foo', 'bar']))],
    ])

    self.Run("""
        compute instances add-tags my-instance
          --tags foo,bar
          --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            tags=messages.Tags(
                fingerprint='my-fingerprint'))],
        [],
    ])

    self.Run("""
        compute instances add-tags
          https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance
          --tags foo,bar
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetTags',
          messages.ComputeInstancesSetTagsRequest(
              instance='my-instance',
              tags=messages.Tags(
                  fingerprint='my-fingerprint',
                  items=['bar', 'foo']),
              project='my-project',
              zone='us-central1-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('1\n')

    self.make_requests.side_effect = iter([
        [
            messages.Instance(name='my-instance', zone='us-central1-a'),
            messages.Instance(name='my-instance', zone='us-central1-b'),
            messages.Instance(name='my-instance', zone='us-central2-a'),
        ],

        [messages.Instance(
            name='my-instance',
            tags=messages.Tags(
                fingerprint='my-fingerprint'))],

        [],
    ])

    self.Run("""
        compute instances add-tags
          my-instance
          --tags foo,bar
        """)

    self.AssertErrContains('my-instance')
    self.AssertErrContains('us-central1-a')
    self.AssertErrContains('us-central1-b')
    self.AssertErrContains('us-central2-a')
    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('my-instance'),

        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetTags',
          messages.ComputeInstancesSetTagsRequest(
              instance='my-instance',
              tags=messages.Tags(
                  fingerprint='my-fingerprint',
                  items=['bar', 'foo']),
              project='my-project',
              zone='us-central1-a'))],
    )


if __name__ == '__main__':
  test_case.main()
