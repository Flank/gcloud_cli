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
"""dlp hooks tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.dlp import hooks
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case


class _HooksTestBase(sdk_test_base.SdkBase, parameterized.TestCase):
  """Base hooks lib Test Class"""

  def SetUp(self):
    self.msg = apis.GetMessagesModule('dlp', 'v2')
    self.test_project = 'fakeproject'
    properties.VALUES.core.project.Set(self.test_project)


class TypesTest(_HooksTestBase):
  """Tests for argparse types in hooks lib."""

  def testBigQueryInputOptions(self):
    expected_option = self.msg.GooglePrivacyDlpV2BigQueryOptions(
        tableReference=self.msg.GooglePrivacyDlpV2BigQueryTable(
            datasetId='test_data_set', projectId=self.test_project,
            tableId='mytable'))

    table_name = '{}.test_data_set.mytable'.format(self.test_project)
    result = hooks.BigQueryInputOptions(table_name)
    self.assertEqual(expected_option, result)

  @parameterized.named_parameters(
      ('TooFewParts', 'foo.bar'),
      ('Empty', ''),
      ('TooManyParts', 'foo.bar.fiz.buzz'),
  )
  def testInvalidBigQueryInputOptionsFails(self, table_name):
    with self.assertRaises(hooks.BigQueryTableNameError):
      hooks.BigQueryInputOptions(table_name)

  def testDatastoreInputOptions(self):
    expected_options = self.msg.GooglePrivacyDlpV2DatastoreOptions(
        kind=self.msg.GooglePrivacyDlpV2KindExpression(name='mykind'),
        partitionId=self.msg.GooglePrivacyDlpV2PartitionId(
            projectId=self.test_project))
    table_name = 'mykind'
    result = hooks.DatastoreInputOptions(table_name)
    self.assertEqual(expected_options, result)

  def testDatastoreInputOptionsWithNamespace(self):
    expected_options = self.msg.GooglePrivacyDlpV2DatastoreOptions(
        kind=self.msg.GooglePrivacyDlpV2KindExpression(name='mykind'),
        partitionId=self.msg.GooglePrivacyDlpV2PartitionId(
            namespaceId='mynamespace', projectId=self.test_project))
    table_name = 'mynamespace:mykind'
    result = hooks.DatastoreInputOptions(table_name)
    self.assertEqual(expected_options, result)

  def testBigQueryTableAction(self):
    expected_action = self.msg.GooglePrivacyDlpV2Action(
        saveFindings=self.msg.GooglePrivacyDlpV2SaveFindings(
            outputConfig=self.msg.GooglePrivacyDlpV2OutputStorageConfig(
                table=self.msg.GooglePrivacyDlpV2BigQueryTable(
                    datasetId='mydataset', projectId=self.test_project,
                    tableId='mytable'))))
    table_name = '{}.mydataset.mytable'.format(self.test_project)
    result = hooks.BigQueryTableAction(table_name)
    self.assertEqual(expected_action, result)

  def testBigQueryTableActionWithNoTableId(self):
    expected_action = self.msg.GooglePrivacyDlpV2Action(
        saveFindings=self.msg.GooglePrivacyDlpV2SaveFindings(
            outputConfig=self.msg.GooglePrivacyDlpV2OutputStorageConfig(
                table=self.msg.GooglePrivacyDlpV2BigQueryTable(
                    datasetId='mydataset', projectId=self.test_project,
                    tableId=''))))
    table_name = '{}.mydataset'.format(self.test_project)
    result = hooks.BigQueryTableAction(table_name)
    self.assertEqual(expected_action, result)

  @parameterized.named_parameters(
      ('TooFewParts', 'foo'),
      ('Empty', ''),
      ('TooManyParts', 'foo.bar.fiz.buzz'),
  )
  def testInvalidBigQueryTableActionFails(self, table_name):
    with self.assertRaises(hooks.BigQueryTableNameError):
      hooks.BigQueryTableAction(table_name)


class ArgumentProcessorsTest(_HooksTestBase):
  """Tests for argument processors in hooks lib."""

  _IMAGE_FILE_CONTENT = (
      b'iVBORw0KGgoAAAANSUhEUgAAAlgAAAGQBAMAAACAGwOrAAAAG1BMVEX')

  @parameterized.named_parameters(
      ('jpg', 'test_image.jpg', 'IMAGE_JPEG'),
      ('jpeg', 'test_image.jpeg', 'IMAGE_JPEG'),
      ('png', 'test_image.png', 'IMAGE_PNG'),
      ('svg', 'test_image.svg', 'IMAGE_SVG'),
      ('bmp', 'test_image.bmp', 'IMAGE_BMP'),
  )
  def testGetImageFromFile(self, file_name, file_type):
    test_image_file = self.Touch(self.root_path, file_name,
                                 contents=self._IMAGE_FILE_CONTENT)
    expected_image_item = self.msg.GooglePrivacyDlpV2ByteContentItem(
        data=self._IMAGE_FILE_CONTENT,
        type=(self.msg.GooglePrivacyDlpV2ByteContentItem.
              TypeValueValuesEnum.lookup_by_name(file_type)))
    result = hooks.GetImageFromFile(test_image_file)
    self.assertEqual(expected_image_item, result)

  @parameterized.named_parameters(
      ('Missing', 'missing.jpg', False),
      ('BadExtension', 'bad_name.jpr', True),
  )
  def testGetImageFromFileBadFileFails(self, file_name, write_content):
    if write_content:
      input_file = self.Touch(self.root_path, file_name,
                              contents=self._IMAGE_FILE_CONTENT)
    else:
      input_file = file_name

    with self.assertRaises(hooks.ImageFileError):
      hooks.GetImageFromFile(input_file)

  @parameterized.named_parameters(
      ('ExplicitFloats', 1.0, 0.5, 0.3),
      ('ConvertibleFloats', 1, 1, 0),
      ('Mixed', 1, 0, 0.5),
  )
  def testGetRedactColorFromString(self, red, green, blue):
    expected_color = self.msg.GooglePrivacyDlpV2Color(
        red=red, green=green, blue=blue)
    color_string = '{},{},{}'.format(red, green, blue)
    result = hooks.GetRedactColorFromString(color_string)
    self.assertEqual(expected_color, result)

  @parameterized.named_parameters(
      ('NonFloats', '1,1,g'),
      ('TooManyValues', '1.0,1.0,0.4,0.6'),
      ('TooFewValues', '0,0'),
      ('ValuesOutOfRange', '1.0,1.0,2.0'),
  )
  def testGetRedactColorFromStringBadInputFails(self, color_string):
    with self.assertRaises(hooks.RedactColorError):
      hooks.GetRedactColorFromString(color_string)


class RequestHooksTest(_HooksTestBase):
  """Tests for requesthooks in hooks lib."""

  def SetUp(self):
    # Faking argparse.NameSpace for testing
    self.namespace_fake = collections.namedtuple(
        'Namespace', ['sort_by', 'project'])

  def testSetRequestParentFromProperty(self):
    args = self.namespace_fake(sort_by=None, project=None)
    updated_request = hooks.SetRequestParent(
        None, args, self.msg.DlpProjectsContentInspectRequest())
    expected_parent = 'projects/fakeproject'
    self.assertEqual(expected_parent, updated_request.parent)

  def testSetRequestParentFromFlag(self):
    args = self.namespace_fake(sort_by=None, project='myotherproject')
    updated_request = hooks.SetRequestParent(
        None, args, self.msg.DlpProjectsContentInspectRequest())
    expected_parent = 'projects/myotherproject'
    self.assertEqual(expected_parent, updated_request.parent)

  def testUpdateDataStoreOptionsFrom(self):
    args = self.namespace_fake(sort_by=None, project='new_project')

    kind_exp = self.msg.GooglePrivacyDlpV2KindExpression(name='ds_kind')
    partition = self.msg.GooglePrivacyDlpV2PartitionId(
        namespaceId='ds_namespace_id', projectId='initial_project_id')

    datastore_option = self.msg.GooglePrivacyDlpV2DatastoreOptions(
        kind=kind_exp, partitionId=partition)
    storage_config = self.msg.GooglePrivacyDlpV2StorageConfig(
        datastoreOptions=datastore_option)
    inspect_job = self.msg.GooglePrivacyDlpV2InspectJobConfig(
        storageConfig=storage_config)
    job_trigger = self.msg.GooglePrivacyDlpV2JobTrigger(
        inspectJob=inspect_job)

    create_request = self.msg.GooglePrivacyDlpV2CreateJobTriggerRequest(
        jobTrigger=job_trigger, triggerId='mytrigger')
    request = self.msg.DlpProjectsJobTriggersCreateRequest(
        googlePrivacyDlpV2CreateJobTriggerRequest=create_request,
        parent='projects/' + self.test_project)

    result = hooks.UpdateDataStoreOptions(None, args, request)
    datastore_project_id = (
        result.googlePrivacyDlpV2CreateJobTriggerRequest.
        jobTrigger.inspectJob.storageConfig.datastoreOptions.partitionId.
        projectId)
    self.assertEqual('new_project', datastore_project_id)

  @parameterized.named_parameters(
      ('AscendingOrder', ['field1', 'field2'], 'field1 asc,field2 asc'),
      ('DecendingOrder', ['~field1', '~field2'], 'field1 desc,field2 desc'),
      ('MixedOrder', ['field1', '~field2'], 'field1 asc,field2 desc'),
  )
  def testSetOrderByFromSortBy(self, sortby, orderby):
    args = self.namespace_fake(sort_by=sortby, project=None)
    request = self.msg.DlpProjectsJobTriggersListRequest(
        parent='projects/' + self.test_project)
    result = hooks.SetOrderByFromSortBy(None, args, request)
    self.assertEqual(orderby, result.orderBy)


if __name__ == '__main__':
  test_case.main()
