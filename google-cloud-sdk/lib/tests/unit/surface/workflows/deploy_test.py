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
"""Tests for workflows create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib.apitools import http_error
from tests.lib.surface.workflows import base

WORKFLOW_ID = 'testWorkflow'

OLD_SOURCE = 'test_workflow_old_source_(incorrect)'
NEW_SOURCE = 'test_workflow_new_source_(incorrect)'

OLD_DESCRIPTION = 'test_workflow_old_description'
NEW_DESCRIPTION = 'test_workflow_new_description'

NEW_SERVICE_ACCOUNT = 'test-account@my-project.iam.gserviceaccount.com'


class WorkflowsDeployTest(parameterized.TestCase, base.WorkflowsUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDeploy_noId(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument (WORKFLOW : --location=LOCATION): Must be specified.'):
      self.Run('workflows deploy --source=ignored_source')
    self.AssertOutputEquals('')

  def testDeploy_noSourceOnFirstDeployment(self):
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)
    self.ExpectGet(workflow_name, exception=http_error.MakeHttpError(code=404))

    with self.AssertRaisesToolExceptionMatches(
        'Missing required argument [--source]: required on first deployment'):
      self.Run('workflows deploy {}'.format(WORKFLOW_ID))
    self.AssertOutputEquals('')

  def testDeploy_noSourceOnSubsequentDeployment(self):
    old_workflow = self.messages.Workflow()
    new_workflow = self.messages.Workflow(description=NEW_DESCRIPTION)
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)

    self.ExpectGet(workflow_name, result=old_workflow)
    self.ExpectUpdate(workflow_name, new_workflow, update_mask='description')
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=new_workflow)

    result = self.Run('workflows deploy {id} '
                      '--description={description}'.format(
                          id=WORKFLOW_ID, description=NEW_DESCRIPTION))
    self.assertEqual(result, new_workflow)

  def testDeploy_customRegion(self):
    workflow = self.messages.Workflow(sourceContents=NEW_SOURCE)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    region = 'europe-west1'
    workflow_name = self.GetWorkflowName(WORKFLOW_ID, region)

    self.ExpectGet(workflow_name, exception=http_error.MakeHttpError(code=404))
    self.ExpectCreate(self.GetLocationName(region), WORKFLOW_ID, workflow)
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=workflow)

    result = self.Run('workflows deploy {id} '
                      '--source={source} '
                      '--location={region}'.format(
                          id=WORKFLOW_ID, source=source_path, region=region))
    self.assertEqual(result, workflow)

  def testDeploy_regionProperty(self):
    workflow = self.messages.Workflow(sourceContents=NEW_SOURCE)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    region = 'europe-west1'
    workflow_name = self.GetWorkflowName(WORKFLOW_ID, region)

    self.ExpectGet(workflow_name, exception=http_error.MakeHttpError(code=404))
    self.ExpectCreate(self.GetLocationName(region), WORKFLOW_ID, workflow)
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=workflow)

    prop = properties.FromString('workflows/location')
    prop.Set(region)
    result = self.Run('workflows deploy {id} --source={source} '.format(
        id=WORKFLOW_ID, source=source_path))
    self.assertEqual(result, workflow)

  def testDeploy_simpleServiceAccount(self):
    full_service_account = 'projects/-/serviceAccounts/' + NEW_SERVICE_ACCOUNT
    workflow = self.messages.Workflow(sourceContents=NEW_SOURCE,
                                      serviceAccount=full_service_account)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)

    self.ExpectGet(workflow_name, exception=http_error.MakeHttpError(code=404))
    self.ExpectCreate(self.GetLocationName(), WORKFLOW_ID, workflow)
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=workflow)

    result = self.Run('workflows deploy {id} '
                      '--source={source} '
                      '--service-account={sa}'.format(
                          id=WORKFLOW_ID,
                          source=source_path,
                          sa=NEW_SERVICE_ACCOUNT))
    self.assertEqual(result, workflow)

  def testDeploy_createAllArguments(self):
    full_service_account = 'projects/-/serviceAccounts/' + NEW_SERVICE_ACCOUNT
    workflow = self.messages.Workflow(sourceContents=NEW_SOURCE,
                                      description=NEW_DESCRIPTION,
                                      serviceAccount=full_service_account)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)

    self.ExpectGet(workflow_name, exception=http_error.MakeHttpError(code=404))
    self.ExpectCreate(self.GetLocationName(), WORKFLOW_ID, workflow)
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=workflow)

    result = self.Run('workflows deploy {id} '
                      '--source={source} '
                      '--description={desc} '
                      '--service-account={sa}'.format(
                          id=WORKFLOW_ID,
                          source=source_path,
                          desc=NEW_DESCRIPTION,
                          sa=full_service_account))
    self.assertEqual(result, workflow)

  def testDeploy_updateSourceContents(self):
    old_workflow = self.messages.Workflow(sourceContents=OLD_SOURCE)
    new_workflow = self.messages.Workflow(sourceContents=NEW_SOURCE)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)

    self.ExpectGet(workflow_name, result=old_workflow)
    self.ExpectUpdate(workflow_name, new_workflow, update_mask='sourceContents')
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=new_workflow)

    result = self.Run('workflows deploy {id} --source={source}'.format(
        id=WORKFLOW_ID, source=source_path))
    self.assertEqual(result, new_workflow)

  def testDeploy_updateDescription(self):
    old_workflow = self.messages.Workflow(description=OLD_DESCRIPTION)
    new_workflow = self.messages.Workflow(description=NEW_DESCRIPTION)
    workflow_name = self.GetWorkflowName(WORKFLOW_ID)

    self.ExpectGet(workflow_name, result=old_workflow)
    self.ExpectUpdate(workflow_name, new_workflow, update_mask='description')
    self.MockOperationWait()
    self.ExpectGet(workflow_name, result=new_workflow)

    result = self.Run('workflows deploy {id} '
                      '--description={desc}'.format(
                          id=WORKFLOW_ID,
                          desc=NEW_DESCRIPTION))
    self.assertEqual(result, new_workflow)

  LONG_WORKFLOW_NAME_MESSAGE = (
      'Invalid value for [workflow]: ID must be between 1-64 characters long')
  WORKFLOW_START_LETTER_MESSAGE = (
      'Invalid value for [workflow]: ID must start with a letter')
  WORKFLOW_END_ALPHANUMERIC_MESSAGE = (
      'Invalid value for [workflow]: ID must end with a letter or number')
  WORKFLOW_INVALID_CHARS_MESSAGE = (
      'Invalid value for [workflow]: ID must only contain letters, numbers, '
      'underscores and hyphens'
  )

  @parameterized.named_parameters(
      ('Workflow name too long',
       'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklm',
       LONG_WORKFLOW_NAME_MESSAGE),
      ('Workflow name cannot start with a number',
       '1testWorkflow', WORKFLOW_START_LETTER_MESSAGE),
      ('Workflow name cannot start with underscore',
       '_testWorkflow', WORKFLOW_START_LETTER_MESSAGE),
      ('Workflow name cannot end with underscore',
       'testWorkflow_', WORKFLOW_END_ALPHANUMERIC_MESSAGE),
      ('Workflow name cannot end with dash',
       'testWorkflow-', WORKFLOW_END_ALPHANUMERIC_MESSAGE),
      ('Workflow name cannot contain spaces',
       '"test Workflow"', WORKFLOW_INVALID_CHARS_MESSAGE),
      ('Workflow name cannot contain special chars',
       '"test~Workflow"', WORKFLOW_INVALID_CHARS_MESSAGE)
  )
  def testDeploy_workflowNamesInvalid(self, workflow_name, exception_message):
    with self.AssertRaisesToolExceptionMatches(exception_message):
      self.Run('workflows deploy {}'.format(workflow_name))
    self.AssertOutputEquals('')

  @parameterized.named_parameters(
      ('Workflow name just fits',
       'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkl'),
      ('Workflow name ends with number',
       'testWorkflow1'),
      ('Workflow name contains dashes and underscores',
       't_e-st__Work--flow'),
  )
  def testDeploy_workflowNamesValid(self, workflow_name):
    workflow = self.messages.Workflow(sourceContents=NEW_SOURCE)
    source_path = self.Touch(
        self.temp_path, name='workflow.yaml', contents=NEW_SOURCE)
    full_workflow_name = self.GetWorkflowName(workflow_name)

    self.ExpectGet(
        full_workflow_name, exception=http_error.MakeHttpError(code=404))
    self.ExpectCreate(self.GetLocationName(), workflow_name, workflow)
    self.MockOperationWait()
    self.ExpectGet(full_workflow_name, result=workflow)

    result = self.Run('workflows deploy {id} --source={source}'.format(
        id=workflow_name, source=source_path))
    self.assertEqual(result, workflow)


class WorkflowsDeployTestAlpha(WorkflowsDeployTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

