# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import http_wrapper
from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.api_lib.functions import util as functions_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions.deploy import source_util
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.functions import base
from tests.lib.surface.functions import util as testutil

import mock

_DEFAULT_FUNCTION_NAME = 'my-test'
_DEFAULT_GS_BUCKET = 'gs://buck/bucket'
_DEFAULT_LOCATION = 'us-central1'
_FILES_LIST = ['file_1', 'file_2']
_OP_FAILED_UPLOAD = (
    r'Failed to upload the function source code to the bucket gs://buck/')
_REPO_URL = 'the_string_for_the_URL_is_not_validated_in_gcloud'
_REPO_PATH = 'random/path/that/is/not/checked/either'
_SUCCESFULL_DEPLOY_STDERR = """\
{"ux": "PROGRESS_TRACKER", "message": "Deploying function (may take a while - up to 2 minutes)", "status": "SUCCESS"}
"""


class FunctionsDeployTestBase(base.FunctionsTestBase):
  # IMPORTANT: if you add a new test that deploys a function from a local
  # directory, make sure you mock MakeZipFromDir or use a dedicated directory.
  # Otherwise the function will be deployed from the CWD, which may result in
  # huge zip files being created (plus potential test timeouts and out of space
  # on /tmp).

  def _GetFakeMakeZipFromDir(self, expected_src_dir=None):
    if expected_src_dir is None:
      expected_src_dir = '.'

    def FakeMakeZipFromDir(dest_zip_file, src_dir, predicate=None):
      del dest_zip_file, predicate
      self.assertEqual(src_dir, expected_src_dir)

    return FakeMakeZipFromDir

  def GetFunctionRelativePath(self, project, location, name):
    return 'projects/{}/locations/{}/functions/{}'.format(
        project, location, name)

  def GetTopicRelativeName(self, project, name):
    return 'projects/{}/topics/{}'.format(project, name)

  def GetLocationRelativePath(self, project, location):
    return 'projects/{}/locations/{}'.format(project, location)

  def GetPubSubTrigger(self, project, topic, retry=False):
    result = self.messages.EventTrigger(
        eventType='google.pubsub.topic.publish',
        resource=self.GetTopicRelativeName(project, topic),
    )
    if retry:
      result.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry()
      )
    return result

  def GetLabels(self, labels):
    labels_value = self.messages.CloudFunction.LabelsValue
    additional_property = labels_value.AdditionalProperty
    additional_properties = [
        additional_property(key=k, value=v) for k, v in labels]
    return labels_value(additionalProperties=additional_properties)

  def GetFunction(self, project, location, name, trigger,
                  source_archive=None, source_repository_url=None,
                  source_upload_url=None, labels=None):
    if labels is None:
      labels = self.GetLabels([('deployment-tool', 'cli-gcloud')])
    if source_repository_url:
      source_repository = self.messages.SourceRepository(
          url=source_repository_url,)
    else:
      source_repository = None
    return self.messages.CloudFunction(
        name=self.GetFunctionRelativePath(project, location, name),
        sourceArchiveUrl=source_archive,
        sourceRepository=source_repository,
        sourceUploadUrl=source_upload_url,
        eventTrigger=trigger,
        labels=labels,
        runtime='nodejs6'
    )

  def GetFunctionsCreateRequest(self, function, location):
    return self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
        location=location,
        cloudFunction=function)

  def GetFunctionsGetRequest(self, project, location, name):
    return self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
        name=self.GetFunctionRelativePath(project, location, name))

  def ExpectFunctionPatch(
      self, function_name, original_function, updated_function,
      update_mask=None, expect_get_upload_url=False):
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=function_name),
        original_function)
    if expect_get_upload_url:
      self._ExpectGenerateUploadUrl()
    self.mock_client.projects_locations_functions.Patch.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsPatchRequest(
            cloudFunction=updated_function,
            name=function_name,
            updateMask=update_mask
        ),
        self._GenerateActiveOperation('operations/operation')
    )
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=updated_function.name),
        updated_function)
    return 0

  def GenerateFunctionWithPubsub(
      self, name, topic, source_archive_url=None, entry_point=None, memory=None,
      timeout=None, retry=False, project=None, labels=None,
      source_repository_url=None, source_upload_url=None):
    if project is None:
      project = self.Project()
    if labels is None:
      labels = self.GetLabels([('deployment-tool', 'cli-gcloud')])
    if source_repository_url:
      source_repository = self.messages.SourceRepository(
          url=source_repository_url,)
    else:
      source_repository = None
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=source_archive_url,
        sourceRepository=source_repository,
        sourceUploadUrl=source_upload_url,
        entryPoint=entry_point,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.pubsub.topic.publish',
            resource=self.GetTopicRelativeName(project, topic),
        ),
        labels=labels,
        runtime='nodejs6'
    )
    if memory:
      result.availableMemoryMb = memory
    if timeout:
      result.timeout = timeout
    if retry:
      result.eventTrigger.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry())
    return result

  def GenerateFunctionNoTrigger(
      self, name, source_archive_url=None, entry_point=None, memory=None,
      timeout=None, retry=False, project=None, labels=None,
      source_repository_url=None):
    if project is None:
      project = self.Project()
    if labels is None:
      labels = self.GetLabels([('deployment-tool', 'cli-gcloud')])
    if source_repository_url:
      source_repository = self.messages.SourceRepository(
          url=source_repository_url,)
    else:
      source_repository = None
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=source_archive_url,
        sourceRepository=source_repository,
        entryPoint=entry_point,
        labels=labels,
        runtime='nodejs6'
    )
    if memory:
      result.availableMemoryMb = memory
    if timeout:
      result.timeout = timeout
    if retry:
      result.eventTrigger.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry())
    return result

  def GenerateFunctionWithHttp(
      self, name, source_archive_url=None, entry_point=None, timeout=None,
      source_repository_url=None):
    https_trigger = self.messages.HttpsTrigger()
    labels = self.GetLabels([('deployment-tool', 'cli-gcloud')])
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=source_archive_url,
        httpsTrigger=https_trigger,
        entryPoint=entry_point,
        labels=labels,
        runtime='nodejs6'
    )
    if timeout:
      result.timeout = timeout
    if source_repository_url:
      result.sourceRepository = self.messages.SourceRepository(
          url=source_repository_url
      )
    return result

  def ExpectGetFunction(
      self, response=None, project=None, region=None, name=None):
    if project is None:
      project = self.Project()
    if name is None:
      name = _DEFAULT_FUNCTION_NAME
    if region is None:
      region = _DEFAULT_LOCATION
    get_request = self.GetFunctionsGetRequest(project, region, name)
    if response:
      self.mock_client.projects_locations_functions.Get.Expect(
          get_request, response)
    else:
      self.mock_client.projects_locations_functions.Get.Expect(
          get_request,
          exception=testutil.CreateTestHttpError(404, 'Not Found'))


class FunctionsDeployTest(FunctionsDeployTestBase,
                          parameterized.TestCase):

  def SetUp(self):
    self.StartObjectPatch(storage_util.ObjectReference, 'ToUrl',
                          return_value=_DEFAULT_GS_BUCKET)

  class MockZipFile(object):
    """Ensure existence of zip file the command will read.

    The command creates random tmp directory, creates 'fun.zip' file in it and
    tries to upload it. This:
    - Creates random tmp directory with 'fun.zi[' file in it.
    - Returns an object imitating temporary directory object (FakeTempDir).
    """

    class FakeTempDir(object):

      def __init__(self, d):
        self.d = d

      def __enter__(self):
        return self.d

      def __exit__(self, *arg):
        pass

    def __init__(self):
      self.tmp_dir = file_utils.TemporaryDirectory()

    def __enter__(self):
      self.tmp_dir_path = self.tmp_dir.__enter__()
      zip_file_name = os.path.join(self.tmp_dir_path, 'fun.zip')
      with open(zip_file_name, 'w+') as f:
        f.write('fun.zip')
      return FunctionsDeployTest.MockZipFile.FakeTempDir(self.tmp_dir_path)

    def __exit__(self, *args):
      self.tmp_dir.__exit__(*args)

  def ReturnOverMaxSize(self, *args, **kwargs):
    return 512 * 2**20 + 1

  def _ExpectGenerateUploadUrl(self, project=None, region=None):
    if project is None:
      project = self.Project()
    if region is None:
      region = self.GetRegion()
    self.mock_client.projects_locations_functions.GenerateUploadUrl.Expect(
        (self.messages.
         CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest)(
             parent='projects/{}/locations/{}'.format(project, region)),
        self.messages.GenerateUploadUrlResponse(uploadUrl='foo')
    )

  def _ExpectUploadToSignedUrl(self):
    def MockMakeRequest(http, request, retries=None, max_retry_wait=None,
                        redirections=None, retry_func=None,
                        check_response_func=None):
      del http, retries, max_retry_wait, redirections, retry_func
      del check_response_func
      self.assertEqual('PUT', request.http_method)
      self.assertEqual('foo', request.url)
      self.assertEqual(request.headers['Content-Length'], '7')
      self.assertEqual(request.headers['x-goog-content-length-range'],
                       '0,104857600')
      self.assertEqual(request.headers['content-type'], 'application/zip')

      return http_wrapper.Response(
          info={'status': 200, 'location': request.url}, content='',
          request_url=request.url)
    self.StartObjectPatch(http_wrapper, 'MakeRequest', MockMakeRequest)

  @parameterized.named_parameters(
      ('UsEastRegion', 'us-east1'),  # NOTICE: Neither of these are the default
      ('UsWestRegion', 'us-west1'),  # functions.region value.
  )
  def testCreateWithPubSub(self, region):
    self.MockUnpackedSourcesDirSize()
    # Mock out making archive containing the function to deploy.
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')
    self.ExpectGetFunction(region=region)

    self._ExpectGenerateUploadUrl(region=region)

    location_path = self.GetLocationRelativePath(
        self.Project(), region)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic', False)
    function = self.GetFunction(
        self.Project(), region, _DEFAULT_FUNCTION_NAME, trigger,
        source_upload_url='foo')
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), region, _DEFAULT_FUNCTION_NAME)),
        function)

    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      result = self.Run(
          'functions deploy my-test --region {} '
          '--trigger-topic topic '
          '--quiet --runtime=nodejs6'.format(region))
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testCreateWithPubSubAndRetrying(self):
    self.MockUnpackedSourcesDirSize()
    # Mock out making archive containing the function to deploy.
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')

    self.ExpectGetFunction()

    self._ExpectGenerateUploadUrl()

    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic', True)
    function = self.GetFunction(
        self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME, trigger,
        source_upload_url='foo')
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME)),
        function)

    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      result = self.Run(
          'functions deploy my-test '
          '--trigger-topic topic '
          '--retry '
          '--quiet '
          '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testCreateWithPubSubAndLabels(self):
    self.MockUnpackedSourcesDirSize()
    # Mock out making archive containing the function to deploy.
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')

    self.ExpectGetFunction()

    self._ExpectGenerateUploadUrl()

    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    labels = self.GetLabels([
        ('boo', 'baz'), ('deployment-tool', 'cli-gcloud'), ('foo', 'bar')])
    function = self.GetFunction(
        self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME, trigger,
        None, labels=labels, source_upload_url='foo')
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME)),
        function)

    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      result = self.Run(
          'functions deploy my-test '
          '--trigger-topic topic '
          '--update-labels=foo=bar,boo=baz '
          '--quiet '
          '--runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testDeployFromLocalDirWithSourceFlag(self):
    # Mock out making archive containing the function to deploy.
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')
    # This mocks the validation that --source is a directory. Originally
    # these tests were mocking os.path, so this is a slight improvement.
    self.StartObjectPatch(
        functions_util,
        'ValidateDirectoryExistsOrRaiseFunctionError',
        lambda directory: directory)
    self.MockUnpackedSourcesDirSize()
    # Mock out making archive containing the function to deploy.
    self.StartObjectPatch(
        archive, 'MakeZipFromDir',
        self._GetFakeMakeZipFromDir(expected_src_dir='my/functions/directory'))

    self.ExpectGetFunction()

    self._ExpectGenerateUploadUrl()
    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    function = self.GetFunction(
        self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME, trigger,
        source_upload_url='foo')
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME)),
        function)

    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      result = self.Run(
          'functions deploy my-test --trigger-topic topic '
          '--source my/functions/directory --quiet --runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testDeployFromLocalSource_failIfPathDoesNotExist(self):
    self.ExpectGetFunction()

    with self.assertRaisesRegex(
        exceptions.FunctionsError,
        'argument `--source`: Provided directory does not exist'):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck '
          '--source my/functions/directory --quiet --runtime=nodejs6')

  def testDeployFromGcsWithSourceFlag(self):
    self.MockUnpackedSourcesDirSize()
    self.ExpectGetFunction()

    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    function = self.GetFunction(
        self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME, trigger,
        'gs://my-bucket/function.zip')
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME)),
        function)

    result = self.Run(
        'functions deploy my-test --trigger-topic topic '
        '--source gs://my-bucket/function.zip --quiet --runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testDeployFromRepoWithSourceFlag(self):
    self.MockUnpackedSourcesDirSize()
    self.ExpectGetFunction()

    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    trigger = self.GetPubSubTrigger(self.Project(), 'topic')
    function = self.GetFunction(
        self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME, trigger,
        source_repository_url=('https://source.developers.google.com/'
                               'projects/my-project/repos/my-repo/'
                               'fixed-aliases/rc0.0.9'))
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)

    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))

    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=self.GetFunctionRelativePath(
                self.Project(), _DEFAULT_LOCATION, _DEFAULT_FUNCTION_NAME)),
        function)

    result = self.Run(
        'functions deploy my-test --trigger-topic topic '
        '--source '
        'https://source.developers.google.com/projects/my-project/'
        'repos/my-repo/fixed-aliases/rc0.0.9 '
        '--quiet --runtime=nodejs6')
    self.assertEqual(result, function)
    self.AssertErrContains(_SUCCESFULL_DEPLOY_STDERR)

  def testHttpTriggerAndRetrying(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(
        calliope_exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --trigger-http, --retry'):
      self.Run(
          'functions deploy my-test '
          '--trigger-http '
          '--stage-bucket buck '
          '--retry '
          '--quiet '
          '--runtime=nodejs6')

  def testUpdateTopic(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    old_topic = 'old-topic'
    new_topic = 'new-topic'
    original_function = self.GenerateFunctionWithPubsub(
        function_name, old_topic, source_archive_url=source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, new_topic, source_archive_url=source_archive_url)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger,httpsTrigger',
    )
    self.Run('functions deploy my-test --trigger-topic new-topic')

  def testUpdate_withMemoryLimitGb(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        memory=1024)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='availableMemoryMb',
    )
    self.Run('functions deploy my-test --memory 1GB')

  def testUpdate_withMemoryLimitMb(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        memory=128)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='availableMemoryMb',
    )
    self.Run('functions deploy my-test --memory 128MB')

  def testUpdate_withMemoryLimitDefaultUnit(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        memory=512)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='availableMemoryMb',
    )
    self.Run('functions deploy my-test --memory 512')

  def testUpdate_withTimeout(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        timeout='512s')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='timeout',
    )
    self.Run('functions deploy my-test --timeout 512')

  def testUpdate_withRetry(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        retry=False)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        retry=True)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger.failurePolicy',
    )
    self.Run('functions deploy my-test --retry')

  def testUpdate_withNoRetry(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url, retry=True)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        retry=False)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger.failurePolicy',

    )
    self.Run('functions deploy my-test --no-retry')

  def testUpdate_withLabels(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_labels = self.GetLabels([
        ('foo', 'old'),
        ('boo', 'drop me'),
        ('bar', 'keep me'),
    ])
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url, retry=True,
        labels=original_labels)
    updated_labels = self.GetLabels([
        ('bar', 'keep me'),
        ('deployment-tool', 'cli-gcloud'),
        ('foo', 'baz'),
    ])
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        retry=False, labels=updated_labels)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels',
    )
    self.Run('functions deploy my-test '
             '--update-labels foo=baz --remove-labels boo,moo')

  def testUpdate_withClearLabels(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_labels = self.GetLabels([
        ('foo', 'old'),
        ('boo', 'drop me'),
    ])
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url, retry=True,
        labels=original_labels)
    updated_labels = self.GetLabels([
        ('deployment-tool', 'cli-gcloud'),
    ])
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=source_archive_url,
        retry=False, labels=updated_labels)
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='labels',
    )
    self.Run('functions deploy my-test --clear-labels')

  def testUpdate_withLocalSource(self):
    self.MockUnpackedSourcesDirSize()
    self.StartObjectPatch(
        archive, 'MakeZipFromDir', self._GetFakeMakeZipFromDir())

    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=original_source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_upload_url='foo')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='sourceUploadUrl',
        expect_get_upload_url=True,
    )
    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      self.Run('functions deploy my-test --source .')

  def testUpdate_withLocalSourceExplicit(self):
    self.MockUnpackedSourcesDirSize()

    zip_name = 'zippy_mczipface.zip'
    self.StartObjectPatch(
        archive, 'MakeZipFromDir', self._GetFakeMakeZipFromDir())
    self.StartObjectPatch(
        source_util, '_GenerateRemoteZipFileName', lambda a: zip_name)

    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_source_archive_url = 'gs://bucket'
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_archive_url=original_source_archive_url)
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, topic, source_upload_url='foo')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        expect_get_upload_url=True,
        update_mask='sourceUploadUrl',
    )
    self._ExpectUploadToSignedUrl()
    with FunctionsDeployTest.MockZipFile() as mock_zip:
      self.StartObjectPatch(
          file_utils, 'TemporaryDirectory', return_value=mock_zip)
      self.Run('functions deploy my-test --source .')

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
      # Change function source from epository url in sourceRepository to
      # bucket in sourceUploadUrl field with --source flag.
      ('RepositoryUrlToSourceArchiveUrl',
       'sourceRepository',
       'https://source.developers.google.com/p/proj/r/repo',
       'sourceArchiveUrl', 'gs://bucket',
       '--source gs://bucket'),
  )
  def testUpdate_changeSourceLocationType(
      self, original_field, original_value, updated_field, updated_value,
      source_flag):
    self.MockUnpackedSourcesDirSize()

    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    topic = self.GetTopicRelativeName(self.Project(), 'topic')
    original_function = self.GenerateFunctionWithPubsub(function_name, topic)
    updated_function = self.GenerateFunctionWithPubsub(function_name, topic)
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
        update_mask=updated_field,
    )
    self.Run('functions deploy my-test {}'.format(source_flag))

  def testDeployAddMasterTag(self):
    self.MockUnpackedSourcesDirSize()
    self.ExpectGetFunction()

    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    location_path = self.GetLocationRelativePath(
        self.Project(), _DEFAULT_LOCATION)
    function = self.GenerateFunctionWithHttp(
        function_name,
        source_repository_url=(
            'https://source.developers.google.com/projects/p/repos/r/'
            'moveable-aliases/master'),
    )
    create_request = self.GetFunctionsCreateRequest(function, location_path)
    operation = self.messages.Operation(name='operations/operation')
    self.mock_client.projects_locations_functions.Create.Expect(
        create_request,
        operation)
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))
    self.ExpectGetFunction(response=function)

    self.Run(
        'functions deploy my-test '
        '--source  https://source.developers.google.com/projects/p/repos/r '
        '--trigger-http --runtime=nodejs6')

  def testUpdate_ImplicitKeepHttpTrigger(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com')
    updated_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com', timeout='512s')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='timeout',
    )
    self.Run(
        'functions deploy my-test --timeout 512')

  def testUpdate_HttpTriggerToTopicTrigger(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com')
    updated_function = self.GenerateFunctionWithPubsub(
        function_name, 'foo', timeout='512s',
        source_archive_url='http://example.com')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger,httpsTrigger,timeout',
    )
    self.Run('functions deploy my-test --timeout 512 --trigger-topic foo')

  def testUpdate_TopicTriggerToHttpTrigger(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_function = self.GenerateFunctionWithPubsub(
        function_name, 'foo', source_archive_url='http://example.com')
    updated_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask='eventTrigger,httpsTrigger',
    )
    self.Run('functions deploy my-test --trigger-http')

  def testUpdate_ExplicitKeepHttpTrigger(self):
    self.MockUnpackedSourcesDirSize()
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    original_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com')
    updated_function = self.GenerateFunctionWithHttp(
        function_name, 'http://example.com', timeout='512s')
    self.ExpectFunctionPatch(
        function_name=function_name,
        original_function=original_function,
        updated_function=updated_function,
        update_mask=('eventTrigger,httpsTrigger,timeout'),
    )
    self.Run('functions deploy my-test --timeout 512 --trigger-http')

  def testManuallySettingDeploymentLabel(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Label keys starting with `deployment` are reserved for use by '
        'deployment tools and cannot be specified manually.'):
      self.Run('functions deploy my-test '
               '--update-labels=deployment=contingency --runtime=nodejs6')

  def testManuallyRemovingDeploymentLabel(self):
    with self.assertRaisesRegex(
        calliope_exceptions.InvalidArgumentException,
        'Label keys starting with `deployment` are reserved for use by '
        'deployment tools and cannot be specified manually.'):
      self.Run('functions deploy my-test --remove-labels=deployment '
               '--runtime=nodejs6')

  def testCreateOversized(self):
    self.StartObjectPatch(
        file_utils, 'GetTreeSizeBytes', self.ReturnOverMaxSize)
    self.ExpectGetFunction()

    with self.assertRaisesRegex(
        exceptions.OversizedDeployment,
        r'Uncompressed deployment is \d+B, bigger than maximum allowed size of '
        r'\d+B.'):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck '
          '--quiet --runtime=nodejs6')

  def testSourceFilesAndFailedUpload(self):
    self.StartObjectPatch(
        file_utils, 'GetTreeSizeBytes', self.ReturnUnderMaxSize)
    upload_mock = self.StartObjectPatch(storage_api.StorageClient,
                                        'CopyFileToGCS')
    upload_mock.side_effect = calliope_exceptions.BadFileException
    function_name = self.GetFunctionRelativePath(
        self.Project(), self.GetRegion(), 'my-test')
    self.mock_client.projects_locations_functions.Get.Expect(
        self.GetFunctionsGetRequest(
            self.Project(), self.GetRegion(), 'my-test'),
        self.GenerateFunctionWithPubsub(
            function_name, 'old-topic', source_archive_url='url'))
    with file_utils.TemporaryDirectory() as t:
      with self.assertRaisesRegex(Exception, _OP_FAILED_UPLOAD):
        self.Run(
            'functions deploy my-test --source {0} --trigger-topic topic '
            '--stage-bucket buck --runtime=nodejs6'
            .format(t))

if __name__ == '__main__':
  test_case.main()
