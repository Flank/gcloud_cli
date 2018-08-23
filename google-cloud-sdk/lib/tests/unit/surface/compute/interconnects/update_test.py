# -*- coding: utf-8 -*- #
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
"""Tests for the interconnect create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


def RunInTracks(alpha=True, beta=True, ga=True):
  args = []
  if alpha:
    args.append(('Alpha', base.ReleaseTrack.ALPHA, 'alpha'))
  if beta:
    args.append(('Beta', base.ReleaseTrack.BETA, 'beta'))
  if ga:
    args.append(('GA', base.ReleaseTrack.GA, 'v1'))
  return parameterized.named_parameters(*args)


class InterconnectsUpdateTest(test_base.BaseTest, parameterized.TestCase):

  def _SetUp(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)

  def CheckInterconnectRequest(self, **kwargs):
    interconnect_msg = {}
    interconnect_msg.update(kwargs)
    self.CheckRequests([(self.compute.interconnects, 'Patch',
                         self.messages.ComputeInterconnectsPatchRequest(
                             project='my-project',
                             interconnect='my-interconnect',
                             interconnectResource=self.messages.Interconnect(
                                 **interconnect_msg)))],)

  @RunInTracks()
  def testUpdateDescription(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--description "this is your interconnect"')

    self.CheckInterconnectRequest(description='this is your interconnect')

  @RunInTracks()
  def testUpdateAdminEnabled(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect ' '--admin-enabled')

    self.CheckInterconnectRequest(adminEnabled=True)

  @RunInTracks()
  def testUpdateNoAdminEnabled(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--no-admin-enabled')

    self.CheckInterconnectRequest(adminEnabled=False)

  @RunInTracks()
  def testUpdateRequestedLinkCount(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--requested-link-count 25')

    self.CheckInterconnectRequest(requestedLinkCount=25)

  @RunInTracks()
  def testUpdateNocContactEmail(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--noc-contact-email jack@google.com')

    self.CheckInterconnectRequest(nocContactEmail='jack@google.com')

  @RunInTracks()
  def testUpdateMultipleFields(self, track, api_version):
    self._SetUp(track, api_version)
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.Interconnect(
                name='my-interconnect',
                description='this is your interconnect',
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--noc-contact-email jack@google.com --requested-link-count 25 '
             '--description "this is your interconnect" '
             '--admin-enabled')

    self.CheckInterconnectRequest(
        nocContactEmail='jack@google.com',
        requestedLinkCount=25,
        adminEnabled=True,
        description='this is your interconnect')

  @RunInTracks(alpha=True, beta=True, ga=False)
  def testUpdateLabels(self, track, api_version):
    self._SetUp(track, api_version)
    labels_cls = self.messages.Interconnect.LabelsValue
    old_labels = labels_cls(
        additionalProperties=[
            labels_cls.AdditionalProperty(key='key1', value='value1'),
            labels_cls.AdditionalProperty(key='key2', value='value2'),
        ]
    )
    new_labels = labels_cls(
        additionalProperties=[
            labels_cls.AdditionalProperty(key='key1', value='value1'),
            labels_cls.AdditionalProperty(key='key2', value='new_value'),
            labels_cls.AdditionalProperty(key='key3', value='value3'),
        ]
    )

    self.make_requests.side_effect = iter([
        [
            self.messages.Interconnect(
                name='my-interconnect',
                labels=old_labels,
                labelFingerprint=b'abcd'
            ),
        ],
        [
            self.messages.Interconnect(
                name='my-interconnect',
                labels=old_labels
            )
        ],
    ])

    self.Run('compute interconnects update my-interconnect '
             '--update-labels key2=new_value,key3=value3')

    self.CheckRequests(
        [(self.compute.interconnects, 'Get',
          self.messages.ComputeInterconnectsGetRequest(
              project='my-project', interconnect='my-interconnect'))],
        [(self.compute.interconnects, 'Patch',
          self.messages.ComputeInterconnectsPatchRequest(
              project='my-project', interconnect='my-interconnect',
              interconnectResource=self.messages.Interconnect(
                  labelFingerprint=b'abcd',
                  labels=new_labels)))])


if __name__ == '__main__':
  test_case.main()
