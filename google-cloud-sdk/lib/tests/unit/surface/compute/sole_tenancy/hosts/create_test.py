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
"""Tests for the sole-tenancy hosts create subcommand."""
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HostsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testDefaultOptionsWithSingleHost(self):
    with self.AssertRaisesExceptionMatches(
        base.DeprecationException,
        'New host creation is disabled. Please use `gcloud alpha '
        'compute sole-tenancy node-groups` instead.'):
      self.Run("""
          compute sole-tenancy hosts create host-1 --zone central2-a
          """)


if __name__ == '__main__':
  test_case.main()
