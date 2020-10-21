# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the instances set-name subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InstancesSetNameTestBeta(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.messages = core_apis.GetMessagesModule('compute', 'beta')

  def _CreateSetNameRequest(self, name, current_name):
    return (self.compute.instances,
            'SetName',
            self.messages.ComputeInstancesSetNameRequest(
                instancesSetNameRequest=self.messages.InstancesSetNameRequest(
                    name=name, currentName=current_name),
                instance=current_name,
                project='my-project',
                zone='central2-a'))

  def _CreateGetRequest(self, name):
    return (self.compute.instances,
            'Get',
            self.messages.ComputeInstancesGetRequest(
                instance=name, project='my-project', zone='central2-a'))

  def testWithDefaults(self):
    self.make_requests.side_effect = iter([
        [self.messages.Instance(name='instance-1')],
        [],
    ])

    self.Run("""
          compute instances set-name instance-1
          --zone central2-a
          --new-name instance-2
        """)

    self.CheckRequests([self._CreateGetRequest(name='instance-1')], [
        self._CreateSetNameRequest(
            name='instance-2', current_name='instance-1')
    ])

  def testWithNoNameSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --new-name: Must be specified.'):
      self.make_requests.side_effect = iter([
          [self.messages.Instance(name='instance-1')],
          [],
      ])

      self.Run('compute instances set-name instance-1')

  def testWithSameName(self):
    self.make_requests.side_effect = iter([
        [self.messages.Instance(name='instance-1')],
        [],
    ])

    self.Run("""
          compute instances set-name instance-1
          --zone central2-a
          --new-name instance-1
        """)

    self.CheckRequests([self._CreateGetRequest(name='instance-1')])


class InstancesSetNameTestAlpha(InstancesSetNameTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')


if __name__ == '__main__':
  test_case.main()
