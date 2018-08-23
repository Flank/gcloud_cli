# -*- coding: utf-8 -*- #
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
"""Tests for the zones describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class ZonesDescribeTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.ZONES[0]],
    ])

    self.Run("""
        compute zones describe us-central1-a
        """)

    self.CheckRequests(
        [(self.compute_v1.zones,
          'Get',
          messages.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-a'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
              deprecated:
                deleted: '2015-03-29T00:00:00.000-07:00'
                replacement: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-b
                state: DEPRECATED
              name: us-central1-a
              region: https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1
              selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a
              status: UP
            """))

  def testDescribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.ZONES)
    self.RunCompletion('compute zones describe ',
                       ['us-central1-a', 'us-central1-b', 'europe-west1-a'])
    self.RunCompletion('compute zones describe u',
                       ['us-central1-a', 'us-central1-b'])
    self.RunCompletion('compute zones describe e',
                       ['europe-west1-a'])

  def testCreateZonesCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.ZONES)
    self.RunCompletion('compute instances create --zone ',
                       ['us-central1-a', 'us-central1-b', 'europe-west1-a'])
    self.RunCompletion('compute instances create --zone u',
                       ['us-central1-a', 'us-central1-b'])
    self.RunCompletion('compute instances create --zone e',
                       ['europe-west1-a'])

if __name__ == '__main__':
  test_case.main()
