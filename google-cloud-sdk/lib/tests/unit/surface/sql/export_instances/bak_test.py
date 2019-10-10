# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise instance exports to bak."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class InstancesExportBakGATest(base.SqlMockTestGA):
  pass


class InstancesExportBakBetaTest(InstancesExportBakGATest,
                                 base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectExport(self, databases):
    # Generate BAK export context.
    export_context = self.messages.ExportContext(
        databases=databases,
        fileType='BAK',
        kind='sql#exportContext',
        uri='gs://speckletest/testinstance.bak',
    )

    # Mock out endpoints for export.
    self.mocked_client.instances.Export.Expect(
        self.messages.SqlInstancesExportRequest(
            instance='testinstance',
            instancesExportRequest=self.messages.InstancesExportRequest(
                exportContext=export_context),
            project=self.Project(),
        ),
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
            targetId='testinstance',
            targetLink='https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='af859489-ca9c-470f-8340-86da167b368f',
            selfLink='https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'
            .format(self.Project()),
            operationType='EXPORT',
            status='PENDING',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='af859489-ca9c-470f-8340-86da167b368f',
            project=self.Project(),
        ),
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
            targetId='testinstance',
            targetLink='https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
            .format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='af859489-ca9c-470f-8340-86da167b368f',
            selfLink='https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/af859489-ca9c-470f-8340-86da167b368f'
            .format(self.Project()),
            operationType='EXPORT',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

  def testExportMissingDatabases(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --database: Must be specified.'):
      self.Run('sql export bak testinstance gs://speckletest/testinstance.bak')

  def testExportWithDatabases(self):
    self._ExpectExport(databases=['db1'])
    self.Run('sql export bak testinstance --database=db1 '
             'gs://speckletest/testinstance.bak')

  def testExportWithDatabases_Async(self):
    self._ExpectExport(databases=['db1'])
    self.Run('sql export bak testinstance --async --database=db1 '
             'gs://speckletest/testinstance.bak')

  def testExportWithD(self):
    self._ExpectExport(databases=['db1'])
    self.Run('sql export bak testinstance -d db1 '
             'gs://speckletest/testinstance.bak')

  def testExportWithD_Async(self):
    self._ExpectExport(databases=['db1'])
    self.Run('sql export bak testinstance --async -d db1 '
             'gs://speckletest/testinstance.bak')


class InstancesExportBakAlphaTest(InstancesExportBakBetaTest,
                                  base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
