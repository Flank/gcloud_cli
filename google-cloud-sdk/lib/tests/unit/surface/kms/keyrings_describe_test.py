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
"""Tests that exercise the 'gcloud kms keyrings describe' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class KeyringsDescribeTest(base.KmsMockTest):

  def SetUp(self):
    self.location_name = self.project_name.Descendant('global')
    self.kr_name = self.location_name.Descendant('my_kr')

  def testDescribe(self, track):
    self.track = track

    self.kms.projects_locations_keyRings.Get.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetRequest(
            name=self.kr_name.RelativeName()),
        self.messages.KeyRing(name=self.kr_name.RelativeName()))

    self.Run('kms keyrings describe {0} --location={1}'.format(
        self.kr_name.key_ring_id, self.kr_name.location_id))

    self.AssertOutputContains('name: {0}'.format(self.kr_name.RelativeName()),
                              normalize_space=True)

  def testMissingId(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [keyring]: keyring id must be non-empty.'):
      self.Run('kms keyrings describe {0}/keyRings/'
               .format(self.location_name.RelativeName()))

if __name__ == '__main__':
  test_case.main()
