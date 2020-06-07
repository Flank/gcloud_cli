# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

  def buildRequest(self, is_prod=False, serve_nodes=None, kms_key=None):
    instance = self.msgs.Instance(
        displayName='thedisplayname',
        type=self.msgs.Instance.TypeValueValuesEnum.DEVELOPMENT)
    if is_prod:
      instance.type = self.msgs.Instance.TypeValueValuesEnum.PRODUCTION

    cluster = self.msgs.Cluster(
        serveNodes=serve_nodes,
        defaultStorageType=(
            self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD),
        location='projects/{0}/locations/us-central1-b'.format(self.Project()))
    if kms_key:
      cluster.encryptionConfig = self.msgs.EncryptionConfig(
          kmsKeyName=kms_key)

    return self.msgs.CreateInstanceRequest(
        instanceId='theinstance',
        parent='projects/{0}'.format(self.Project()),
        instance=instance,
        clusters=self.msgs.CreateInstanceRequest.ClustersValue(
            additionalProperties=[
                self.msgs.CreateInstanceRequest.ClustersValue
                .AdditionalProperty(key='thecluster', value=cluster)
            ]))

  def SetUp(self):
    self.svc = self.client.projects_instances.Create
    self.production_msg = self.buildRequest(True, 5)
    self.development_msg = self.buildRequest()

  def testCreateAsync(self):
    self.svc.Expect(
        request=self.buildRequest(True, 5),
        response=self.msgs.Operation(name='operations/theop'))
    self.Run(
        'bigtable instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b --display-name '
        'thedisplayname --async --instance-type PRODUCTION')
    self.AssertErrContains(
        'Create in progress for bigtable instance theinstance '
        '[operations/theop].\n')
    self.AssertOutputEquals('')

  def testCreateDisplayNameRequired(self):
    with self.AssertRaisesArgumentError():
      self.Run('bigtable instances create theinstance --cluster thecluster '
               '--cluster-num-nodes 5 --cluster-zone us-central1-b '
               '--instance-type PRODUCTION')

  def testCreateWait(self):
    self.client.projects_instances.Create.Expect(
        request=self.buildRequest(True, 5),
        response=self.msgs.Operation(name='operations/longlong', done=False),
    )
    result = self.ExpectOperation(self.client.operations, 'operations/longlong',
                                  self.client.projects_instances,
                                  'p/theinstance')
    result.displayName = 'weird instance'
    result.state = self.msgs.Instance.StateValueValuesEnum.READY

    self.Run('bigtable instances create theinstance --cluster thecluster '
             '--cluster-num-nodes 5 --cluster-zone us-central1-b '
             '--display-name thedisplayname --format=yaml')

    self.AssertErrContains('Creating bigtable instance theinstance')
    self.AssertOutputContains("""\
displayName: weird instance
name: p/theinstance
state: READY
""")

  def testCreateDevelopment(self):
    self.client.projects_instances.Create.Expect(
        request=self.buildRequest(),
        response=self.msgs.Operation(name='operations/longlong', done=False),
    )
    result = self.ExpectOperation(self.client.operations, 'operations/longlong',
                                  self.client.projects_instances,
                                  'p/theinstance')
    result.displayName = 'weird instance'
    result.state = self.msgs.Instance.StateValueValuesEnum.READY

    self.Run('bigtable instances create theinstance --cluster thecluster '
             '--cluster-zone us-central1-b --display-name '
             'thedisplayname --format=yaml --instance-type development')

    self.AssertErrContains('Creating bigtable instance theinstance')
    self.AssertOutputContains("""\
displayName: weird instance
name: p/theinstance
state: READY
""")

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.production_msg):
      self.Run(
          'bigtable instances create theinstance --cluster thecluster '
          '--cluster-num-nodes 5 --cluster-zone us-central1-b --display-name '
          'thedisplayname --async')


class CreateCommandTestBeta(CreateCommandTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateCommandTestAlpha(CreateCommandTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testKmsKeySucceeds(self):
    kms_key = 'projects/p/locations/l/keyRings/r/cryptoKeys/k'
    self.svc.Expect(
        request=self.buildRequest(True, 5, kms_key),
        response=self.msgs.Operation(name='operations/theop'))

    self.Run(
        'bigtable instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b --display-name '
        'thedisplayname --async --kms-key %s' % kms_key)
    self.AssertErrContains(
        'Create in progress for bigtable instance theinstance '
        '[operations/theop].\n')
    self.AssertOutputEquals('')

  def testSplitKmsFlagsSucceeds(self):
    kms_key = 'projects/p/locations/l/keyRings/r/cryptoKeys/k'
    self.svc.Expect(
        request=self.buildRequest(True, 5, kms_key),
        response=self.msgs.Operation(name='operations/theop'))

    self.Run(
        'bigtable instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b '
        '--display-name thedisplayname --async --kms-project p '
        '--kms-location l --kms-keyring r --kms-key k')
    self.AssertErrContains(
        'Create in progress for bigtable instance theinstance '
        '[operations/theop].\n')
    self.AssertOutputEquals('')

  def testInvalidKmsKeyFails(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run(
          'bigtable instances create theinstance --cluster thecluster '
          '--cluster-num-nodes 5 --cluster-zone us-central1-b --display-name '
          'thedisplayname --kms-key invalid/k')


if __name__ == '__main__':
  test_case.main()
