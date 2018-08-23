# -*- coding: utf-8 -*- #
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
"""Test of the 'update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.bigtable import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class UpdateCommandTest(base.BigtableV2TestBase):

  def SetUp(self):
    self.cmd = ('bigtable clusters update --instance theinstance thecluster '
                '--num-nodes 5 --async')
    self.svc = self.client.projects_instances_clusters.Update
    cluster_ref = resources.REGISTRY.Create(
        'bigtableadmin.projects.instances.clusters',
        projectsId=self.Project(),
        instancesId='theinstance',
        clustersId='thecluster')
    self.msg = self.msgs.Cluster(name=cluster_ref.RelativeName(),
                                 serveNodes=5)

  def testUpdate(self, track):
    self.track = track
    self.svc.Expect(request=self.msg, response=self.msgs.Operation())
    self.Run(self.cmd)
    self.AssertOutputEquals('')
    self.AssertErrContains('Update in progress for cluster [thecluster].\n')

  def testErrorResponse(self, track):
    self.track = track
    with self.AssertHttpResponseError(self.svc, self.msg):
      self.Run(self.cmd)
    self.AssertErrContains('Resource not found.')


if __name__ == '__main__':
  test_case.main()
