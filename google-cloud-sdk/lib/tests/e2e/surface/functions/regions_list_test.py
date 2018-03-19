# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Integration test for the 'functions regions list' command."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case


class RegionsListIntegrationTest(e2e_base.WithServiceAuth):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testListRegions(self):
    self.Run('functions regions list')
    self.AssertOutputContains(
        'projects/{0}/locations/us-central1'.format(self.Project()))

if __name__ == '__main__':
  test_case.main()
