# -*- coding: utf-8 -*- #
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
"""Test of the 'workflow template remove-job' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import calliope

from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import jobs_unit_base


class WorkflowTemplateRemoveJobUnitTest(jobs_unit_base.JobsUnitTestBase,
                                        compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow template remove job."""

  def testRemoveJob(self):
    """Tests removing a job from a template."""
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job_1 = self.MakeOrderedJob(
        step_id='001',
        start_after=['ABC'],
        hadoopJob=self.HADOOP_JOB,
        labels=labels)
    ordered_job_2 = self.MakeOrderedJob(
        step_id='ABC', hadoopJob=self.HADOOP_JOB, labels=labels)
    workflow_template.jobs = [ordered_job_1, ordered_job_2]
    self.WriteInput('y\n')
    expected = self.ExpectUpdateWorkflowTemplatesJobCalls(
        workflow_template=workflow_template, ordered_jobs=[ordered_job_2])
    result = self.RunDataproc('workflow-templates remove-job {0} '
                              '--step-id 001'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(expected, result)

  def testRemoveJobNoJobWithStepId(self):
    workflow_template = self.MakeWorkflowTemplate()
    labels = {'some_label_key': 'some_label_value'}
    ordered_job = self.MakeOrderedJob(
        step_id='001',
        start_after=['002'],
        hadoopJob=self.HADOOP_JOB,
        labels=labels)
    workflow_template.jobs = [ordered_job]
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        response=workflow_template)
    result = self.RunDataproc('workflow-templates remove-job {0} '
                              '--step-id 12'.format(self.WORKFLOW_TEMPLATE))
    self.AssertMessagesEqual(None, result)
    err_msg = 'Step id [{0}] is not found in workflow template [{1}].'.format(
        12, workflow_template.id)
    self.AssertErrContains(err_msg)


class WorkflowTemplateRemoveJobUnitTestBeta(WorkflowTemplateRemoveJobUnitTest):

  def SetUp(self):
    self.SetupForReleaseTrack(calliope.base.ReleaseTrack.BETA)
