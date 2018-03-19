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
"""Tests for the project-info remove-metadata subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class ProjectInfoRemoveMetadataTest(test_base.BaseTest):

  def testWithNoKeysAndNoAllOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'One of \[--all\] or \[--keys\] must be provided.'):
      self.Run("""
          compute project-info remove-metadata
        """)
    self.CheckRequests()

  def testWithKeysAndAllOption(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --all: At most one of --all | --keys may be specified.'):
      self.Run("""
          compute project-info remove-metadata
                 --keys a,b --all
          """)
    self.CheckRequests()

  def testWithNoExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [messages.Project(
            name='my-project',
            commonInstanceMetadata=messages.Metadata())],

        [],
    ])

    self.Run("""
        compute project-info remove-metadata --keys x,y,z
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

  def testWithExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [messages.Project(
            name='my-project',
            commonInstanceMetadata=messages.Metadata(
                fingerprint='my-fingerprint',
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
        compute project-info remove-metadata --keys hello,x
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],

        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(
                  fingerprint='my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                  ]),
              project='my-project'))],
    )

  def testWithExistingMetadataAndNoChanges(self):
    self.make_requests.side_effect = iter([
        [messages.Project(
            name='my-project',
            commonInstanceMetadata=messages.Metadata(
                fingerprint='my-fingerprint',
                items=[
                    messages.Metadata.ItemsValueListEntry(
                        key='x',
                        value='y'),
                    messages.Metadata.ItemsValueListEntry(
                        key='hello',
                        value='world'),
                    messages.Metadata.ItemsValueListEntry(
                        key='a',
                        value='b'),
                ]))],

        [],
    ])

    self.Run("""
        compute project-info remove-metadata --keys fish,bacon
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

  def testWithAllOption(self):
    self.make_requests.side_effect = iter([
        [messages.Project(
            name='my-project',
            commonInstanceMetadata=messages.Metadata(
                fingerprint='my-fingerprint',
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
        compute project-info remove-metadata --all
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],

        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(
                  fingerprint='my-fingerprint',
                  items=[]),
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
