# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud datastore indexes list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.datastore import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.GA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.ALPHA)
class IndexesListTest(base.DatastoreCommandUnitTest):

  def testList(self, track):
    self.track = track
    expected_indexes = self._MakeIndexes(2)
    self._ExpectList(expected_indexes)
    self.Run('datastore indexes list')

  def testList_ProjectOverride(self, track):
    self.track = track
    expected_indexes = self._MakeIndexes(3, 'my-project')
    self._ExpectList(expected_indexes, 'my-project')
    self.Run('datastore indexes list --project=my-project')

  def testList_Uri(self, track):
    self.track = track
    expected_indexes = self._MakeIndexes(4)
    self._ExpectList(expected_indexes)
    self.Run('datastore indexes list --uri')

    self.AssertOutputEquals(
        """\
        https://datastore.googleapis.com/v1/projects/my-test-project/indexes/indexes-0
        https://datastore.googleapis.com/v1/projects/my-test-project/indexes/indexes-1
        https://datastore.googleapis.com/v1/projects/my-test-project/indexes/indexes-2
        https://datastore.googleapis.com/v1/projects/my-test-project/indexes/indexes-3
        """,
        normalize_space=True)

  def _ExpectList(self, indexes, project_id='my-test-project'):
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=project_id),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=indexes))

  def _MakeIndexes(self, n, project_id='my-test-project'):
    indexes = []
    for i in range(n):
      index = self.messages.GoogleDatastoreAdminV1Index(
          indexId='indexes-{}'.format(i), projectId=project_id)
      indexes.append(index)

    return indexes


if __name__ == '__main__':
  test_case.main()
