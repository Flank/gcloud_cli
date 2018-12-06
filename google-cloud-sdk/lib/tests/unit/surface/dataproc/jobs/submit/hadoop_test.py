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

"""Test of the 'jobs submit hadoop' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os
import tempfile
import textwrap

from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import sdk_test_base
from tests.lib.surface.dataproc import base
from tests.lib.surface.dataproc import jobs_unit_base


class JobsSubmitHadoopUnitTest(jobs_unit_base.JobsUnitTestBase):
  """Tests for dataproc jobs submit hadoop."""

  def testSubmitHadoopJob(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit hadoop --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {2} -- foo --bar baz '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitHadoopJobJarClass(self):
    job = self.MakeJob(hadoopJob=copy.deepcopy(self.HADOOP_JOB))
    job.hadoopJob.jarFileUris = [self.JAR_URI]
    with self.AssertRaisesArgumentErrorMatches(
        'argument --class: Exactly one of (--class | --jar) '
        'must be specified.'):
      self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} --jar {3} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS, self.JAR_URI))

  def testSubmitHadoopJobWithArchivesFilesJars(self):
    hadoop_job = self.HADOOP_JOB
    hadoop_job.archiveUris = self.ARCHIVE_URIS
    hadoop_job.jarFileUris = self.JAR_URIS
    hadoop_job.fileUris = self.FILE_URIS
    job = self.MakeJob(hadoopJob=hadoop_job)
    self.ExpectSubmitCalls(job)
    self.RunDataproc(
        'jobs submit hadoop --cluster {0} --id {1} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {2} --archives {3} --jars {4} --files {5} '
        '-- foo --bar baz '
        .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS,
                ','.join(self.ARCHIVE_URIS), ','.join(self.JAR_URIS),
                ','.join(self.FILE_URIS)))

  def testSubmitHadoopJobWithLabels(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)

    labels = {'some-label-key': 'some-label-value'}
    job.labels = self.ConvertLabels(labels)

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit hadoop --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--properties foo=bar,some.key=some.value '
                 '--labels some-label-key=some-label-value '
                 '--class {2} -- foo --bar baz ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitHadoopJobNoUserProvidedId(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        'jobs submit hadoop --cluster {0} '
        '--driver-log-levels root=INFO,com.example=DEBUG '
        '--properties foo=bar,some.key=some.value '
        '--class {1} -- foo --bar baz '
        .format(self.CLUSTER_NAME, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitUploads(self):
    # TODO(b/35944219): Don't create real file.
    with tempfile.NamedTemporaryFile(
        dir=self.temp_path, suffix='.jar') as local_jar:
      jar_basename = os.path.basename(local_jar.name)
      staging_dir = ('gs://test-bucket/google-cloud-dataproc-metainfo/'
                     '74048165-54a9-457c-b3d3-d4da3512e66b/jobs/'
                     'dbf5f287-f332-470b-80b2-c94b49358c45/staging/')
      staged_jar = staging_dir + jar_basename
      hadoop_job = self.messages.HadoopJob(mainJarFileUri=staged_jar)
      job = self.MakeJob(hadoopJob=hadoop_job)
      expected = self.ExpectSubmitCalls(job)
      result = self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} --jar {2}'.format(
              self.CLUSTER_NAME, self.JOB_ID, local_jar.name))
    self.AssertMessagesEqual(expected, result)
    self.mock_upload.assert_called_once_with([local_jar.name], staging_dir)
    self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))

  def testSubmitJobFailure(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    self.ExpectSubmitCalls(job, final_state=self.STATE_ENUM.ERROR)
    with self.AssertRaisesExceptionMatches(
        exceptions.JobError,
        'Job [{0}] entered state [ERROR] while waiting for [DONE].'.format(
            self.JOB_ID)):
      self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
      self.AssertErrContains(textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))

  def testSubmitJobClusterNotFound(self):
    self.ExpectGetCluster(exception=self.MakeHttpError(
        404, 'Cluster not found.'))
    with self.AssertRaisesHttpExceptionMatches(
        'Resource not found API reason: Cluster not found.'):
      self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))

  def testSubmitJobPermissionsFailure(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)
    self.ExpectGetCluster()
    self.ExpectSubmitJob(
        job, exception=self.MakeHttpError(403, 'Permission denied.'))
    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))

  def testSubmitJobBucket(self):
    # TODO(b/35944219): Don't create real file.
    with tempfile.NamedTemporaryFile(
        dir=self.temp_path, suffix='.jar') as local_jar:
      jar_basename = os.path.basename(local_jar.name)
      staging_dir = ('gs://foo-bucket/google-cloud-dataproc-metainfo/'
                     '74048165-54a9-457c-b3d3-d4da3512e66b/jobs/'
                     'dbf5f287-f332-470b-80b2-c94b49358c45/staging/')
      staged_jar = staging_dir + jar_basename
      hadoop_job = self.messages.HadoopJob(mainJarFileUri=staged_jar)
      job = self.MakeJob(hadoopJob=hadoop_job)
      expected = self.ExpectSubmitCalls(job)
      result = self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} --jar {2} '
          '--bucket=foo-bucket'.format(
              self.CLUSTER_NAME, self.JOB_ID, local_jar.name))
    self.AssertMessagesEqual(expected, result)
    self.mock_upload.assert_called_once_with([local_jar.name], staging_dir)

  def testSubmitHadoopJobNoJobGetPermission(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)

    self.ExpectGetCluster()
    self.ExpectSubmitJob(job)
    self.ExpectGetJob(
        job=job,
        exception=self.MakeHttpError(403))

    with self.AssertRaisesHttpExceptionMatches(
        'Permission denied API reason: Permission denied.'):
      self.RunDataproc(
          'jobs submit hadoop --cluster {0} --id {1} '
          '--driver-log-levels root=INFO,com.example=DEBUG '
          '--properties foo=bar,some.key=some.value '
          '--class {2} -- foo --bar baz '
          .format(self.CLUSTER_NAME, self.JOB_ID, self.CLASS))

  def testSubmitRestartableJob(self):
    job = self.MakeJob(hadoopJob=self.HADOOP_JOB)

    scheduling = self.messages.JobScheduling(maxFailuresPerHour=1)
    job.scheduling = scheduling

    expected = self.ExpectSubmitCalls(job)
    result = self.RunDataproc(
        command=('jobs submit hadoop --cluster {0} --id {1} '
                 '--driver-log-levels root=INFO,com.example=DEBUG '
                 '--properties foo=bar,some.key=some.value '
                 '--max-failures-per-hour 1 '
                 '--class {2} -- foo --bar baz ').format(
                     self.CLUSTER_NAME, self.JOB_ID, self.CLASS))
    self.AssertMessagesEqual(expected, result)
    self.AssertErrContains(
        textwrap.dedent("""\
        First line of job output.
        Next line of job output.
        Yet another line of job output.
        Last line of job output."""))
    self.AssertErrContains(
        'Job [{0}] finished successfully.'.format(self.JOB_ID))


class JobsSubmitHadoopUnitTestBeta(JobsSubmitHadoopUnitTest,
                                   base.DataprocTestBaseBeta):
  """Tests for dataproc jobs submit hadoop."""

  def testBeta(self):
    self.assertEqual(self.messages, self._beta_messages)
    self.assertEqual(self.track, calliope_base.ReleaseTrack.BETA)

  def testSubmitHadoopJobJarClass(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --class: Exactly one of (--class | --jar) must be '
        'specified.'):
      self.RunDataproc('jobs submit hadoop --cluster {0} --id {1} '
                       '--driver-log-levels root=INFO,com.example=DEBUG '
                       '--properties foo=bar,some.key=some.value '
                       '--class {2} --jar {3} -- foo --bar baz '.format(
                           self.CLUSTER_NAME, self.JOB_ID, self.CLASS,
                           self.JAR_URI))


if __name__ == '__main__':
  sdk_test_base.main()
