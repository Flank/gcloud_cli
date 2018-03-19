# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests that exercise instance exports to csv."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime

from apitools.base.protorpclite import util as protorpc_util

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesExportCsvTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectExport(self, databases=None, query=None):
    # Generate CSV export context.
    export_context = self.messages.ExportContext(
        csvExportOptions=self.messages.ExportContext.
        CsvExportOptionsValue(
            selectQuery=query,),
        databases=databases or [],
        fileType='CSV',
        kind=u'sql#exportContext',
        sqlExportOptions=None,
        uri=u'gs://speckletest/testinstance.gz')

    # Mock out endpoints for export.
    self.mocked_client.instances.Export.Expect(
        self.messages.SqlInstancesExportRequest(
            instance='testinstance',
            instancesExportRequest=self.messages.InstancesExportRequest(
                exportContext=export_context),
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                20,
                50,
                43,
                963000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=export_context,
            importContext=None,
            targetId=u'testinstance',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'af859489-ca9c-470f-8340-86da167b368f',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'.
            format(self.Project()),
            operationType=u'EXPORT',
            status=u'PENDING',
            user=u'170350250316@developer.gserviceaccount.com'))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation=u'af859489-ca9c-470f-8340-86da167b368f',
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                20,
                50,
                43,
                963000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                13,
                20,
                50,
                44,
                13000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                13,
                20,
                50,
                49,
                639000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=export_context,
            importContext=None,
            targetId=u'testinstance',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'af859489-ca9c-470f-8340-86da167b368f',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'.
            format(self.Project()),
            operationType=u'EXPORT',
            status=u'DONE',
            user=u'170350250316@developer.gserviceaccount.com'))

  def testSimpleExport(self):
    self._ExpectExport(query='SELECT * FROM table')
    self.Run('sql export csv testinstance --query="SELECT * FROM table" '
             'gs://speckletest/testinstance.gz')

  def testSimpleExport_Async(self):
    self._ExpectExport(query='SELECT * FROM table')
    self.Run('sql export csv testinstance --query="SELECT * FROM table" '
             '--async gs://speckletest/testinstance.gz')

  def testExportWithDatabases(self):
    self._ExpectExport(query='SELECT * FROM table', databases=['db1', 'db2'])
    self.Run('sql export csv testinstance --database=db1,db2 '
             '--query="SELECT * FROM table" gs://speckletest/testinstance.gz')


class InstancesExportCsvBetaTest(_BaseInstancesExportCsvTest,
                                 base.SqlMockTestBeta):
  pass


class InstancesExportCsvGATest(_BaseInstancesExportCsvTest, base.SqlMockTestGA):
  pass


if __name__ == '__main__':
  test_case.main()
