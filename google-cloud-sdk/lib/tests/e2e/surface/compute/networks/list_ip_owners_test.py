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
"""Integration tests for network list-ip-owners."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_test_base


class NetworkListIpOwnersTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testListIpOwners(self):
    self.Run('compute networks list-ip-owners default')
    self.AssertNewOutputContains(
        'IP_CIDR_RANGE SYSTEM_OWNED OWNERS', reset=False, normalize_space=True)
    self.AssertNewOutputContains('/32 True', reset=False, normalize_space=True)


if __name__ == '__main__':
  e2e_test_base.main()
