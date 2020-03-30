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
"""Base for all Dataflow e2e tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from tests.lib import e2e_base
from tests.lib.surface.dataflow import base

JOB_ID_PATTERN = r'[\d]{4}-[\d]{2}-[\d]{2}_[\d]{2}_[\d]{2}_[\d]{2}-[\d]+'

DATAFLOW_VERSION = 'beta'


class DataflowIntegrationTestBase(base.DataflowTestBase,
                                  e2e_base.WithServiceAuth):
  """Integration test base class for Dataflow.

  Dataflow requires the Apache Beam Java (or python) SDK in order to create a
  job and there is no API to create a job. This means for user facing code
  like the UI and the CLI there is no way to create a job; thre needs to be a
  project that already has the Dataflow jobs. All jobs are kept in the
  'dataflow-monitoring' project. This is an external project that only the
  Dataflow team has access to this. For every CLI integration test, do a
  'gcloud config set project dataflow-monitoring' to be in the proper project.
  """

  PROJECT_ID = 'dataflow-monitoring'

  def SetUp(self):
    self.Run('config set project %s' % self.PROJECT_ID)

  def Do(self, command):
    command = '%s dataflow %s' % (DATAFLOW_VERSION, command)
    logging.error(command)
    return self.Run(command)

  def IsActive(self, status):
    return status == 'Running'

  def IsTerminated(self, status):
    return status in ['Cancelled', 'Done', 'Failed', 'Stopped', 'Updated']

  def DescribeJob(self, job_id, region=None):
    region_flag = '--region=' + region if region else ''
    return self.Do('jobs describe %s %s --format=disable' % (job_id,
                                                             region_flag))

  def ShowJob(self, job_id, region=None):
    region_flag = '--region=' + region if region else ''
    return self.Do('jobs show %s %s --format=disable' % (job_id, region_flag))

  def ListMetrics(self, job_id, source='all', region=None):
    region_flag = '--region=' + region if region else ''
    return self.Do('metrics list %s %s --format=disable --source=%s' %
                   (job_id, region_flag, source))

  def ListJobs(self, status='all', uri=False, region=None):
    status_flag = '--status=' + status
    uri_flag = '--uri' if uri else ''
    region_flag = '--region=' + region if region else ''
    return list(
        self.Do('jobs list --limit=10 --format=disable %s %s %s' %
                (status_flag, uri_flag, region_flag)))

  def GetOldTerminatedJobFromList(self, region=None):
    """Find the terminated job from `jobs list` with the latest state time.

    Args:
      region: Optional parameter specifying the region in which to find a job.

    Returns:
      dict, A job description (ID, NAME, TYPE, CREATION_TIME, STATE)
    Raises:
      ValueError: If no terminated jobs are found by the CLI.
    """
    jobs = self.ListJobs('terminated --format=disable', region=region)
    if not jobs:
      raise ValueError('No terminated jobs available.')
    jobs = sorted(jobs, key=lambda x: x.stateTime)
    jobs = [job for job in jobs if job.state != 'Failed']
    return jobs[0]
