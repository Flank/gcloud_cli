# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the instances remove-metadata subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class InstancesRemoveMetadataTest(test_base.BaseTest):

  def testWithNoKeysAndNoAllOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'One of \[--all\] or \[--keys\] must be provided.'):
      self.Run("""
          compute instances remove-metadata my-instance
            --zone us-central1-a
        """)
    self.CheckRequests()

  def testWithKeysAndAllOption(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --all: At most one of --all | --keys may be specified.'):
      self.Run("""
          compute instances remove-metadata my-instance
            --zone us-central1-a --keys x,y --all
        """)
    self.CheckRequests()

  def testWithNoExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            metadata=messages.Metadata(
                fingerprint=b'my-fingerprint'))],

        [],
    ])

    self.Run("""
        compute instances remove-metadata my-instance
          --keys x,y,z --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            metadata=messages.Metadata(
                fingerprint=b'my-fingerprint',
                items=[
                    messages.Metadata.ItemsValueListEntry(
                        key='a',
                        value='b'),
                    messages.Metadata.ItemsValueListEntry(
                        key='hello',
                        value='world'),
                    messages.Metadata.ItemsValueListEntry(
                        key='x',
                        value='y'),
                ]))],

        [],
    ])

    self.Run("""
        compute instances remove-metadata my-instance
          --keys x,hello --zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetMetadata',
          messages.ComputeInstancesSetMetadataRequest(
              instance='my-instance',
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                  ]),
              project='my-project',
              zone='us-central1-a'))],
    )

  def testWithAllOption(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            metadata=messages.Metadata(
                fingerprint=b'my-fingerprint',
                items=[
                    messages.Metadata.ItemsValueListEntry(
                        key='a',
                        value='b'),
                    messages.Metadata.ItemsValueListEntry(
                        key='hello',
                        value='world'),
                    messages.Metadata.ItemsValueListEntry(
                        key='x',
                        value='y'),
                ]))],

        [],
    ])

    self.Run("""
        compute instances remove-metadata my-instance --all
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
          'SetMetadata',
          messages.ComputeInstancesSetMetadataRequest(
              instance='my-instance',
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[]),
              project='my-project',
              zone='us-central1-a'))],
    )

  def testUriSupport(self):
    self.make_requests.side_effect = iter([
        [messages.Instance(
            name='my-instance',
            metadata=messages.Metadata(
                fingerprint=b'my-fingerprint',
                items=[
                    messages.Metadata.ItemsValueListEntry(
                        key='a',
                        value='b'),
                    messages.Metadata.ItemsValueListEntry(
                        key='hello',
                        value='world'),
                    messages.Metadata.ItemsValueListEntry(
                        key='x',
                        value='y'),
                ]))],

        [],
    ])

    self.Run("""
        compute instances remove-metadata
          https://compute.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-instance
          --keys x,hello
        """)

    self.CheckRequests(
        [(self.compute_v1.instances,
          'Get',
          messages.ComputeInstancesGetRequest(
              instance='my-instance',
              project='my-project',
              zone='us-central1-a'))],

        [(self.compute_v1.instances,
          'SetMetadata',
          messages.ComputeInstancesSetMetadataRequest(
              instance='my-instance',
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                  ]),
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
            metadata=messages.Metadata(
                fingerprint=b'my-fingerprint',
                items=[
                    messages.Metadata.ItemsValueListEntry(
                        key='a',
                        value='b'),
                    messages.Metadata.ItemsValueListEntry(
                        key='hello',
                        value='world'),
                    messages.Metadata.ItemsValueListEntry(
                        key='x',
                        value='y'),
                ]))],

        [],
    ])

    self.Run("""
        compute instances remove-metadata
          my-instance
          --keys x,hello
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
          'SetMetadata',
          messages.ComputeInstancesSetMetadataRequest(
              instance='my-instance',
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                  ]),
              project='my-project',
              zone='us-central1-a'))],
    )


if __name__ == '__main__':
  test_case.main()
