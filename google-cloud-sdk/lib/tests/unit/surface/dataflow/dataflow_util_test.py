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
"""Tests for dataflow_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import exceptions
from googlecloudsdk.command_lib.dataflow import dataflow_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.calliope import util
from tests.lib.surface.dataflow import base

ERROR = http_error.MakeHttpError(404, 'Not Found')


class _BaseDataflowHelpersTest(base.DataflowMockingTestBase):

  def SetUp(self):
    parser = util.ArgumentParser()
    parser.add_argument(
        '--region', help='The region ID of the job\'s regional endpoint.')
    self.parser = parser


class DataflowUtilTest(_BaseDataflowHelpersTest):

  def testGetErrorMessage(self):
    self.assertEqual('Not Found', dataflow_util.GetErrorMessage(ERROR))

  def testGetErrorMessageWithUnknownError(self):
    err = http_error.MakeHttpError(444, 'Unknown error')
    self.assertEqual('Unknown error', dataflow_util.GetErrorMessage(err))

  def testMakeErrorMessageNoJobNoProjectNoRegion(self):
    msg = dataflow_util.MakeErrorMessage(ERROR)
    self.assertEqual('Failed operation: Not Found', msg)

  def testMakeErrorMessage(self):
    msg = dataflow_util.MakeErrorMessage(
        ERROR, job_id='job', project_id='project', region_id='region')
    self.assertEqual('Failed operation with job ID [job] in project [project] '
                     'in regional endpoint [region]: Not Found', msg)

  def testMakeErrorMessageNoProject(self):
    msg = dataflow_util.MakeErrorMessage(
        ERROR, job_id='job', region_id='region')
    self.assertEqual(
        'Failed operation with job ID [job] in regional endpoint [region]: '
        'Not Found', msg)

  def testMakeErrorMessageNoJob(self):
    msg = dataflow_util.MakeErrorMessage(
        ERROR, project_id='project', region_id='region')
    self.assertEqual(
        'Failed operation in project [project] in regional endpoint [region]: '
        'Not Found', msg)

  def testMakeErrorMessageNoRegion(self):
    msg = dataflow_util.MakeErrorMessage(
        ERROR, job_id='job', project_id='project')
    self.assertEqual(
        'Failed operation with job ID [job] in project [project]: Not Found',
        msg)

  def testJobsUriFromId(self):
    url = dataflow_util.JobsUriFromId('jobID', 'test-region')
    self.assertEqual(
        'https://dataflow.googleapis.com/v1b3/projects/fake-project'
        '/locations/test-region/jobs/jobID', url)

  def testYieldExceptionWrapperCanIterate(self):
    length = 2

    def Generator():
      num = 0
      while num < length:
        yield num
        num += 1

    wrapper = dataflow_util.YieldExceptionWrapper(Generator())
    array = []
    array.append(next(wrapper))
    array.append(next(wrapper))
    self.assertEqual([0, 1], array)

  def testYieldExceptionWrapperEmitsException(self):
    def Generator():
      yield 0
      raise ERROR

    wrapper = dataflow_util.YieldExceptionWrapper(Generator())
    next(wrapper)
    with self.AssertRaisesExceptionMatches(
        exceptions.ServiceException,
        'Failed operation: Not Found'):
      next(wrapper)

  def testGetRegion(self):
    args = self.parser.parse_args(['--region=not-us-central1'])
    self.assertEqual('not-us-central1', dataflow_util.GetRegion(args))

  def testGetRegionEmpty(self):
    args = self.parser.parse_args(['--region='])
    self.assertEqual('us-central1', dataflow_util.GetRegion(args))


if __name__ == '__main__':
  test_case.main()
