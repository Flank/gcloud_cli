# -*- coding: utf-8 -*- #
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

"""Test of the 'jobs update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base
import six


class JobsUpdateUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs update."""

  def testUpdateJobLabels(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'emca'})
    self.ExpectGetJob(original_job)
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={'customer': 'acme'})

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job, field_paths=changed_fields, response=updated_job)

    result = self.RunDataproc(
        'jobs update {0} --update-labels=customer=acme'.format(self.JOB_ID))
    self.AssertMessagesEqual(updated_job, result)

  def testAddJobLabels(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'size': 'big'})
    self.ExpectGetJob(original_job)
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={'customer': 'acme',
                                              'size': 'big'})

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job, field_paths=changed_fields, response=updated_job)

    result = self.RunDataproc(
        'jobs update {0} --update-labels=customer=acme'.format(self.JOB_ID))
    self.AssertMessagesEqual(updated_job, result)

  def testRemoveJobLabels(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'acme',
                                               'mistakeKey': 'mistakeVal'})
    self.ExpectGetJob(original_job)
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={'customer': 'acme'})

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job, field_paths=changed_fields, response=updated_job)

    result = self.RunDataproc(
        'jobs update {0} --remove-labels=mistakeKey'.format(self.JOB_ID))
    self.AssertMessagesEqual(updated_job, result)

  def testClearJobLabels(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'acme',
                                               'mistakeKey': 'mistakeVal'})
    self.ExpectGetJob(original_job)
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={})

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job, field_paths=changed_fields, response=updated_job)

    result = self.RunDataproc(
        'jobs update {0} --clear-labels'.format(self.JOB_ID))
    self.AssertMessagesEqual(updated_job, result)

  def testAllLabelsOptions(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'emca',
                                               'mistakeKey': 'mistakeVal'})
    self.ExpectGetJob(original_job)
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={'customer': 'acme',
                                              'keyonly': ''})

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job, field_paths=changed_fields, response=updated_job)

    result = self.RunDataproc(
        'jobs update {0} '
        '--remove-labels=mistakeKey '
        '--update-labels=customer=acme '
        '--update-labels=keyonly="" '.format(self.JOB_ID))
    self.AssertMessagesEqual(updated_job, result)

  def testFetchJobFailsInUpdateJob(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'emca'})
    self.ExpectGetJob(job=original_job, exception=self.MakeHttpError(404))

    with self.AssertRaisesHttpExceptionMatches('Resource not found.'):
      self.RunDataproc(
          'jobs update {0} --update-labels=customer=acme'.format(self.JOB_ID))

  def testUpdateJobFails(self):
    original_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                       labels={'customer': 'emca'})
    updated_job = self.MakeRunningJob(jobId=self.JOB_ID,
                                      labels={'customer': 'acme'})
    self.ExpectGetJob(original_job)

    changed_fields = ['labels']
    self.ExpectUpdateJob(
        job=updated_job,
        field_paths=changed_fields,
        exception=self.MakeHttpError(500))

    with self.AssertRaisesHttpExceptionMatches('Internal server error'):
      self.RunDataproc(
          'jobs update {0} --update-labels=customer=acme'.format(self.JOB_ID))

  def labelsDictToMessage(self, labels_dict):
    return self.messages.Job.LabelsValue(additionalProperties=[
        self.messages.Job.LabelsValue.AdditionalProperty(key=key, value=value)
        for key, value in sorted(six.iteritems(labels_dict))
    ])

  def ExpectUpdateJob(
      self, job, field_paths, response=None, exception=None):
    if not (response or exception):
      response = self.MakeOperation()
    self.mock_client.projects_regions_jobs.Patch.Expect(
        self.messages.DataprocProjectsRegionsJobsPatchRequest(
            jobId=job.reference.jobId,
            projectId=self.Project(),
            region=self.REGION,
            job=job,
            updateMask=','.join(field_paths)),
        response=response,
        exception=exception)


class JobsUpdateUnitTestBeta(JobsUpdateUnitTest, base.DataprocTestBaseBeta):
  """Tests for dataproc jobs update."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

if __name__ == '__main__':
  sdk_test_base.main()
