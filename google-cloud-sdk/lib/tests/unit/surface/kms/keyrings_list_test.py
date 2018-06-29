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
"""Tests that exercise the 'gcloud kms keyrings list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class KeyringsListTest(base.KmsMockTest):

  def testList(self, track):
    self.track = track
    kr_1 = self.project_name.Descendant('global/my_kr1')
    kr_2 = self.project_name.Descendant('global/my_kr2')

    self.kms.projects_locations_keyRings.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsListRequest(
            pageSize=100,
            parent=kr_1.Parent().RelativeName()),
        self.messages.ListKeyRingsResponse(keyRings=[
            self.messages.KeyRing(name=kr_1.RelativeName()),
            self.messages.KeyRing(name=kr_2.RelativeName())
        ]))

    self.Run('kms keyrings list --location={0}'.format(kr_1.location_id))
    self.AssertOutputContains(
        """NAME
{0}
{1}
""".format(kr_1.RelativeName(), kr_2.RelativeName()),
        normalize_space=True)

  def testListParentFlag(self, track):
    self.track = track
    kr_1 = self.project_name.Descendant('global/my_kr1')

    self.kms.projects_locations_keyRings.List.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsListRequest(
            pageSize=100, parent=kr_1.Parent().RelativeName()),
        self.messages.ListKeyRingsResponse(
            keyRings=[self.messages.KeyRing(name=kr_1.RelativeName())]))

    self.Run(
        'kms keyrings list --location={0}'.format(kr_1.Parent().RelativeName()))
    self.AssertOutputContains(
        """NAME
{0}
""".format(kr_1.RelativeName()), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
