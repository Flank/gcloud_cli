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
"""Tests for the public advertised prefixes delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class PublicAdvertisedPrefixesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[
        self.messages.Operation(
            operationType='delete',
            status=self.messages.Operation.StatusValueValuesEnum.DONE)
    ]])
    self.WriteInput('y\n')
    self.Run('compute public-advertised-prefixes delete my-pap')
    self.CheckRequests(
        [(self.compute.publicAdvertisedPrefixes, 'Delete',
          self.messages.ComputePublicAdvertisedPrefixesDeleteRequest(
              publicAdvertisedPrefix='my-pap', project='my-project'))],)
    self.AssertErrContains('Deleted public advertised prefix [my-pap]')


if __name__ == '__main__':
  test_case.main()
