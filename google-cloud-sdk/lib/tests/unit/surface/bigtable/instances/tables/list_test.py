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

"""Test of the 'list' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.core import grpc_util
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
import six
from six.moves import range  # pylint: disable=redefined-builtin


if six.PY2:
  # TODO(b/78118402): gRPC support on Python 3.
  # This doesn't work on py3. We skip the import here just so tests can load
  # and be skipped without crashing.
  from google.bigtable.admin.v2 import bigtable_table_admin_pb2  # pylint: disable=g-import-not-at-top
  from google.bigtable.admin.v2 import bigtable_table_admin_pb2_grpc  # pylint: disable=g-import-not-at-top
  from google.bigtable.admin.v2 import table_pb2  # pylint: disable=g-import-not-at-top

  # Can't create this class on py3 because it needs the grpc pb files.
  class BigtableTestStub(bigtable_table_admin_pb2_grpc.BigtableTableAdminStub):

    def __init__(self, channel):
      # pylint:disable=invalid-name
      self.ListTables = mock.MagicMock()


@test_case.Filters.SkipOnPy3('Not yet py3 compatible', 'b/78118402')
class ListTests(sdk_test_base.WithFakeAuth,
                cli_test_base.CliTestBase,
                sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.StartObjectPatch(grpc_util, 'MakeSecureChannel')
    self.stub = BigtableTestStub(channel=None)
    self.StartObjectPatch(
        bigtable_table_admin_pb2_grpc, 'BigtableTableAdminStub',
        new=lambda _: self.stub)

  def _MakeInstanceRef(self, name):
    return resources.REGISTRY.Create(
        'bigtableadmin.projects.instances',
        instancesId=name,
        projectsId=self.Project())

  def _MakeTableRef(self, name, instance_ref):
    return resources.REGISTRY.Create(
        'bigtableadmin.projects.instances.tables',
        tablesId=name,
        **instance_ref.AsDict())

  def testEmpty_DefaultName(self):
    instance_ref = self._MakeInstanceRef('-')
    request = bigtable_table_admin_pb2.ListTablesRequest(
        parent=instance_ref.RelativeName(),
    )
    self.stub.ListTables.return_value = (
        bigtable_table_admin_pb2.ListTablesResponse())

    self.Run('beta bigtable instances tables list')

    self.AssertOutputEquals('')
    self.AssertErrEquals('Listed 0 items.\n')
    self.stub.ListTables.assert_called_once_with(request)

  def testSingle_Name(self):
    instance_ref = self._MakeInstanceRef('ocean')
    request = bigtable_table_admin_pb2.ListTablesRequest(
        parent=instance_ref.RelativeName(),
    )
    self.stub.ListTables.return_value = (
        bigtable_table_admin_pb2.ListTablesResponse(
            tables=[
                table_pb2.Table(name=self._MakeTableRef(
                    'fish1', instance_ref).SelfLink())
            ],
        ))

    self.Run('beta bigtable instances tables list --instances {}'
             .format(instance_ref.Name()))

    self.AssertOutputEquals('NAME\nfish1\n')
    self.AssertErrEquals('')
    self.stub.ListTables.assert_called_once_with(request)

  def testMultiple_Uri(self):
    instance_ref = self._MakeInstanceRef('ocean')
    request = bigtable_table_admin_pb2.ListTablesRequest(
        parent=instance_ref.RelativeName(),
    )
    fish = [self._MakeTableRef('fish' + str(i), instance_ref) for i in range(3)]
    self.stub.ListTables.return_value = (
        bigtable_table_admin_pb2.ListTablesResponse(
            tables=[table_pb2.Table(name=f.RelativeName()) for f in fish],
        ))

    self.Run('beta bigtable instances tables list --instances {} --uri'
             .format(instance_ref.Name()))

    self.AssertOutputEquals('\n'.join(f.SelfLink() for f in fish) + '\n')
    self.AssertErrEquals('')
    self.stub.ListTables.assert_called_once_with(request)


if __name__ == '__main__':
  test_case.main()
