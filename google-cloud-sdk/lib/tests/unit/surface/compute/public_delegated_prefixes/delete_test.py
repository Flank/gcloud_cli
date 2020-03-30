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
"""Tests for the public delegated prefixes delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class PublicDelegatedPrefixesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.region = 'us-central1'

  def testDelete_global(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)
    ]])
    self.WriteInput('y\n')
    self.Run('compute public-delegated-prefixes delete my-pdp --global')
    self.CheckRequests(
        [(self.compute.globalPublicDelegatedPrefixes, 'Delete',
          self.messages.ComputeGlobalPublicDelegatedPrefixesDeleteRequest(
              publicDelegatedPrefix='my-pdp', project='my-project'))],)
    self.AssertErrContains('Deleted public delegated prefix [my-pdp]')

  def testDelete_regional(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)
    ]])
    self.WriteInput('y\n')
    self.Run(
        'compute public-delegated-prefixes delete my-pdp --region {}'.format(
            self.region))
    self.CheckRequests(
        [(self.compute.publicDelegatedPrefixes, 'Delete',
          self.messages.ComputePublicDelegatedPrefixesDeleteRequest(
              publicDelegatedPrefix='my-pdp',
              project='my-project',
              region=self.region))],)
    self.AssertErrContains('Deleted public delegated prefix [my-pdp]')


if __name__ == '__main__':
  test_case.main()
