# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud datastore indexes describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.datastore import base


@parameterized.parameters(calliope_base.ReleaseTrack.GA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.ALPHA)
class IndexesDescribeTest(base.DatastoreCommandUnitTest):

  def testDescribe(self, track):
    self.track = track
    self._ExpectDescribe()
    self.Run('datastore indexes describe my-index')
    self.AssertOutputEquals(
        """\
        indexId: my-index
        projectId: my-test-project
        """,
        normalize_space=True)

  def testDescribe_RelativeName(self, track):
    self.track = track
    self._ExpectDescribe()
    self.Run(
        'datastore indexes describe projects/my-test-project/indexes/my-index')

  def testDescribe_ProjectOverride(self, track):
    self.track = track
    self._ExpectDescribe(project_id='my-project')
    self.Run('datastore indexes describe my-index --project=my-project')

  def _ExpectDescribe(self, project_id='my-test-project'):
    self.projects_indexes.Get.Expect(
        request=self.messages.DatastoreProjectsIndexesGetRequest(
            indexId='my-index', projectId=project_id),
        response=self.messages.GoogleDatastoreAdminV1Index(
            indexId='my-index', projectId=project_id))


if __name__ == '__main__':
  test_case.main()
