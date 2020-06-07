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
"""Test of the 'create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


class CreateCommandTestGA(base.BigtableV2TestBase,
                          waiter_test_base.CloudOperationsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.svc = self.client.projects_instances_clusters.Create

  def buildRequest(self, cluster, zone='thezone', serve_nodes=3, kms_key=None):
    new_cluster = self.msgs.Cluster(
        defaultStorageType=(self.msgs.Cluster.DefaultStorageTypeValueValuesEnum
                            .STORAGE_TYPE_UNSPECIFIED),
        location='projects/{0}/locations/{1}'.format(self.Project(), zone),
        serveNodes=serve_nodes)
    if kms_key:
      new_cluster.encryptionConfig = self.msgs.EncryptionConfig(
          kmsKeyName=kms_key)
    return self.msgs.BigtableadminProjectsInstancesClustersCreateRequest(
        cluster=new_cluster,
        clusterId=cluster,
        parent='projects/{0}/instances/{1}'.format(self.Project(),
                                                   'theinstance'))

  def testCreateDefault(self):
    self.svc.Expect(
        request=self.buildRequest('thecluster'),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable clusters create thecluster --instance theinstance '
             '--zone thezone --async')

  def testCreateCustom(self):
    self.svc.Expect(
        request=self.buildRequest(
            'anothercluster',
            zone='anotherzone',
            serve_nodes=4),
        response=self.msgs.Operation(name='operations/theoperation'))
    self.Run('bigtable clusters create anothercluster --instance theinstance '
             '--zone anotherzone --num-nodes 4 --async')

  def testCreateWait(self):
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

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc,
                                      self.buildRequest('thecluster')):
      self.Run('bigtable clusters create thecluster --instance theinstance '
               '--zone thezone --async')


class CreateCommandTestBeta(CreateCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateCommandTestAlpha(CreateCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testKmsKeySucceeds(self):
    kms_key = 'projects/p/locations/l/keyRings/r/cryptoKeys/k'
    self.svc.Expect(
        request=self.buildRequest('thecluster', kms_key=kms_key),
        response=self.msgs.Operation(name='operations/theop'))
    self.Run('bigtable clusters create thecluster --instance theinstance '
             '--zone thezone --async --kms-key %s' % kms_key)
    self.AssertErrContains(
        'Create in progress for bigtable cluster thecluster '
        '[operations/theop].\n')
    self.AssertOutputEquals('')

  def testSplitKmsFlagsSucceeds(self):
    kms_key = 'projects/p/locations/l/keyRings/r/cryptoKeys/k'
    self.svc.Expect(
        request=self.buildRequest('thecluster', kms_key=kms_key),
        response=self.msgs.Operation(name='operations/theop'))
    self.Run('bigtable clusters create thecluster --instance theinstance '
             '--zone thezone --async --kms-project p --kms-location l '
             '--kms-keyring r --kms-key k')
    self.AssertErrContains(
        'Create in progress for bigtable cluster thecluster '
        '[operations/theop].\n')
    self.AssertOutputEquals('')

  def testInvalidKmsKeyFails(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run('bigtable clusters create thecluster --instance theinstance '
               '--zone thezone --kms-key invalid/k')


if __name__ == '__main__':
  test_case.main()
