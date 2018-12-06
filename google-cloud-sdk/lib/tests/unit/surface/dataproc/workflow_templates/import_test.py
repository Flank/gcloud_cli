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
"""Test of the 'workflow-templates import' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import files
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateImportUnitTest(unit_base.DataprocUnitTestBase,
                                     compute_base.BaseComputeUnitTest):
  """Tests for workflow-templates import."""

  def ExpectCreateWorkflowTemplate(self,
                                   workflow_template=None,
                                   response=None,
                                   parent=None,
                                   exception=None):
    if not parent:
      parent = self.WorkflowTemplateParentName()
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    if not (response or exception):
      response = workflow_template
    self.mock_client.projects_regions_workflowTemplates.Create.Expect(
        self.messages.DataprocProjectsRegionsWorkflowTemplatesCreateRequest(
            workflowTemplate=workflow_template, parent=parent),
        response=response,
        exception=exception)

  def ExpectUpdateWorkflowTemplate(self,
                                   workflow_template=None,
                                   response=None,
                                   exception=None):
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    if not (response or exception):
      response = workflow_template
    self.mock_client.projects_regions_workflowTemplates.Update.Expect(
        workflow_template, response=response, exception=exception)

  def testImportWorkflowTemplatesFromStdIn(self):
    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    # The id is populated before we make the create request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE

    # The create response has the name populated.
    expected_response = copy.deepcopy(expected_request)
    expected_response.name = self.WorkflowTemplateName()

    self.WriteInput(export_util.Export(provided_template))
    self.ExpectGetWorkflowTemplate(
        exception=self.MakeHttpError(status_code=404))
    self.ExpectCreateWorkflowTemplate(expected_request, expected_response)
    result = self.RunDataproc('workflow-templates import {0}'.format(
        self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(expected_response, result)

  def testImportWorkflowTemplatesInvalid(self):
    self.WriteInput('foo: bar')
    with self.AssertRaisesExceptionMatches(
        yaml_validator.ValidationError,
        "Additional properties are not allowed "
        "('foo' was unexpected)"):
      self.RunDataproc('workflow-templates import {0}'.format(
          self.WORKFLOW_TEMPLATE))

  def testImportWorkflowTemplatesHttpError(self):
    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    # The id is populated before we make the create request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE

    self.WriteInput(export_util.Export(provided_template))
    self.ExpectGetWorkflowTemplate(
        exception=self.MakeHttpError(status_code=403))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc('workflow-templates import {0}'.format(
          self.WORKFLOW_TEMPLATE))

  def testImportWorkflowTemplatesCreateNew(self):
    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    # The id is populated before we make the create request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE

    # The create response has the name populated.
    expected_response = copy.deepcopy(expected_request)
    expected_response.name = self.WorkflowTemplateName()

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=provided_template, stream=stream)

    self.ExpectGetWorkflowTemplate(
        exception=self.MakeHttpError(status_code=404))
    self.ExpectCreateWorkflowTemplate(expected_request, expected_response)
    result = self.RunDataproc(
        'workflow-templates import {0} --source {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.AssertMessagesEqual(expected_response, result)

  def testImportWorkflowTemplatesCreateNewWithRegion(self):
    # Set region property.
    properties.VALUES.dataproc.region.Set('us-test1')

    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    # The id is populated before we make the create request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE

    # The create response has the name populated.
    expected_response = copy.deepcopy(expected_request)
    expected_response.name = self.WorkflowTemplateName(region='us-test1')

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=provided_template, stream=stream)

    self.ExpectGetWorkflowTemplate(
        name=self.WorkflowTemplateName(region='us-test1'),
        exception=self.MakeHttpError(status_code=404))
    parent = self.WorkflowTemplateParentName(region='us-test1')
    self.ExpectCreateWorkflowTemplate(
        workflow_template=expected_request,
        response=expected_response,
        parent=parent)
    result = self.RunDataproc(
        'workflow-templates import {0} --source {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.AssertMessagesEqual(expected_response, result)

  def testImportWorkflowTemplatesCreateNewWithRegionNoZone(self):
    # Set region property.
    properties.VALUES.dataproc.region.Set('us-test1')

    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    # Provided template has a managed cluster with a name, but no zone.
    managed_cluster = self.messages.ManagedCluster(clusterName='test-cluster')
    provided_template.placement = self.messages.WorkflowTemplatePlacement(
        managedCluster=managed_cluster)

    # The id is populated before we make the create request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE

    # The create response has the name populated.
    expected_response = copy.deepcopy(expected_request)
    expected_response.name = self.WorkflowTemplateName(region='us-test1')

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(
          message=provided_template,
          stream=stream,
          schema_path=export_util.GetSchemaPath(
              'dataproc', 'v1', 'WorkflowTemplate'))

    self.ExpectGetWorkflowTemplate(
        name=self.WorkflowTemplateName(region='us-test1'),
        exception=self.MakeHttpError(status_code=404))
    parent = self.WorkflowTemplateParentName(region='us-test1')
    self.ExpectCreateWorkflowTemplate(
        workflow_template=expected_request,
        response=expected_response,
        parent=parent)
    result = self.RunDataproc(
        'workflow-templates import {0} --source {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.AssertMessagesEqual(expected_response, result)

  def testImportWorkflowTemplatesUpdateExisting(self):
    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    get_response = self.MakeWorkflowTemplate()
    get_response.version = 1

    # The id, name, and version are populated before we make the update request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE
    expected_request.name = self.WorkflowTemplateName()
    expected_request.version = 1

    # Response has version incremented.
    expected_response = copy.deepcopy(expected_request)
    expected_response.version = 2

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=provided_template, stream=stream)

    self.ExpectGetWorkflowTemplate(response=get_response)
    self.ExpectUpdateWorkflowTemplate(
        workflow_template=expected_request, response=expected_response)
    self.WriteInput('y\n')
    result = self.RunDataproc(
        'workflow-templates import {0} --source {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.AssertMessagesEqual(expected_response, result)

  def testImportWorkflowTemplatesUpdateExistingWithRegion(self):
    # Set region property.
    properties.VALUES.dataproc.region.Set('us-test1')

    # Provided template does not have an id or a name.
    provided_template = self.MakeWorkflowTemplate()
    provided_template.id = None
    provided_template.name = None

    get_response = self.MakeWorkflowTemplate()
    get_response.version = 1
    get_response.name = self.WorkflowTemplateName(region='us-test1')

    # The id, name, and version are populated before we make the update request.
    expected_request = copy.deepcopy(provided_template)
    expected_request.id = self.WORKFLOW_TEMPLATE
    expected_request.name = self.WorkflowTemplateName(region='us-test1')
    expected_request.version = 1

    # Response has version incremented.
    expected_response = copy.deepcopy(expected_request)
    expected_response.version = 2

    # Write test template to file.
    file_name = os.path.join(self.temp_path, 'template.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=provided_template, stream=stream)

    self.ExpectGetWorkflowTemplate(
        name=self.WorkflowTemplateName(region='us-test1'),
        response=get_response)
    self.ExpectUpdateWorkflowTemplate(
        workflow_template=expected_request, response=expected_response)
    self.WriteInput('y\n')
    result = self.RunDataproc(
        'workflow-templates import {0} --source {1}'.format(
            self.WORKFLOW_TEMPLATE, file_name))
    self.AssertMessagesEqual(expected_response, result)


class WorkflowTemplateImportUnitTestBeta(WorkflowTemplateImportUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)
