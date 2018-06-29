# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine jobs submit training tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
import collections
import contextlib
import json
import os
import sys

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.logs import stream
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_prep
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.ml_engine import base
import mock


LogSeverity = collections.namedtuple('LogSeverity', ['name'])


# pylint: disable=invalid-name
class Log(object):
  """Fake log object."""

  def __init__(self,
               timestamp=None,
               severity=None,
               labels=None,
               insertId=None,
               textPayload=None,
               jsonPayload=None,
               protoPayload=None,
               resourceLabels=None):

    class Resource(object):
      """Resources for a log entry."""

      def __init__(self, labels=None):
        self.labels = labels

    self.timestamp = timestamp
    self.severity = severity
    self.labels = labels
    self.insertId = insertId
    self.textPayload = textPayload
    self.jsonPayload = jsonPayload
    self.protoPayload = protoPayload
    self.resource = Resource(resourceLabels)
# pylint: enable=invalid-name


class TrainTestBase(object):

  _LOG_ENTRIES = [
      Log(
          severity=LogSeverity('INFO'),
          timestamp='2016-01-01T00:00:00Z',
          textPayload='message',
          resourceLabels={'task_name': 'service'},
          labels={'ml.googleapis.com/trial_id': '10'}),
      Log(
          severity=LogSeverity('INFO'),
          timestamp='2016-01-01T01:00:00Z',
          textPayload='message2',
          resourceLabels={'task_name': 'service'},
          labels={'ml.googleapis.com/trial_id': '20'}),
  ]

  def _MakeCreateRequest(self, job, parent):
    raise NotImplementedError()

  @property
  def state_enum(self):
    # Because this is hard to fit on one line.
    return self.short_msgs.Job.StateValueValuesEnum

  @contextlib.contextmanager
  def _AssertRaisesExitCode(self, exc_type, exit_code):
    try:
      yield
    except exc_type as err:
      self.assertEqual(err.exit_code, exit_code)
    else:
      self.fail('Should have raised googlecloudsdk.exceptions.Error')

  def _MakeLabels(self, **kwargs):
    labels_cls = self.short_msgs.Job.LabelsValue
    return labels_cls(additionalProperties=[
        labels_cls.AdditionalProperty(key=k, value=v) for k, v in
        sorted(kwargs.items())
    ])

  def _ExpectCreate(self, scale_tier=None, runtime_version=None,
                    python_version=None, job_dir='gs://job-bucket/job-prefix',
                    args=None, labels=None):
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my_job',
                labels=labels,
                trainingInput=self.short_msgs.TrainingInput(
                    pythonModule='my_module',
                    packageUris=['gs://bucket/stuff.tar.gz'],
                    scaleTier=scale_tier,
                    region='us-central1',
                    jobDir=job_dir,
                    runtimeVersion=runtime_version,
                    pythonVersion=python_version,
                    args=args or [])),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job(
            jobId='my_job',
            trainingInput=self.short_msgs.TrainingInput(
                pythonModule='my_module',
                packageUris=['gs://bucket/stuff.tar.gz'],
                scaleTier=scale_tier,
                region='us-central1',
                jobDir=job_dir,
                runtimeVersion=runtime_version,
                pythonVersion=python_version),
            state=self.state_enum.QUEUED,
            labels=labels,
            startTime='2016-01-01T00:00:00Z')
    )

  def _ExpectGet(self, state):
    scale_tier_enum = self.short_msgs.TrainingInput.ScaleTierValueValuesEnum
    self.client.projects_jobs.Get.Expect(
        self.msgs.MlProjectsJobsGetRequest(
            name='projects/{}/jobs/my_job'.format(self.Project())),
        self.short_msgs.Job(
            jobId='my_job',
            trainingInput=self.short_msgs.TrainingInput(
                pythonModule='my_module',
                packageUris=['gs://bucket/stuff.tar.gz'],
                region='us-central1',
                jobDir='gs://job-bucket/job-prefix',
                scaleTier=scale_tier_enum.CUSTOM),
            state=state,
            startTime='2016-01-01T00:00:00Z',
            endTime='2016-01-02T00:00:00Z'))

  def SetUp(self):
    self.upload_mock = self.StartObjectPatch(
        jobs_prep, 'UploadPythonPackages',
        return_value=['gs://bucket/stuff.tar.gz'])

    self.expected_request = self.short_msgs.Job(
        jobId='my_job',
        trainingInput=self.short_msgs.TrainingInput(
            pythonModule='my_module',
            packageUris=['gs://bucket/stuff.tar.gz'],
            region='us-central1',
            jobDir='gs://job-bucket/job-prefix'))
    self.staging_location = storage_util.ObjectReference.FromUrl(
        'gs://bucket/my_job')
    # For consistent output of times
    self.StartObjectPatch(times, 'LOCAL', times.GetTimeZone('PST'))

  def testTrain_Async(self):
    self._ExpectCreate(args=['--foo'])

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    -- --foo')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertOutputEquals("""\
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: QUEUED
        """, normalize_space=True)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncDeprecated(self):
    self._ExpectCreate(args=['--foo'])

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --async '
        '    -- --foo')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertOutputEquals("""\
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: QUEUED
        """, normalize_space=True)
    self.AssertErrContains("""\
        WARNING: The --async flag is deprecated, as the default behavior is to \
        submit the job asynchronously; it can be omitted. For synchronous \
        behavior, please pass --stream-logs.

        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncConfig(self):
    config_file = self.Touch(
        self.temp_path, 'config.yaml',
        contents=json.dumps({
            'trainingInput': {'args': ['foo']},
            'labels': {'key': 'value'}}))
    self._ExpectCreate(args=['foo'], labels=self._MakeLabels(key='value'))

    self.Run(
        ('ml-engine jobs submit training my_job '
         '    --module-name my_module '
         '    --package-path stuff/ '
         '    --staging-bucket gs://bucket '
         '    --job-dir gs://job-bucket/job-prefix '
         '    --region us-central1 '
         '    --config {}').format(config_file))

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncConfigEmptyArgs(self):
    config_file = self.Touch(
        self.temp_path, 'config.yaml',
        contents=json.dumps({'trainingInput': {'args': ['foo']}}))
    self._ExpectCreate(args=[])

    self.Run(
        ('ml-engine jobs submit training my_job '
         '    --module-name my_module '
         '    --package-path stuff/ '
         '    --staging-bucket gs://bucket '
         '    --job-dir gs://job-bucket/job-prefix '
         '    --region us-central1 '
         '    --config {} '
         '    --').format(config_file))

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncNoJobDir(self):
    self._ExpectCreate(job_dir=None)

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --region us-central1')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)
    self.AssertOutputEquals("""\
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: QUEUED
        """, normalize_space=True)

  def testTrain_AsyncRuntimeVersion(self):
    self._ExpectCreate(runtime_version='0.12')

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --runtime-version 0.12')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncPythonVersion(self):
    self._ExpectCreate(python_version='2.7')

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --python-version 2.7')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_AsyncLabels(self):
    self._ExpectCreate(labels=self._MakeLabels(key='value'))

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --labels key=value')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)

  def testTrain_AsyncScaleTier(self):
    scale_tier = self.short_msgs.TrainingInput.ScaleTierValueValuesEnum.CUSTOM
    self._ExpectCreate(scale_tier=scale_tier)

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --scale-tier CUSTOM')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_Logs(self):
    # Check that the polling_interval property is respected
    properties.VALUES.ml_engine.polling_interval.Set(20)
    self._ExpectCreate()
    self._ExpectGet(self.state_enum.SUCCEEDED)
    log_fetcher_mock = mock.Mock()
    log_fetcher_constructor_mock = self.StartObjectPatch(
        stream, 'LogFetcher', return_value=log_fetcher_mock)
    log_fetcher_mock.YieldLogs.return_value = iter(self._LOG_ENTRIES)

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --stream-logs')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        INFO 2015-12-31 16:00:00 -0800 service 10 message
        INFO 2015-12-31 17:00:00 -0800 service 20 message2
        """, normalize_space=True)
    self.AssertOutputEquals("""\
        endTime: '2016-01-01T16:00:00'
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: SUCCEEDED
        """, normalize_space=True)
    log_fetcher_constructor_mock.assert_called_once_with(
        continue_func=mock.ANY, filters=mock.ANY,
        polling_interval=20, continue_interval=10)

  def testTrain_LogsError(self):
    self._ExpectCreate()
    self._ExpectGet(self.state_enum.FAILED)
    self.log_fetcher_mock = self.StartObjectPatch(
        stream.LogFetcher, 'YieldLogs', return_value=iter(self._LOG_ENTRIES))

    with self._AssertRaisesExitCode(calliope_exceptions.ExitCodeNoError, 1):
      self.Run(
          'ml-engine jobs submit training my_job '
          '    --module-name my_module '
          '    --package-path stuff/ '
          '    --staging-bucket gs://bucket '
          '    --job-dir gs://job-bucket/job-prefix '
          '    --region us-central1 '
          '    --stream-logs')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        INFO 2015-12-31 16:00:00 -0800 service 10 message
        INFO 2015-12-31 17:00:00 -0800 service 20 message2
        """, normalize_space=True)
    self.AssertOutputEquals("""\
        endTime: '2016-01-01T16:00:00'
        jobId: my_job
        startTime: '2015-12-31T16:00:00'
        state: FAILED
        """, normalize_space=True)

  def testTrain_LogsCtrlC(self):
    self._ExpectCreate()
    self._ExpectGet(self.state_enum.QUEUED)
    self.log_fetcher_mock = self.StartObjectPatch(
        stream.LogFetcher, 'YieldLogs', side_effect=KeyboardInterrupt)

    with self._AssertRaisesExitCode(calliope_exceptions.ExitCodeNoError, 1):
      self.Run(
          'ml-engine jobs submit training my_job '
          '    --module-name my_module '
          '    --package-path stuff/ '
          '    --staging-bucket gs://bucket '
          '    --job-dir gs://job-bucket/job-prefix '
          '    --region us-central1 '
          '    --stream-logs')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Received keyboard interrupt.

        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_LogsPollingError(self):
    self._ExpectCreate()
    self._ExpectGet(self.state_enum.QUEUED)
    http_err = http_error.MakeHttpError(
        code=403, url='http://googleapis.com/endpoint')
    self.log_fetcher_mock = self.StartObjectPatch(
        stream.LogFetcher, 'YieldLogs', side_effect=http_err)

    with self._AssertRaisesExitCode(calliope_exceptions.ExitCodeNoError, 1):
      self.Run(
          'ml-engine jobs submit training my_job '
          '    --module-name my_module '
          '    --package-path stuff/ '
          '    --staging-bucket gs://bucket '
          '    --job-dir gs://job-bucket/job-prefix '
          '    --region us-central1 '
          '    --stream-logs')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Polling logs failed:
        HttpError accessing <http://googleapis.com/endpoint>:\
        """, normalize_space=True)
    self.AssertErrContains("""\
        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)

  def testTrain_LogsCtrlCSuccess(self):
    self._ExpectCreate()
    self._ExpectGet(self.state_enum.SUCCEEDED)
    self.log_fetcher_mock = self.StartObjectPatch(
        stream.LogFetcher, 'YieldLogs', side_effect=KeyboardInterrupt)

    self.Run(
        'ml-engine jobs submit training my_job '
        '    --module-name my_module '
        '    --package-path stuff/ '
        '    --staging-bucket gs://bucket '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region us-central1 '
        '    --stream-logs')

    self.upload_mock.assert_called_once_with(
        packages=[], package_path='stuff/',
        staging_location=self.staging_location)
    self.AssertErrContains("""\
        Job [my_job] submitted successfully.
        Received keyboard interrupt.

        Your job is still active. \
        You may view the status of your job with the command

          $ gcloud ml-engine jobs describe my_job

        or continue streaming the logs with the command

          $ gcloud ml-engine jobs stream-logs my_job
        """, normalize_space=True)


class TrainIntegrationTestBase(object):
  """Integration tests for `ml-engine jobs submit training`.

  They all do pretty much the following:

  - Set up a package structure:
    $ROOT/other.tar.gz
    $ROOT/ml/trainer/
    $ROOT/ml/trainer/__init__.py

  - Call `ml-engine jobs submit training`.

  - Check that an appropriate Job Create request was sent (mainly based on the
    args given to the command).

  - Check that the appropriate packages were copied to Cloud Storage (mocked).
    If `--package-path` was provided, it should run setuptools (mocked), on a
    copy of the directory with a `setup.py` file added, and copy every file in
    the resulting `dist` directory. If `--packages` was provided, those files
    are simply copied to Cloud Storage as-is.

  The variation is based on the combination of `--package-path` and `--packages`
  given.
  """

  _TF_CODE = """\
import tensorflow as tf

if __name__ == '__main__':
  tf.app.run()
"""
  _SETUP_PY = """\
from setuptools import setup

if __name__ == '__main__':
    setup(name='trainer', packages=['trainer'])
"""
  # This is the checksum of an empty file, which is the dummy value we're using
  # for our package.
  _EMPTY_CHECKSUM = (
      'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

  def _StoragePath(self, package_name):
    return 'gs://train-bucket/my-job/{}/{}'.format(
        self._EMPTY_CHECKSUM, package_name)

  def _StoragePathJobDir(self, package_name):
    return 'gs://job-bucket/job-prefix/packages/{}/{}'.format(
        self._EMPTY_CHECKSUM, package_name)

  def _StoragePathJobDirEmptyPrefix(self, package_name):
    return 'gs://job-bucket/packages/{}/{}'.format(
        self._EMPTY_CHECKSUM, package_name)

  def _FakeRunSetupTools(self, args, no_exit, out_func, err_func, cwd, env):
    """Mimic the behavior of setuptools."""
    del out_func, err_func, env  # Unused
    self.assertTrue(no_exit)
    self.assertEqual(os.path.basename(args[1]), 'setup.py')
    # Make some assertions about the state of the directory we're given
    self.AssertFileExistsWithContents(self._SETUP_PY, args[1])
    self.AssertFileExistsWithContents(self._TF_CODE, cwd, 'trainer', 'task.py')
    # Drop an output package in the dest-dir directory.
    dist_dir = args[args.index('--dist-dir') + 1]
    self.Touch(dist_dir, 'trainer-0.0.0.tar.gz', makedirs=True)
    return 0  # Indicates success

  def SetUp(self):
    self.package_dir = os.path.join(self.temp_path, 'ml', 'trainer')
    self.Touch(self.package_dir, '__init__.py', makedirs=True)
    self.Touch(self.package_dir, 'task.py', self._TF_CODE, makedirs=True)
    self.other_package_path = self.Touch(self.temp_path, 'other-0.0.0.tar.gz')

    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', autospec=True,
        side_effect=self._FakeRunSetupTools)
    self.StartObjectPatch(sys, 'executable', 'fake/python')

    def FakeCopyToGcs(bucket_ref, local_path, target_path):
      del local_path  # Unused.
      return storage_util.ObjectReference(bucket_ref, target_path)
    self.copy_to_gcs = self.StartObjectPatch(
        storage_api.StorageClient, 'CopyFileToGCS', side_effect=FakeCopyToGcs)
    self.bucket_ref = storage_util.BucketReference.FromBucketUrl(
        'gs://train-bucket/')
    self.job_bucket_ref = storage_util.BucketReference.FromBucketUrl(
        'gs://job-bucket/')

  def _AssertExecMockCalled(self):
    """Assert that execution_utils.Exec was called with the proper arguments."""
    self.exec_mock.assert_called_once_with(
        [mock.ANY, mock.ANY,
         'egg_info', '--egg-base', mock.ANY,
         'build', '--build-base', mock.ANY, '--build-temp', mock.ANY,
         'sdist', '--dist-dir', mock.ANY],
        cwd=mock.ANY, err_func=mock.ANY, out_func=mock.ANY, no_exit=True,
        env=mock.ANY)

  def _ExpectCreate(self, package_uris=None, job_dir=None):
    self.client.projects_jobs.Create.Expect(
        self._MakeCreateRequest(
            self.short_msgs.Job(
                jobId='my-job',
                trainingInput=self.short_msgs.TrainingInput(
                    args=['--train_dir=gs://train-bucket/my-job/train'],
                    packageUris=package_uris,
                    pythonModule='trainer.task',
                    region='us-central1',
                    jobDir=job_dir
                )
            ),
            parent='projects/{}'.format(self.Project())),
        self.short_msgs.Job())

  def testSubmit_PackagePath(self):
    self._ExpectCreate(
        package_uris=[self._StoragePath('trainer-0.0.0.tar.gz')],
        job_dir='gs://job-bucket/job-prefix')

    self.Run(
        'ml-engine jobs submit training my-job'
        '    --package-path={} '
        '    --module-name=trainer.task '
        '    --staging-bucket=gs://train-bucket/ '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.package_dir))

    self._AssertExecMockCalled()
    self.copy_to_gcs.assert_called_once_with(
        self.bucket_ref, mock.ANY,
        'my-job/{}/trainer-0.0.0.tar.gz'.format(self._EMPTY_CHECKSUM))

  def testSubmit_PackagesAndPackagePath(self):
    self._ExpectCreate(
        package_uris=[self._StoragePath('other-0.0.0.tar.gz'),
                      self._StoragePath('trainer-0.0.0.tar.gz')],
        job_dir='gs://job-bucket/job-prefix')

    self.Run(
        'ml-engine jobs submit training my-job'
        '    --package-path={} '
        '    --packages={} '
        '    --module-name=trainer.task '
        '    --staging-bucket=gs://train-bucket/ '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.package_dir, self.other_package_path))

    self._AssertExecMockCalled()
    self.copy_to_gcs.assert_has_calls(
        [
            mock.call(
                self.bucket_ref, mock.ANY,
                'my-job/{}/trainer-0.0.0.tar.gz'.format(self._EMPTY_CHECKSUM)
            ),
            mock.call(
                self.bucket_ref, mock.ANY,
                'my-job/{}/other-0.0.0.tar.gz'.format(self._EMPTY_CHECKSUM)
            )
        ], any_order=True)

  def testSubmit_PackagesJobDirAndStagingBucket(self):
    self._ExpectCreate(
        package_uris=['gs://other-bucket/other-package.tar.gz',
                      self._StoragePath('other-0.0.0.tar.gz')],
        job_dir='gs://job-bucket/job-prefix')

    self.Run(
        'ml-engine jobs submit training my-job'
        '    --packages={},gs://other-bucket/other-package.tar.gz '
        '    --module-name=trainer.task '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --staging-bucket gs://train-bucket/ '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.other_package_path))

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_called_once_with(
        self.bucket_ref, mock.ANY,
        'my-job/{}/other-0.0.0.tar.gz'.format(self._EMPTY_CHECKSUM))

  def testSubmit_PackagesNoStagingBucketNoJobDir(self):
    with self.AssertRaisesExceptionMatches(
        flags.ArgumentError,
        'the `--staging-bucket` or `--job-dir` flag must be given.'):
      # No --staging-bucket flag or job_dir
      self.Run(
          'ml-engine jobs submit training my-job'
          '    --packages={}'
          '    --module-name=trainer.task '
          '    --region=us-central1 '
          '    -- '
          '    --train_dir=gs://train-bucket/my-job/train'.format(
              self.other_package_path))

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_not_called()

  def testSubmit_PackagesJobDirNoStagingBucket(self):
    self._ExpectCreate(
        package_uris=[self._StoragePathJobDir('other-0.0.0.tar.gz')],
        job_dir='gs://job-bucket/job-prefix')

    # No --staging-bucket flag
    # Okay because there's a job_dir
    self.Run(
        'ml-engine jobs submit training my-job'
        '    --packages={}'
        '    --module-name=trainer.task '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.other_package_path))

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_called_once_with(
        self.job_bucket_ref, mock.ANY,
        'job-prefix/packages/{}/other-0.0.0.tar.gz'.format(
            self._EMPTY_CHECKSUM))

  def testSubmit_PackagesJobDirEmptyPrefixNoStagingBucket(self):
    self._ExpectCreate(
        package_uris=[self._StoragePathJobDirEmptyPrefix('other-0.0.0.tar.gz')],
        job_dir='gs://job-bucket/')

    # No --staging-bucket flag
    # Okay because there's a job_dir
    self.Run(
        'ml-engine jobs submit training my-job'
        '    --packages={}'
        '    --module-name=trainer.task '
        '    --job-dir gs://job-bucket '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.other_package_path))

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_called_once_with(
        self.job_bucket_ref, mock.ANY,
        'packages/{}/other-0.0.0.tar.gz'.format(
            self._EMPTY_CHECKSUM))

  def testSubmit_PackagesStagingBucketNoJobDir(self):
    self._ExpectCreate([self._StoragePath('other-0.0.0.tar.gz')])

    # No --job-dir flag
    # Okay because there's a --staging-bucket
    self.Run(
        'ml-engine jobs submit training my-job'
        '    --packages={}'
        '    --module-name=trainer.task '
        '    --region=us-central1 '
        '    --staging-bucket gs://train-bucket '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train'.format(
            self.other_package_path))

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_called_once_with(
        self.bucket_ref, mock.ANY,
        'my-job/{}/other-0.0.0.tar.gz'.format(self._EMPTY_CHECKSUM))

  def testSubmit_RemotePackages(self):
    self._ExpectCreate(
        package_uris=['gs://other-bucket/other-package.tar.gz'],
        job_dir='gs://job-bucket/job-prefix')

    # No --staging-bucket or job-dir flag, but that's okay.
    self.Run(
        'ml-engine jobs submit training my-job'
        '    --packages=gs://other-bucket/other-package.tar.gz '
        '    --module-name=trainer.task '
        '    --job-dir gs://job-bucket/job-prefix '
        '    --region=us-central1 '
        '    -- '
        '    --train_dir=gs://train-bucket/my-job/train')

    self.exec_mock.assert_not_called()
    self.copy_to_gcs.assert_not_called()

  def testSubmit_PackagePathDoesNotExist(self):
    with self.assertRaisesRegexp(jobs_prep.InvalidSourceDirError,
                                 'junk'):
      self.Run(
          'ml-engine jobs submit training my-job'
          '    --package-path={} '
          '    --module-name=trainer.task '
          '    --staging-bucket=gs://train-bucket/ '
          '    --job-dir gs://job-bucket/job-prefix '
          '    --region=us-central1 '
          '    -- '
          '    --train_dir=gs://train-bucket/my-job/train'.format('junk/junk'))


class TrainGaTest(TrainTestBase, base.MlGaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(TrainGaTest, self).SetUp()


class TrainBetaTest(TrainTestBase, base.MlBetaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(TrainBetaTest, self).SetUp()


class TrainIntegrationGaTest(TrainIntegrationTestBase,
                             base.MlGaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(TrainIntegrationGaTest, self).SetUp()


class TrainIntegrationBetaTest(TrainIntegrationTestBase,
                               base.MlBetaPlatformTestBase):

  def _MakeCreateRequest(self, job, parent):
    return self.msgs.MlProjectsJobsCreateRequest(googleCloudMlV1Job=job,
                                                 parent=parent)

  def SetUp(self):
    super(TrainIntegrationBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
