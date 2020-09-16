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
"""Tests of the 'deploy' command."""

# TODO(b/74342501) Move this file to parent folder once old deploy tests are
# retired

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import zipfile

from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.functions import env_vars as env_vars_api_util
from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.functions import util as api_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions.deploy import trigger_util
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.functions import base
from tests.lib.surface.functions import util as testutil

import mock
from six.moves import range


_TEST_FUNCTION_FILE = 'functions.js'
_TEST_EXCLUDE_FILE = 'foobar.txt'
_TEST_GS_BUCKET = 'gs://fake_bucket'
_DEFAULT_REGION = 'us-central1'
_DEFAULT_FUNCTION_NAME = 'my-test'
_SUCCESSFUL_DEPLOY_STDERR = """\
{"ux": "PROGRESS_TRACKER", "message": "Deploying function (may take a while - up to 2 minutes)", "status": "SUCCESS"}
"""
_NO_UPDATE_STDERR = """\
Nothing to update.
"""

_TEST_EVENT_TRIGGER_TYPES = {
    'pubsub_legacy': 'providers/cloud.pubsub/eventTypes/topic.publish',
    'pubsub': 'google.pubsub.topic.publish',
    'gcs_legacy': 'providers/cloud.storage/eventTypes/object.change',
    'gcs': 'google.storage.object.finalize'
}


class DeployTestBase(base.FunctionsTestBase):
  """Base Test class for deployment workflows for functions deploy command."""

  def AssertNodeModulesNotUploaded(self, source_archive_path):
    """Asserts that node_modules does not appear in prepared source archive."""
    source_zip = zipfile.ZipFile(source_archive_path)
    has_node_modules = [
        'node_modules' in f.filename for f in source_zip.infolist()
    ]
    self.assertFalse(any(has_node_modules))

  def MockUploadToSignedUrl(self, status_code=200, empty_response=False):
    """Mock upload to signed url."""
    def MockMakeRequest(http, request, retries=None, max_retry_wait=None,
                        redirections=None, retry_func=None,
                        check_response_func=None):
      del http, retries, max_retry_wait, redirections, retry_func
      if empty_response:  # Handle empty server response edge case.
        check_response_func(None)
      self.assertEqual('foo', request.url)
      self.assertEqual('PUT', request.http_method)
      fname_suffix = self.RandomFileName()
      tmp_zip_file = self.Touch(self.temp_path,
                                'tmp_{}.zip'.format(fname_suffix),
                                contents=request.body)
      self.AssertNodeModulesNotUploaded(tmp_zip_file)
      return http_wrapper.Response(
          info={'status': status_code, 'location': request.url}, content='',
          request_url=request.url)

    self.StartObjectPatch(http_wrapper, 'MakeRequest', MockMakeRequest)

  def MockLongRunningOpResult(self, op_name, poll_count=2, is_error=False):
    """Get Expectation for a LRO."""
    for _ in range(poll_count):
      in_progress_op = self._GenerateActiveOperation(op_name)
      self.mock_client.operations.Get.Expect(
          self.messages.CloudfunctionsOperationsGetRequest(name=op_name),
          in_progress_op)

    if is_error:
      op_done_response = self._GenerateFailedOperation(op_name)
    else:
      op_done_response = self._GenerateSuccessfulOperation(op_name)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(name=op_name),
        op_done_response)

    return op_done_response

  def WriteExtraneousFiles(self,
                           source_dir,
                           use_node_modules=False,
                           use_git=False,
                           ignore_file=False):
    """Write files to source_dir that should be filtered by gcloudignore."""
    path = source_dir
    if use_node_modules:
      path = '{}/{}'.format(path, 'node_modules')
    else:
      self.UpdateIgnoreFile(path, use_git, ignore_file)

    self.Touch(
        path,
        'skip_me.txt',
        makedirs=True,
        contents=(' ' * self.ReturnLargeFileSize()))

  def UpdateIgnoreFile(self, path, use_git, ignore_file):
    if ignore_file:
      self.Touch(path, '.ignore_file_test', contents='skip_me.txt')
    elif use_git:
      self.Touch(path, '.gitignore', contents='skip_me.txt')
    else:
      self.Touch(path, '.gcloudignore', contents='skip_me.txt')

  def RemoveIgnoreFile(self, path):
    ignore_files = ['{}/.gcloudignore'.format(path),
                    '{}/.gitignore'.format(path),
                    '{}/.ignore_file_test'.format(path)]
    try:
      for f in ignore_files:
        os.remove(f)
    except OSError:
      pass  # Ignore File Not Exits Errors.

  def MockUploadToGCSBucket(self):
    """Mock uploading the function archive to cloud storage."""
    def FakeCopyFileToGCS(client_obj, local_path, target_obj_ref):
      del client_obj, target_obj_ref
      self.AssertNodeModulesNotUploaded(local_path)
    self.StartObjectPatch(storage_api.StorageClient,
                          'CopyFileToGCS',
                          FakeCopyFileToGCS)
    self.StartObjectPatch(storage_util.ObjectReference, 'ToUrl',
                          return_value=_TEST_GS_BUCKET)

  def PrepareLocalSource(self,
                         file_name=_TEST_FUNCTION_FILE,
                         write_extra_files=False,
                         use_node_modules=False,
                         use_git=False,
                         ignore_file=False):
    """Write Test function source with optional files to be filtered."""
    path = self.CreateTempDir()
    self.Touch(path, 'package.json', contents='package_foo')
    self.Touch(path, file_name, contents='foo')
    if write_extra_files:
      self.WriteExtraneousFiles(path, use_git=use_git, ignore_file=ignore_file)
    elif use_git:
      raise ValueError('Cannot pass `use_git` without `write_extra_files`')
    return path

  def GetPubSubTrigger(self, project, topic, retry=False,
                       trigger_type='pubsub'):
    result = self.messages.EventTrigger(
        eventType=_TEST_EVENT_TRIGGER_TYPES[trigger_type],
        resource=self.GetTopicResource(topic),
    )
    if retry:
      result.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry())
    return result

  def GetGcsTrigger(self, project, bucket,
                    event_type='gcs', retry=False):
    result = self.messages.EventTrigger(
        eventType=_TEST_EVENT_TRIGGER_TYPES[event_type],
        resource=self.GetBucketResource(bucket),
    )
    if retry:
      result.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry())
    return result

  def GetFunctionsGetRequest(self, location, name):
    return self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
        name=self.GetFunctionResource(location, name))

  def MockGetExistingFunction(self,
                              response=None,
                              project=None,
                              region=_DEFAULT_REGION,
                              name=_DEFAULT_FUNCTION_NAME):
    """Set mock call for Get of existing function."""

    project = project or self.Project()
    get_request = self.GetFunctionsGetRequest(region, name)
    if response:
      self.mock_client.projects_locations_functions.Get.Expect(
          get_request, response)
    else:
      self.mock_client.projects_locations_functions.Get.Expect(
          get_request, exception=testutil.CreateTestHttpError(404, 'Not Found'))

  def MockGeneratedApiUploadUrl(self, project=None, region=_DEFAULT_REGION):
    """Mock generated upload url for a function."""
    project = project or self.Project()
    upload_url = self.messages.GenerateUploadUrlResponse(uploadUrl='foo')
    self.mock_client.projects_locations_functions.GenerateUploadUrl.Expect(
        (self.messages.
         CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest
        )(parent='projects/{}/locations/{}'.format(project, region)),
        upload_url)

  def GetLocationResource(self):
    location_ref = resources.REGISTRY.Parse(
        _DEFAULT_REGION,
        params={'projectsId': self.Project()},
        collection='cloudfunctions.projects.locations')
    return location_ref.RelativeName()

  def GetFunctionResource(self, location, name):
    function_ref = resources.REGISTRY.Parse(
        name,
        params={'projectsId': self.Project(),
                'locationsId': location},
        collection='cloudfunctions.projects.locations.functions')
    return function_ref.RelativeName()

  def GetTopicResource(self, name):
    topic_ref = resources.REGISTRY.Parse(
        name,
        params={'projectsId': self.Project()},
        collection='pubsub.projects.topics')
    return topic_ref.RelativeName()

  def GetBucketResource(self, bucket):
    return 'projects/_/buckets/{}'.format(bucket)

  def GetFunctionsCreateRequest(self, function, location):
    return self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
        location=location, cloudFunction=function)

  def GetLabelsMessage(self, labels=None):
    if labels:
      labels.insert(0, ('deployment-tool', 'cli-gcloud'))
    else:
      labels = [('deployment-tool', 'cli-gcloud')]

    labels_value = self.messages.CloudFunction.LabelsValue
    additional_property = labels_value.AdditionalProperty
    additional_properties = [
        additional_property(key=k, value=v) for k, v in (
            sorted(labels, key=lambda x: x[0]))
    ]
    return labels_value(additionalProperties=additional_properties)

  def GetFunctionMessage(self,
                         location,
                         name,
                         event_trigger=None,
                         memory=None,
                         https_trigger=None,
                         entry_point=None,
                         source_archive=None,
                         source_repository_url=None,
                         source_upload_url=None,
                         timeout=None,
                         labels=None,
                         env_vars=None,
                         runtime=None):
    if labels is None:
      labels = self.GetLabelsMessage()
    if source_repository_url:
      source_repository = self.messages.SourceRepository(
          url=source_repository_url,)
    else:
      source_repository = None

    return self.messages.CloudFunction(
        name=self.GetFunctionResource(location, name),
        sourceArchiveUrl=source_archive,
        sourceRepository=source_repository,
        sourceUploadUrl=source_upload_url,
        eventTrigger=event_trigger,
        httpsTrigger=https_trigger,
        entryPoint=entry_point,
        timeout=timeout,
        labels=labels,
        availableMemoryMb=memory,
        environmentVariables=env_vars,
        runtime=runtime)

  def ExpectFunctionPatch(
      self, function_name, original_function, updated_function,
      update_mask=None, expect_get_upload_url=False):
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=function_name),
        original_function)
    if expect_get_upload_url:
      self.MockGeneratedApiUploadUrl()
    self.mock_client.projects_locations_functions.Patch.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsPatchRequest(
            cloudFunction=updated_function,
            name=function_name,
            updateMask=update_mask
        ),
        self._GenerateActiveOperation('operations/operation')
    )

    self.MockLongRunningOpResult('operations/operation')

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=updated_function.name),
        updated_function)


class PackagingTest(DeployTestBase):
  """Test of source code packaging workflows for functions deploy command."""

  def SetUp(self):
    self._dirs_size_limit_method = 513 * (2**20)

  def _MockBasicFunctionCreate(self):
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.MockGeneratedApiUploadUrl()
    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_upload_url='foo', runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockUploadToSignedUrl()
    self.MockGetExistingFunction(response=function)
    return function

  @parameterized.parameters([True, False])
  def testPackageFilesWithIgnoreFile(self, use_node_modules):
    path = self.PrepareLocalSource(
        write_extra_files=True, use_node_modules=use_node_modules,
        ignore_file=True)

    function = self._MockBasicFunctionCreate()

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source {} --quiet --runtime=nodejs6 '
                      '--ignore-file .ignore_file_test'.format(path))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testInvalidIgnoreFile(self):
    path = self.PrepareLocalSource()
    self.RemoveIgnoreFile(path)
    self.MockGetExistingFunction(response=None)
    with self.assertRaisesRegex(
        exceptions.FileNotFoundError,
        'File .ignore_file_test referenced by --ignore-file does not exist.'):
      self.Run('functions deploy my-test --trigger-http '
               '--source {} --quiet --runtime=nodejs6 '
               '--ignore-file .ignore_file_test'.format(path))
    self.AssertErrNotContains(_SUCCESSFUL_DEPLOY_STDERR)

  @parameterized.parameters([True, False])
  def testPackageFilesWithGcloudIgnore(self, use_node_modules):
    path = self.PrepareLocalSource(
        write_extra_files=True, use_node_modules=use_node_modules)

    function = self._MockBasicFunctionCreate()

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source {} --quiet --runtime=nodejs6'.format(path))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  @parameterized.parameters([True, False])
  def testPackageFilesWithGitignore(self, use_node_modules):
    path = self.PrepareLocalSource(
        write_extra_files=True, use_node_modules=use_node_modules, use_git=True)

    function = self._MockBasicFunctionCreate()

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source {} --quiet --runtime=nodejs6'.format(path))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  @parameterized.parameters([True, False])
  def testPackageBadFilesWithNoIgnoreFileFails(self, use_node_modules):
    path = self.PrepareLocalSource(
        write_extra_files=True, use_node_modules=use_node_modules)
    self.RemoveIgnoreFile(path)
    self.MockGetExistingFunction(response=None)
    with self.assertRaisesRegex(
        exceptions.OversizedDeployment,
        (r'Uncompressed deployment is \d+B, bigger than maximum allowed '
         r'size of \d+B')):
      self.Run('functions deploy my-test --trigger-http '
               '--source {} --quiet --runtime=nodejs6'.format(path))

    self.AssertErrNotContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testPackageFilesWithNoIgnorefile(self):  # Happypath use case.
    path = self.PrepareLocalSource(
        write_extra_files=False)

    function = self._MockBasicFunctionCreate()

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source {} --quiet --runtime=nodejs6'.format(path))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testPackageWithInvalidFiles(self):
    path = self.PrepareLocalSource()
    self.RemoveIgnoreFile(path)
    self.MockGetExistingFunction(response=None)
    self.StartObjectPatch(files, 'GetTreeSizeBytes', side_effect=OSError(
        'No such file or directory: foo'))
    with self.assertRaisesRegex(
        exceptions.FunctionsError,
        (r'Could not validate source files: '
         r'\[No such file or directory: foo\]')):
      self.Run('functions deploy my-test --trigger-http --runtime=nodejs6 '
               '--source {} --quiet'.format(path))

    self.AssertErrNotContains(_SUCCESSFUL_DEPLOY_STDERR)


class CoreTest(DeployTestBase):
  """Test deploy workflow with various --source and general argument options."""

  @parameterized.parameters({
      'staging_bucket_flag': '--stage-bucket {}'.format(_TEST_GS_BUCKET)
  }, {
      'staging_bucket_flag': ''
  })
  def testLocalSource(self, staging_bucket_flag):
    path = self.PrepareLocalSource()
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    if staging_bucket_flag:
      self.MockUploadToGCSBucket()
    else:
      self.MockGeneratedApiUploadUrl()
      self.MockUploadToSignedUrl()

    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_upload_url=None if staging_bucket_flag else 'foo',
        source_archive=_TEST_GS_BUCKET if staging_bucket_flag else None,
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source {source} {bucket} --quiet --runtime=nodejs6'
                      .format(source=path, bucket=staging_bucket_flag))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testLocalSourceImplied(self):
    path = self.PrepareLocalSource()
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self.MockGeneratedApiUploadUrl()
    self.MockUploadToSignedUrl()

    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_upload_url='foo',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    with files.ChDir(path):
      result = self.Run(
          'functions deploy my-test --trigger-http --quiet --runtime=nodejs6')
      self.assertEqual(result, function)
      self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testGcsSource(self):
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source gs://my-bucket/function.zip --quiet '
                      '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testGcsSourceWithoutExtensionWarns(self):
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_archive='gs://my-bucket/',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source gs://my-bucket/ --quiet --runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(
        '[gs://my-bucket/] does not end with extension `.zip`')
    # Users may have .zip archives with unusual names, and we don't want to
    # prevent those from being deployed; the deployment should go through
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testCodeRepositorySource(self):
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_repository_url=('https://source.developers.google.com/'
                               'projects/my-project/repos/my-repo/'
                               'fixed-aliases/rc0.0.9'),
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run(
        'functions deploy my-test --trigger-http '
        '--source https://source.developers.google.com/projects/my-project/'
        'repos/my-repo/fixed-aliases/rc0.0.9 '
        '--quiet --runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testLocalSourceFailsOnPathDoesNotExist(self):
    self.MockGetExistingFunction(response=None)
    with self.assertRaisesRegex(
        exceptions.FunctionsError,
        'argument `--source`: Provided directory does not exist'):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck '
          '--source my/functions/directory --quiet --runtime=nodejs6')

  def testWithAllValidOptionalArgs(self):  # Including Retry and Labels
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    trigger = self.GetPubSubTrigger(self.Project(), 'topic', True)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        memory=512,
        entry_point='foo',
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)
    result = self.Run(
        'functions deploy my-test --trigger-topic topic --runtime=nodejs6 '
        '--entry-point foo --region {} --memory 512MB  --retry '
        '--source gs://my-bucket/function.zip --quiet'.format(_DEFAULT_REGION))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testValidLabels(self):
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    labels = self.GetLabelsMessage([('fizz', 'buzz'), ('foo', 'bar')])
    trigger = self.GetPubSubTrigger(self.Project(), 'topic', False)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        labels=labels,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)
    result = self.Run('functions deploy my-test --trigger-topic topic '
                      '--update-labels=foo=bar,fizz=buzz '
                      '--source gs://my-bucket/function.zip --quiet '
                      '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  @parameterized.parameters(['deployment-tool=foobar'])
  def testInvalidLabelsRaisesError(self, labels):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        r'Invalid value for \[--update-labels\]: Label keys starting with '
        r'`deployment` are reserved for use by deployment tools and cannot '
        r'be specified manually.'):
      self.Run('functions deploy my-test --trigger-topic topic '
               '--runtime=nodejs6 '
               "--update-labels='{}' "
               '--source gs://my-bucket/function.zip --quiet'.format(labels))
    self.AssertErrNotContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testFailedUploadToUrlRaisesError(self):
    path = self.PrepareLocalSource()
    self.MockGetExistingFunction(response=None)
    self.MockGeneratedApiUploadUrl()
    self.MockUploadToSignedUrl(status_code=400)

    with self.assertRaisesRegex(
        exceptions.FunctionsError,
        r'Failed to upload the function source code to signed url: '
        r'foo. Status: \[400:\]'):
      self.Run('functions deploy my-test --trigger-http --runtime=nodejs6 '
               '--source {source} --quiet'.format(source=path))
    self.AssertErrNotContains(_SUCCESSFUL_DEPLOY_STDERR)


class TriggerTests(DeployTestBase):
  """Test various deploy trigger scenarios."""

  def testNoTriggerFails(self):
    self.MockGetExistingFunction(response=None)

    with self.assertRaisesRegex(
        calliope_exceptions.OneOfArgumentsRequiredException,
        'You must specify a trigger when deploying a new function.'):
      self.Run('functions deploy my-test '
               '--stage-bucket buck '
               '--retry '
               '--quiet '
               '--runtime=nodejs6')

  @parameterized.parameters([
      '--trigger-http --trigger-topic topic',
      '--trigger-bucket gs://foo --trigger-topic topic',
      '--trigger-bucket gs://foo --trigger-http'
  ])
  def testMultipleTriggersFails(self, triggers):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'At most one of --trigger-bucket | --trigger-http | '
        r'--trigger-provider | --trigger-topic may be specified.'):
      self.Run('functions deploy my-test {} '
               '--stage-bucket buck '
               '--retry '
               '--quiet '
               '--runtime=nodejs6'.format(triggers))

  def testWithHttpTriggerAndRetryFails(self):
    with self.assertRaisesRegex(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --trigger-http, --retry'):
      self.Run('functions deploy my-test '
               '--trigger-http '
               '--stage-bucket buck '
               '--retry '
               '--quiet '
               '--runtime=nodejs6')

  @parameterized.parameters(
      {'trigger_event': 'providers/cloud.pubsub/eventTypes/topic.publish',
       'trigger_resource': 'topic',
       'trigger': 'pubsub'},
      {'trigger_event': 'providers/cloud.storage/eventTypes/object.change',
       'trigger_resource': 'fake_bucket',
       'trigger': 'gcs'}
  )
  def testWithTriggerEventArgsStillWorks(self,
                                         trigger_event,
                                         trigger_resource,
                                         trigger):
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    if trigger == 'pubsub':
      trigger = self.GetPubSubTrigger(self.Project(), 'topic', False,
                                      trigger_type='pubsub_legacy')
    else:
      trigger = self.GetGcsTrigger(self.Project(), 'fake_bucket', retry=False,
                                   event_type='gcs_legacy')

    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)

    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)
    result = self.Run(
        'functions deploy my-test --runtime=nodejs6 '
        '--trigger-event {event} '
        '--trigger-resource {resource} '
        '--source gs://my-bucket/function.zip --quiet'.format(
            event=trigger_event, resource=trigger_resource))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testPubSubTriggerWithDefaultBehavior(self):
    self.MockGetExistingFunction(response=None)

    location = self.GetLocationResource()
    trigger = self.GetPubSubTrigger(self.Project(), 'topic', retry=True)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run('functions deploy my-test --trigger-topic topic --retry '
                      '--source gs://my-bucket/function.zip --quiet '
                      '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testGcsTriggerWithDefaultTriggerEvent(self):
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    trigger = self.GetGcsTrigger(self.Project(), 'fake_bucket', retry=False)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run(
        'functions deploy my-test --trigger-bucket {} --runtime=nodejs6 '
        '--source gs://my-bucket/function.zip --quiet'.format(_TEST_GS_BUCKET))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testGcsTriggerWithFullyQualifiedBucketUrl(self):
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    trigger = self.GetGcsTrigger(self.Project(), 'full-images', retry=False)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run(
        'functions deploy my-test --trigger-bucket {} --runtime=nodejs6 '
        '--source gs://my-bucket/function.zip --quiet'.format(
            'projects/_/buckets/full-images'))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)

  def testHttpTrigger(self):
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    location = self.GetLocationResource()
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)

    result = self.Run('functions deploy my-test --trigger-http '
                      '--source gs://my-bucket/function.zip --quiet '
                      '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)


class UpdateTests(DeployTestBase):
  """Test various deploy update scenarios scenarios.

  Test updating of:
  Nothing
  Labels
    Add
    Remove
    Clear
  Runtime config
    Memory
    Retry
    Entry point
    Timeout

  """

  def testNoUpdatePrintsStatus(self):
    """Test update with no valid values prints to stderr."""
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_source_archive_url = 'gs://bucket'
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=original_source_archive_url,
        runtime='nodejs6'
    )
    self.MockGetExistingFunction(response=original_function)
    self.Run('functions deploy my-test')
    self.AssertErrEquals(_NO_UPDATE_STDERR)

  @parameterized.parameters(
      # Test Memory Update
      {'memory': 1024, 'retry': None, 'entry_point': None, 'timeout': None},
      # Test retry Update
      {'memory': None, 'retry': True, 'entry_point': None, 'timeout': None},
      # Test entrypoint Update
      {'memory': None, 'retry': None, 'entry_point': 'foobar', 'timeout': None},
      # Test timeout Update
      {'memory': None, 'retry': None, 'entry_point': None, 'timeout': '200s'},
      # Test All Fields Update, add retry
      {'memory': 1024, 'retry': True,
       'entry_point': 'foobar', 'timeout': '200s'},
      # Test All Fields Update, remove retry
      {'memory': 1024, 'retry': False,
       'entry_point': 'foobar', 'timeout': '200s'}
  )
  def testUpdateMetaData(self, memory, retry, entry_point, timeout):
    """Test update of memory, retry, entry-point and timeout."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    update_mask = []
    update_lst = []

    # Handle Retry Update
    if retry is None:
      original_trigger = self.GetPubSubTrigger(self.Project(), 'topic')
      new_trigger = original_trigger
    elif retry:
      original_trigger = self.GetPubSubTrigger(self.Project(), 'topic')
      new_trigger = self.GetPubSubTrigger(self.Project(), 'topic', True)
      update_mask.append('eventTrigger.failurePolicy')
      update_lst.append('--retry')
    else:
      original_trigger = self.GetPubSubTrigger(self.Project(), 'topic', True)
      new_trigger = self.GetPubSubTrigger(self.Project(), 'topic', False)

    if entry_point:
      update_mask.append('entryPoint')
      update_lst.append('--entry-point {}'.format(entry_point))

    if memory:
      update_mask.append('availableMemoryMb')
      update_lst.append('--memory {}'.format(memory))

    if timeout:
      update_mask.append('timeout')
      update_lst.append('--timeout {}'.format(timeout))

    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=original_trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=new_trigger,
        source_archive=source_archive_url,
        memory=memory,
        timeout=timeout,
        entry_point=entry_point,
        runtime='nodejs6'
    )
    update_mask.append('runtime')

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask=','.join(sorted(update_mask)),
    )

    self.Run('functions deploy my-test {} --runtime=nodejs6'
             .format(' '.join(update_lst)))

  def testAddLabels(self):
    """Test adding labels to function with no labels."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )

    updated_labels = self.GetLabelsMessage([
        ('foo', 'baz'),
        ('boo', 'add_me'),
    ])
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=updated_labels,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels',
    )
    self.Run('functions deploy my-test '
             '--update-labels foo=baz,boo=add_me')

  def testUpdateLabels(self):
    """Test updating labels of function with labels."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_labels = self.GetLabelsMessage([
        ('foo', 'old'),
        ('bar', 'keep me'),
    ])
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=original_labels,
        runtime='nodejs6'
    )

    updated_labels = self.GetLabelsMessage([
        ('bar', 'newvalue'),
        ('foo', 'baz'),
        ('boo', 'add_me'),
    ])
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=updated_labels,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels,runtime',
    )
    self.Run('functions deploy my-test --runtime=nodejs6 '
             '--update-labels foo=baz,boo=add_me,bar=newvalue')

  def testRemoveLabels(self):
    """Test removing specific labels only."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_labels = self.GetLabelsMessage([
        ('foo', 'baz'),
        ('bar', 'keep me'),
        ('boo', 'remove me'),
    ])
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=original_labels,
        runtime='nodejs6'
    )

    updated_labels = self.GetLabelsMessage([
        ('bar', 'keep me'),
        ('foo', 'baz'),
    ])
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=updated_labels,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels,runtime',
    )
    self.Run('functions deploy my-test '
             '--remove-labels boo --runtime=nodejs6')

  def testClearLabels(self):
    """Test removing all labels."""
    #  --remove-labels boo,moo
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_labels = self.GetLabelsMessage([
        ('foo', 'everything'),
        ('bar', 'must'),
        ('boo', 'go'),
    ])
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=original_labels,
        runtime='nodejs6'
    )

    updated_labels = self.GetLabelsMessage()
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        labels=updated_labels,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels,runtime',
    )
    self.Run('functions deploy my-test '
             '--clear-labels --runtime=nodejs6')

  def testLocalSourceExplicit(self):
    """Test update local source with --source arg."""
    path = self.PrepareLocalSource()
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_source_archive_url = 'gs://bucket'
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=original_source_archive_url,
        runtime='nodejs6'
    )

    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_upload_url='foo',
        runtime='nodejs6'
    )
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        expect_get_upload_url=True,
        update_mask='runtime,sourceUploadUrl',
    )
    self.MockUploadToSignedUrl()
    self.Run('functions deploy my-test --source {} --runtime=nodejs6'
             .format(path))

  @parameterized.parameters(['', '--source .'])
  def testLocalSourceCwd(self, source_flag):
    """Test update from local source with --source='.' or missing."""
    path = self.PrepareLocalSource()
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_upload_url='foo',
        runtime='nodejs6'
    )

    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_upload_url='foo',
        runtime='nodejs6'
    )
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        expect_get_upload_url=True,
        update_mask='runtime,sourceUploadUrl',
    )
    self.MockUploadToSignedUrl()
    with files.ChDir(path):
      self.Run('functions deploy my-test {} --runtime=nodejs6'
               .format(source_flag))

  def testImpliedLocalSourceForRepoAndGcsPrintsToStdErr(self):
    """Test update from local source with no source flag for GCS and CSR."""
    path = self.PrepareLocalSource()
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_source_archive_url = 'gs://bucket'
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=original_source_archive_url
    )
    self.MockGetExistingFunction(response=original_function)
    with files.ChDir(path):
      self.Run('functions deploy my-test')
      self.AssertErrEquals(_NO_UPDATE_STDERR)

  def testUpdateTopicForPubSubFunction(self):
    """Test update of topic for a pubsub based function."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    old_topic_trigger = self.GetPubSubTrigger(self.Project(), 'old-topic')
    new_topic_trigger = self.GetPubSubTrigger(self.Project(), 'new-topic')
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=old_topic_trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=new_topic_trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger,httpsTrigger,runtime',
    )
    self.Run(
        'functions deploy my-test --trigger-topic new-topic --runtime=nodejs6')

  @parameterized.named_parameters(
      # Change function source from bucket in sourceArchiveUrl field to
      # repository url in sourceRepository field with --source flag.
      ('sourceArchiveUrlToRepositoryUrl',
       'sourceArchiveUrl', 'gs://bucket', 'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo',
       '--source https://source.developers.google.com/p/proj/r/repo'
      ),
      # Change function source from bucket in sourceUploadUrl field to
      # repository url in sourceRepository field with --source flag.
      ('SourceUploadUrlUrlToRepositoryUrl',
       'sourceUploadUrl', 'gs://bucket', 'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo',
       '--source https://source.developers.google.com/p/proj/r/repo'),
      # Change function source from repository url in sourceRepository to
      # bucket in sourceUploadUrl field with --source flag.
      ('RepositoryUrlToSourceArchiveUrl',
       'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo',
       'sourceArchiveUrl', 'gs://bucket',
       '--source gs://bucket'),
      # Change function source repository url in sourceRepository to
      # new in sourceRepository url  with --source flag.
      ('RepositoryUrlUpdate',
       'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo',
       'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo2',
       '--source https://source.developers.google.com/p/proj/r/repo2'),
      # Change function source bucket in sourceArchiveUrl to
      # new bucket sourceArchiveUrl with --source flag.
      ('SourceArchiveUrlUpdate',
       'sourceArchiveUrl', 'gs://bucket',
       'sourceArchiveUrl', 'gs://bucket2',
       '--source gs://bucket2'),
  )
  def testChangeSourceType(self, original_field, original_value, updated_field,
                           updated_value, source_flag):
    """Test update source from local|pubsub|storgae|repo to another."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')

    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        runtime='nodejs6'
    )

    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        runtime='nodejs6'
    )

    if original_field == 'sourceRepository':
      original_value = self.messages.SourceRepository(url=original_value)
    setattr(original_function, original_field, original_value)
    if updated_field == 'sourceRepository':
      updated_value = self.messages.SourceRepository(url=updated_value)
    setattr(updated_function, updated_field, updated_value)

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask=','.join(sorted([updated_field, 'runtime']))
    )
    self.Run('functions deploy my-test --runtime=nodejs6 {}'
             .format(source_flag))

  @parameterized.named_parameters(
      # Change function trigger from https to pubsub topic
      ('HttpsToPubsub', 'https', '', 'pubsub', 'topic', '--trigger-topic topic'
      ),
      # Change function trigger from http to gcs bucket
      ('HttpsToGcs', 'https', '', 'gcs', 'fake',
       '--trigger-bucket gs://fake'),
      # Change function trigger from pubsub to https
      ('PubSubToHttps', 'pubsub', 'topic', 'http', '', '--trigger-http'),
      # Change function trigger from pubsub to gcs
      ('PubSubToGcs', 'pubsub', 'topic', 'gcs', 'fake',
       '--trigger-bucket gs://fake'),
      # Change function trigger from gcs to https
      ('GcsToHttps', 'gcs', 'fake', 'http', '', '--trigger-http'),
      # Change function trigger from gcs to pubsub
      ('GcsToPubSub', 'gcs', 'fake', 'pubsub', 'topic',
       '--trigger-topic topic'),
  )
  def testChangeTriggerType(self, original_trigger, original_value,
                            updated_trigger, updated_value, trigger_flag):
    """Test change source type from http|gcs|pubsub to another."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')

    if original_trigger == 'pubsub':
      original_event_trigger = self.GetPubSubTrigger(self.Project(),
                                                     original_value)
      original_http_trigger = None
    elif original_trigger == 'gcs':
      original_event_trigger = self.GetGcsTrigger(self.Project(),
                                                  original_value)
      original_http_trigger = None
    else:
      original_event_trigger = None
      original_http_trigger = self.messages.HttpsTrigger()

    if updated_trigger == 'pubsub':
      updated_event_trigger = self.GetPubSubTrigger(self.Project(),
                                                    updated_value)
      update_http_trigger = None
    elif updated_trigger == 'gcs':
      updated_event_trigger = self.GetGcsTrigger(self.Project(), updated_value)
      update_http_trigger = None
    else:
      updated_event_trigger = None
      update_http_trigger = self.messages.HttpsTrigger()

    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=original_event_trigger,
        https_trigger=original_http_trigger,
        runtime='nodejs6')

    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=updated_event_trigger,
        https_trigger=update_http_trigger,
        runtime='nodejs6')

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger,httpsTrigger,runtime',
    )
    self.Run('functions deploy my-test {} --runtime=nodejs6'
             .format(trigger_flag))

  def testUpdateLegacyGcsTriggerError(self):
    """Test update of legacy trigger for a gcs based function."""
    trigger = self.GetGcsTrigger(self.Project(), 'fake_bucket', retry=False,
                                 event_type='gcs_legacy')
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    self.MockGetExistingFunction(response=function)
    with self.assertRaises(trigger_util.TriggerCompatibilityError):
      self.Run(
          'functions deploy my-test --trigger-bucket {} --runtime=nodejs6 '
          '--source gs://my-bucket/function.zip --quiet'.format(
              _TEST_GS_BUCKET))
      self.AsserErrContains(trigger_util.GCS_COMPATIBILITY_ERROR)

  def testUpdateLegacyGcsTriggerError_EventFlags(self):
    """Test update of legacy trigger for a gcs based function."""
    trigger = self.GetGcsTrigger(self.Project(), 'fake_bucket', retry=False,
                                 event_type='gcs_legacy')
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='nodejs6')
    self.MockGetExistingFunction(response=function)
    with self.assertRaises(trigger_util.TriggerCompatibilityError):
      self.Run(
          'functions deploy my-test --runtime=nodejs6 '
          '--trigger-event google.storage.object.finalize '
          '--trigger-resource {resource} '
          '--source gs://my-bucket/function.zip --quiet'.format(
              resource=_TEST_GS_BUCKET))
      self.AsserErrContains(trigger_util.GCS_COMPATIBILITY_ERROR)

  def testUpdateLegacyPubSubTriggerError(self):
    """Test update of legacy trigger for a pubsub based function."""
    source_archive_url = 'gs://bucket'
    topic_trigger = self.GetPubSubTrigger(self.Project(), 'new-topic',
                                          trigger_type='pubsub_legacy')
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=topic_trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )
    self.MockGetExistingFunction(response=original_function)
    with self.assertRaises(trigger_util.TriggerCompatibilityError):
      self.Run(
          'functions deploy my-test --trigger-topic new-topic --runtime=nodejs6'
          )
      self.AssertErrorContains(trigger_util.PUBSUB_COMPATIBILITY_ERROR)

  def testUpdateLegacyPubSubTriggerError_EventFlags(self):
    """Test update of legacy trigger for a pubsub based function."""
    source_archive_url = 'gs://bucket'
    topic_trigger = self.GetPubSubTrigger(self.Project(), 'new-topic',
                                          trigger_type='pubsub_legacy')
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=topic_trigger,
        source_archive=source_archive_url,
        runtime='nodejs6'
    )
    self.MockGetExistingFunction(response=original_function)
    with self.assertRaises(trigger_util.TriggerCompatibilityError):
      self.Run(
          'functions deploy my-test --runtime=nodejs6 '
          '--trigger-event google.pubsub.topic.publish '
          '--trigger-resource topic '
          '--source gs://my-bucket/function.zip --quiet')
      self.AssertErrorContains(trigger_util.PUBSUB_COMPATIBILITY_ERROR)

  def testUpdateDeploymentLabelFails(self):
    """Test that updating deployment label raises exception."""
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Label keys starting with `deployment` are reserved for use by '
        'deployment tools and cannot be specified manually.'):
      self.Run(
          'functions deploy my-test --update-labels=deployment=contingency '
          '--runtime=nodejs6')

  def testRemoveDeploymentLabelFails(self):
    """Test that removing deployment label raises exception."""
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Label keys starting with `deployment` are reserved for use by '
        'deployment tools and cannot be specified manually.'):
      self.Run(
          'functions deploy my-test --remove-labels=deployment '
          '--runtime=nodejs6')


class DeployRuntimeTests(DeployTestBase):

  def testUpdateRuntime(self):
    """Test update of runtime."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'

    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        source_archive=source_archive_url,
        runtime='nodejs6')
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        source_archive=source_archive_url,
        runtime='python37')

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='runtime'
    )

    self.Run('functions deploy my-test --runtime python37')

  def testCreateRuntime(self):
    self.MockGetExistingFunction(response=None)
    location = self.GetLocationResource()
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive='gs://my-bucket/function.zip',
        runtime='python37')
    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockLongRunningOpResult('operations/operation')
    self.MockGetExistingFunction(response=function)
    result = self.Run(
        'functions deploy my-test --trigger-topic topic '
        '--region {} --source gs://my-bucket/function.zip '
        '--runtime python37 --quiet'.format(_DEFAULT_REGION))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESSFUL_DEPLOY_STDERR)


class EnvVarsTests(DeployTestBase):
  """Test various scenarios of setting and updating environment variables.

  Scenario:
    New function
    Existing function with no environment variables
    Existing function with environment variables

  Flag:
    --set-env-vars
    --update-env-vars
    --add-env-vars
    --remove-env-vars
    --clear-env-vars
    --env-vars-file
  """

  _ENV_VARS_TYPE_CLASS = api_util.GetApiMessagesModule(
  ).CloudFunction.EnvironmentVariablesValue

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  @parameterized.named_parameters(
      (
          'Set env vars new function',
          {'FOO': 'bar', 'BAZ': 'boo'},
          '--set-env-vars FOO=bar,BAZ=boo'
      ),
      (
          'Update env vars new function',
          {'FOO': 'bar', 'BAZ': 'boo'},
          '--update-env-vars FOO=bar,BAZ=boo'
      )
  )
  def testEnvVarsFlagsNewFunction(self, env_vars, flags):
    """Test adding env vars to functions with no env vars with different flags.

    Args:
      env_vars: A dict of environment variables.
      flags: A string containing the flags for setting environment variables.
    """
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(False)

    source_archive_url = 'gs://bucket'
    location = self.GetLocationResource()

    env_vars_message = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, env_vars)
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_archive=source_archive_url,
        env_vars=env_vars_message,
        runtime='nodejs6'
    )

    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockUploadToSignedUrl()
    self.MockGetExistingFunction(response=function)

    self.Run('functions deploy my-test --trigger-http --source gs://bucket '
             '{} --runtime=nodejs6'.format(flags))

  @parameterized.named_parameters(
      (
          'Set env vars existing function with no env vars',
          None,
          {'FOO': 'bar', 'BAZ': 'boo'},
          '--set-env-vars FOO=bar,BAZ=boo'
      ),
      (
          'Set env vars existing function with env vars',
          {'FOO': 'old bar', 'OLD_BAZ': 'old boo'},
          {'FOO': 'new bar', 'NEW_BAZ': 'new boo'},
          '--set-env-vars "FOO=new bar,NEW_BAZ=new boo"'
      ),
      (
          'Clear env vars',
          {'FOO': 'bar', 'BAZ': 'boo'},
          None,
          '--clear-env-vars'
      ),
      (
          'Update env vars',
          {'FOO': 'bar', 'BAZ': 'boo'},
          {'FOO': 'bar', 'BAZ': 'bam', 'BAR': 'baa'},
          '--update-env-vars BAZ=bam,BAR=baa'
      ),
      (
          'Remove env vars',
          {'FOO': 'bar', 'BAZ': 'boo'},
          {'FOO': 'bar'},
          '--remove-env-vars BAZ,BAR'
      ),
  )
  def testEnvVarsFlagsExistingFunction(self, old_env_vars, new_env_vars, flags):
    """Test adding env vars to function with no env vars."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    original_env_vars = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, old_env_vars)
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        env_vars=original_env_vars,
        runtime='nodejs6'
    )

    updated_env_vars = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, new_env_vars)
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        env_vars=updated_env_vars,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='environmentVariables',
    )
    self.Run('functions deploy my-test {}'.format(flags))

  def testEnvVarsFileNewFunction(self):
    """Test adding env vars to function with no env vars."""
    self.MockGetExistingFunction(response=None)
    self.ExpectResourceManagerTestIamPolicyBinding(False)

    source_archive_url = 'gs://bucket'
    location = self.GetLocationResource()

    env_vars = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, {
            'BAZ': 'boo',
            'BAR': 'baa',
        })
    function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        https_trigger=self.messages.HttpsTrigger(),
        source_archive=source_archive_url,
        env_vars=env_vars,
        runtime='nodejs6'
    )

    create_request = self.GetFunctionsCreateRequest(function, location)
    operation = self._GenerateActiveOperation('operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request, operation)
    self.MockRemoveIamPolicy(_DEFAULT_FUNCTION_NAME)
    self.MockLongRunningOpResult('operations/operation')
    self.MockUploadToSignedUrl()
    self.MockGetExistingFunction(response=function)

    with mock.patch('googlecloudsdk.core.yaml.load_path') as yaml_load_path:
      yaml_load_path.return_value = {
          'BAZ': 'boo',
          'BAR': 'baa',
      }
      self.Run('functions deploy my-test --trigger-http --source gs://bucket '
               '--env-vars-file env.yaml --runtime=nodejs6')

  def testEnvVarsFileExistingFunction(self):
    """Test adding env vars to function with no env vars."""
    function_name = self.GetFunctionResource(self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')

    original_env_vars = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, {
            'FOO': 'bar',
            'BAZ': 'bee',
        })
    original_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        env_vars=original_env_vars,
        runtime='nodejs6'
    )

    updated_env_vars = env_vars_api_util.DictToEnvVarsProperty(
        self._ENV_VARS_TYPE_CLASS, {
            'BAZ': 'boo',
            'BAR': 'baa',
        })
    updated_function = self.GetFunctionMessage(
        _DEFAULT_REGION,
        _DEFAULT_FUNCTION_NAME,
        event_trigger=trigger,
        source_archive=source_archive_url,
        env_vars=updated_env_vars,
        runtime='nodejs6'
    )

    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='environmentVariables',
    )

    with mock.patch('googlecloudsdk.core.yaml.load_path') as yaml_load_path:
      yaml_load_path.return_value = {
          'BAZ': 'boo',
          'BAR': 'baa',
      }
      self.Run(
          'functions deploy my-test --env-vars-file env.yaml')

  @parameterized.parameters(
      '--set-env-vars X_GOOGLE_FOO=bar',
      '--update-env-vars X_GOOGLE_FOO=bar',
      '--remove-env-vars X_GOOGLE_FOO',
  )
  def testEnvVarsFlagsFailWithInvalidKeys(self, flags):
    """Test adding env vars to function with no env vars."""

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Environment variable keys that start with `X_GOOGLE_` are reserved '
        'for use by deployment tools and cannot be specified manually.'):
      self.Run('functions deploy my-test {} --runtime=nodejs6'.format(flags))

  @parameterized.parameters(
      ({'': 'boo'}, 'Environment variable keys cannot be empty.'),
      ({'X_GOOGLE_FOO': 'boo'}, 'Environment variable keys that start with '
                                '`X_GOOGLE_` are reserved for use by deployment'
                                ' tools and cannot be specified manually.'),
      ({'FOO=BAR': 'boo'}, 'Environment variable keys cannot contain `=`.'),
  )
  def testEnvVarsFileFailsWithInvalidKeys(self, file_env_vars,
                                          expected_error_message):
    """Test adding env vars to function with no env vars."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, expected_error_message):
      with mock.patch('googlecloudsdk.core.yaml.load_path') as yaml_load_path:
        yaml_load_path.return_value = file_env_vars

        self.Run('functions deploy my-test --env-vars-file env.yaml '
                 '--runtime=nodejs6')


# TODO(b/109938541): Remove this after new non-gsutil implementation seems
# stable
class CoreTestGsutil(CoreTest):
  """Test deploy workflow with various --source and general argument options."""

  def SetUp(self):
    properties.VALUES.storage.use_gsutil.Set(True)

  def MockUploadToGCSBucket(self):
    """Mock uploading the function archive to cloud storage."""
    # Args is different ordering/length for  execution_utils.ArgsForCMDTool vs.
    # execution_utils.ArgsForExecutableTool
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
      file_arg = 4
    else:
      file_arg = 2
    def FakeExec(args, no_exit, out_func, err_func):
      """Mock implementation for execution_utils.Exec."""
      del out_func, err_func
      self.assertTrue(no_exit)
      self.AssertNodeModulesNotUploaded(args[file_arg])
      return 0

    self.StartObjectPatch(storage_util, '_GetGsutilPath', return_value='gsutil')
    self.StartObjectPatch(execution_utils, 'Exec', FakeExec)
    self.StartObjectPatch(storage_util.ObjectReference, 'ToUrl',
                          return_value=_TEST_GS_BUCKET)


if __name__ == '__main__':
  test_case.main()
