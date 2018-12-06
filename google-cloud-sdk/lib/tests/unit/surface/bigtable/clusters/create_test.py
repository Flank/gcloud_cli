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
"""Test of the 'create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA)
class CreateCommandTest(base.BigtableV2TestBase,
                        waiter_test_base.CloudOperationsBase):

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters.Create

  def buildRequest(self,
                   cluster,
                   zone='thezone',
                   serve_nodes=3):
    return self.msgs.BigtableadminProjectsInstancesClustersCreateRequest(
        cluster=self.msgs.Cluster(
            defaultStorageType=(
                self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.
                STORAGE_TYPE_UNSPECIFIED),
            location='projects/{0}/locations/{1}'.format(self.Project(), zone),
            serveNodes=serve_nodes),
        clusterId=cluster,
        parent='projects/{0}/instances/{1}'.format(self.Project(),
                                                   'theinstance'))

  def testCreateDefault(self, track):
    self.track = track
    self.svc.Expect(
        request=self.buildRequest('thecluster'),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable clusters create thecluster --instance theinstance '
             '--zone thezone --async')

  def testCreateCustom(self, track):
    self.track = track
    self.svc.Expect(
        request=self.buildRequest(
            'anothercluster',
            zone='anotherzone',
            serve_nodes=4),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable clusters create anothercluster --instance theinstance '
             '--zone anotherzone --num-nodes 4 --async')

  def testCreateWait(self, track):
    self.track = track
    self.svc.Expect(
        request=self.buildRequest('thecluster'),
        response=self.msgs.Operation(
            name='operations/theoperation', done=False))
    result = self.ExpectOperation(
        self.client.operations, 'operations/theoperation',
        self.client.projects_instances_clusters, 'p/thecluster')
    result.state = self.msgs.Cluster.StateValueValuesEnum.READY

    self.Run('bigtable clusters create thecluster --instance theinstance '
             '--zone thezone --format=yaml')

    self.AssertErrContains('Creating bigtable cluster thecluster')
    self.AssertErrContains('SUCCESS')
    self.AssertOutputEquals("""\
name: p/thecluster
state: READY
""")

  def testErrorResponse(self, track):
    self.track = track
    with self.AssertHttpResponseError(self.svc,
                                      self.buildRequest('thecluster')):
      self.Run('bigtable clusters create thecluster --instance theinstance '
               '--zone thezone --async')


if __name__ == '__main__':
  test_case.main()
