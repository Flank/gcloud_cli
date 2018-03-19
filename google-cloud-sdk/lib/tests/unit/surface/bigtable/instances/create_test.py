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
"""Test of the 'create' command."""

from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


class CreateCommandTest(base.BigtableV2TestBase,
                        waiter_test_base.CloudOperationsBase):

  def SetUp(self):
    self.svc = self.client.projects_instances.Create
    cir = self.msgs.CreateInstanceRequest
    self.production_msg = cir(
        instanceId='theinstance',
        parent='projects/{0}'.format(self.Project()),
        instance=self.msgs.Instance(
            displayName='thedisplayname',
            type=self.msgs.Instance.TypeValueValuesEnum.PRODUCTION),
        clusters=cir.ClustersValue(additionalProperties=[
            cir.ClustersValue.AdditionalProperty(
                key='thecluster',
                value=self.msgs.Cluster(
                    serveNodes=5,
                    defaultStorageType=(
                        self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD
                    ),
                    location='projects/{0}/locations/us-central1-b'.format(
                        self.Project())))
        ]))
    self.development_msg = cir(
        instanceId='theinstance',
        parent='projects/{0}'.format(self.Project()),
        instance=self.msgs.Instance(
            displayName='thedisplayname',
            type=self.msgs.Instance.TypeValueValuesEnum.DEVELOPMENT),
        clusters=cir.ClustersValue(additionalProperties=[
            cir.ClustersValue.AdditionalProperty(
                key='thecluster',
                value=self.msgs.Cluster(
                    serveNodes=None,
                    defaultStorageType=(
                        self.msgs.Cluster.DefaultStorageTypeValueValuesEnum.SSD
                    ),
                    location='projects/{0}/locations/us-central1-b'.format(
                        self.Project())))
        ]))

  def testCreateAsync(self):
    self.svc.Expect(
        request=self.production_msg,
        response=self.msgs.Operation(name='operations/theop'))
    self.RunBT(
        'instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b --display-name '
        'thedisplayname --async --instance-type PRODUCTION')
    self.AssertErrEquals(
        'Create in progress for bigtable instance theinstance '
        '[https://bigtableadmin.googleapis.com/v2/operations/theop].\n')
    self.AssertOutputEquals('')

  # TODO(b/73365914) Remove after deprecation period
  def testCreateAsyncDescription(self):
    self.svc.Expect(
        request=self.production_msg,
        response=self.msgs.Operation(name='operations/theop'))
    self.RunBT(
        'instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b --description '
        'thedisplayname --async --instance-type PRODUCTION')
    self.AssertErrContains('WARNING: Flag --description is deprecated. Use '
                           '--display-name=DISPLAY_NAME instead.')
    self.AssertErrContains(
        'Create in progress for bigtable instance theinstance '
        '[https://bigtableadmin.googleapis.com/v2/operations/theop].\n')
    self.AssertOutputEquals('')

  # TODO(b/73365914) Remove after deprecation period
  def testCreateDescriptionDisplayName(self):
    with self.AssertRaisesArgumentError():
      self.RunBT(
          'instances create theinstance --cluster thecluster '
          '--cluster-num-nodes 5 --cluster-zone us-central1-b --description '
          'thedisplayname --instance-type PRODUCTION --display-name '
          'thedisplayname')

  def testCreateDisplayNameRequired(self):
    with self.AssertRaisesArgumentError():
      self.RunBT('instances create theinstance --cluster thecluster '
                 '--cluster-num-nodes 5 --cluster-zone us-central1-b '
                 '--instance-type PRODUCTION')

  def testCreateWait(self):
    self.client.projects_instances.Create.Expect(
        request=self.production_msg,
        response=self.msgs.Operation(name='operations/longlong', done=False),)
    result = self.ExpectOperation(self.client.operations, 'operations/longlong',
                                  self.client.projects_instances,
                                  'p/theinstance')
    result.displayName = 'weird instance'
    result.state = self.msgs.Instance.StateValueValuesEnum.READY

    self.RunBT(
        'instances create theinstance --cluster thecluster '
        '--cluster-num-nodes 5 --cluster-zone us-central1-b --description '
        'thedisplayname --format=yaml')

    self.AssertErrContains('Creating bigtable instance theinstance')
    self.AssertOutputContains("""\
displayName: weird instance
name: p/theinstance
state: READY
""")

  def testCreateDevelopment(self):
    self.client.projects_instances.Create.Expect(
        request=self.development_msg,
        response=self.msgs.Operation(name='operations/longlong', done=False),)
    result = self.ExpectOperation(self.client.operations, 'operations/longlong',
                                  self.client.projects_instances,
                                  'p/theinstance')
    result.displayName = 'weird instance'
    result.state = self.msgs.Instance.StateValueValuesEnum.READY

    self.RunBT('instances create theinstance --cluster thecluster '
               '--cluster-zone us-central1-b --description '
               'thedisplayname --format=yaml --instance-type development')

    self.AssertErrContains('Creating bigtable instance theinstance')
    self.AssertOutputContains("""\
displayName: weird instance
name: p/theinstance
state: READY
""")

  def testErrorResponse(self):
    with self.AssertHttpResponseError(self.svc, self.production_msg):
      self.RunBT(
          'instances create theinstance --cluster thecluster '
          '--cluster-num-nodes 5 --cluster-zone us-central1-b --description '
          'thedisplayname --async')


if __name__ == '__main__':
  test_case.main()
