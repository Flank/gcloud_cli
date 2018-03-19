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

"""Tests of the 'deploy' command.

Those tests are compact but hard to understand and modify. b/36553351 tracks
simplifying them. This doesn't look like a thing worth doing actively, instead
they get gradually replaced by tests in deploy_simplified_test.py:
- they get removed when functionality they are testing gets removed
- they get moved to 'simplified' file when test needs a modification (because of
  command changing behavior) and it doesn't look like too much trouble.
"""

from argparse import ArgumentTypeError
import functools
import os
import zipfile

from googlecloudsdk.api_lib.functions.exceptions import FunctionsError
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import archive
from tests.lib import test_case
from tests.lib.surface.functions import base
from tests.lib.surface.functions import util as testutil

import mock

FILES_LIST = ['file_1', 'file_2']
REPO_URL = 'the_string_for_the_URL_is_not_validated_in_gcloud'
REPO_PATH = 'random/path/that/is/not/checked/either'


class FunctionsDeployTestBase(base.FunctionsTestBase):
  # IMPORTANT: if you add a new test that deploys a function from a local
  # directory, make sure you mock MakeZipFromDir or use a dedicated directory.
  # Otherwise the function will be deployed from the CWD, which may result in
  # huge zip files being created (plus potential test timeouts and out of space
  # on /tmp).

  def FakeMakeZipFromDir(self, dest_zip_file, src_dir, predicate=None):
    self.assertEqual(src_dir, '.')

  def _CreateFiles(self, directory, files):
    if not os.path.exists(directory):
      os.makedirs(directory)
    for name in files:
      full_name = os.path.join(directory, name)
      f = open(full_name, 'w+')
      f.close()

  def _CheckFiles(self, zip_name, files):
    zip_file = zipfile.ZipFile(zip_name)
    self.assertEqual(zip_file.namelist().sort(), files.sort())

  def _GetDefaultLabelsMessage(self):
    return self.messages.CloudFunction.LabelsValue(
        additionalProperties=[
            self.messages.CloudFunction.LabelsValue.AdditionalProperty(
                key='deployment-tool',
                value='cli-gcloud',
            ),
        ],
    )

  def _GenerateFunctionWithPubsub(
      self, name, url, topic, entry_point=None, memory=None, timeout=None,
      retry=None, project=None):
    if project is None:
      project = self.Project()
    result = self.messages.CloudFunction(
        name=name, sourceArchiveUrl=url, entryPoint=entry_point,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.pubsub.topic.publish',
            resource='projects/{0}/topics/topic'.format(project),
        ),
        labels=self._GetDefaultLabelsMessage(),
    )
    if memory:
      result.availableMemoryMb = memory
    if timeout:
      result.timeout = timeout
    if retry:
      result.eventTrigger.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry(),
      )
    return result

  def _GenerateFunctionWithSource(self, name, repo, topic, entry_point=None):
    if repo:
      source_repository = self.messages.SourceRepository(url=repo)
    else:
      source_repository = None
    return self.messages.CloudFunction(
        name=name, sourceRepository=source_repository, entryPoint=entry_point,
        eventTrigger=self.messages.EventTrigger(
            eventType='providers/cloud.pubsub/eventTypes/topic.publish',
            resource=topic,
        ),
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithGcs(self, name, url, bucket):
    return self.messages.CloudFunction(
        name=name, sourceArchiveUrl=url,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithTimeout(self, name, url, timeout, bucket):
    return self.messages.CloudFunction(
        name=name, sourceArchiveUrl=url, timeout=timeout,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithHttp(
      self, name, url, entry_point=None, timeout=None):
    https_trigger = self.messages.HttpsTrigger()
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        httpsTrigger=https_trigger,
        entryPoint=entry_point,
        labels=self._GetDefaultLabelsMessage(),
    )
    if timeout:
      result.timeout = timeout
    return result

  def _ExpectGetOperationAndGetFunction(self, test_name):
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        self._GenerateFunctionWithPubsub(test_name, 'url', 'old-topic'))

  def _ExpectFunctionCreateWithPubsub(self, args, entry_point=None,
                                      project=None):
    if project is None:
      project = self.Project()
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        project, self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(project, self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithPubsub(
                test_name, args[-1],
                'projects/{0}/topics/topic'.format(project),
                entry_point=entry_point,
                project=project)),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithPubsubAndRepo(self, source_repository,
                                             entry_point=None):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithSource(
                test_name, source_repository,
                'projects/fake-project/topics/topic', entry_point=entry_point)),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithGcs(self, args):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithGcs(
                test_name, args[-1], 'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithTimeout(self, args):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithTimeout(
                test_name, args[-1], '30s', 'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithHttp(self, args, entry_point=None):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithHttp(
                test_name, args[-1], entry_point=entry_point)),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFailedFunctionCreate(self, args):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithPubsub(
                test_name, args[-1], 'projects/fake-project/topics/topic')),
        self._GenerateActiveOperation('operations/operation'))
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateFailedOperation('operations/operation'))
    return 0

  def _ExpectFunctionUpdate(self, original_function, updated_function):
    self.mock_client.projects_locations_functions.Update.Expect(
        original_function,
        self._GenerateActiveOperation('operations/operation'))
    self.mock_client.operations.Get.Expect(
        self.messages.CloudfunctionsOperationsGetRequest(
            name='operations/operation'),
        self._GenerateSuccessfulOperation('operations/operation'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=updated_function.name),
        updated_function)
    return 0

  def _ExpectSourceFiles(self, args):
    self._CheckFiles(args[2], FILES_LIST)
    return 1

  def _ExpectGsutilCall(self, callback):

    def FakeExec(args, no_exit, out_func, err_func):
      """Mock implementation for execution_utils.Exec."""
      del out_func, err_func

      self.assertTrue(no_exit)
      return self.callback(args)

    self.callback = callback
    self.StartObjectPatch(execution_utils, 'Exec', FakeExec)
    self.StartObjectPatch(storage_util, '_GetGsutilPath', return_value='gsutil')

  def _RunDeployFromRepoScenario(self, expected_repository, source_args):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self._ExpectFunctionCreateWithPubsubAndRepo(expected_repository)
    self.Run(
        'functions deploy my-test {0} --trigger-topic topic'.format(
            source_args))

  def _GsutilCallback(
      self, args, event_type, resource, test_name, test_location):
    # We need to know what the arguments to gsutil were to know what
    # sourceArchiveUrl to expect in the Create() call
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            cloudFunction=self.messages.CloudFunction(
                eventTrigger=self.messages.EventTrigger(
                    eventType=event_type,
                    resource=resource,
                ),
                name=test_name,
                sourceArchiveUrl=args[-1],
                labels=self._GetDefaultLabelsMessage(),
            ),
            location=test_location,),
        self._GenerateActiveOperation('operations/operation'),)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectCreateFunctionWith(self, event_type, resource):
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    test_name = test_location + '/functions/my-test'
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name,),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    def GscutilCb(args):
      return self._GsutilCallback(
          args, event_type, resource, test_name, test_location)
    self._ExpectGsutilCall(GscutilCb)

  def _ExpectCreateFunctionWithModules(self, event_type, resource):
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    test_name = test_location + '/functions/my-test'
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name,),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    def GscutilCb(args):
      return self._GsutilCallback(
          args, event_type, resource, test_name, test_location)
    self._ExpectGsutilCall(GscutilCb)


class FunctionsDeployTest(FunctionsDeployTestBase):

  def testCreateWithPubsub_andEntryPoint(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectGsutilCall(functools.partial(
        self._ExpectFunctionCreateWithPubsub, entry_point='foo_bar'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-topic topic '
             '--stage-bucket buck '
             '--entry-point foo_bar')

  def testCreateWithGcs(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectGsutilCall(self._ExpectFunctionCreateWithGcs)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test --trigger-bucket path --stage-bucket buck')

  def testCreateWithTimeout(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectGsutilCall(self._ExpectFunctionCreateWithTimeout)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test --timeout 30s --trigger-bucket path '
        '--stage-bucket buck')

  def testCreateWithHttp(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectGsutilCall(self._ExpectFunctionCreateWithHttp)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck')

  def testFailedCreate(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectGsutilCall(self._ExpectFailedFunctionCreate)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    with self.assertRaisesRegexp(Exception, base.OP_FAILED_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')

  def testFailedZip(self):
    self.MockUnpackedSourcesDirSize()
    error_message_for_zip = 'Error message for ZIP'
    def ThrowingFakeMakeZipFromDir(
        dest_zip_file, src_dir, predicate=None):
      del predicate, dest_zip_file, src_dir
      raise ValueError(error_message_for_zip)
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir', ThrowingFakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    with self.assertRaisesRegexp(
        FunctionsError,
        'Error creating a ZIP archive.*{0}'.format(error_message_for_zip)):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')

  def testCreateWithPubsub_specifyProject(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/another/locations/{}/functions/my-test'.format(
        self.GetRegion())
    self._ExpectGsutilCall(functools.partial(
        self._ExpectFunctionCreateWithPubsub, project='another'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-topic topic '
             '--stage-bucket buck --project another')

  def testDeployNoAuth(self):
    self.MockUnpackedSourcesDirSize()
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_AUTH_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')

  def testCreateExplicitRegion(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{0}/locations/asia-east1/functions/my-test'.format(
        self.Project())
    self._ExpectGsutilCall(self._ExpectFunctionCreateWithPubsub)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.SetRegion('asia-east1')
    self.Run(
        'functions deploy my-test --trigger-topic topic --stage-bucket buck '
        '--region asia-east1')


class FunctionsDeployArgumentValidationTest(FunctionsDeployTestBase):

  def testTriggerEventTriggerHttpFlagsSet(self):
    self.MockUnpackedSourcesDirSize()
    with self.AssertRaisesArgumentErrorMatches(
        'argument --trigger-http: At most one of --trigger-bucket | '
        '--trigger-http | --trigger-topic | --trigger-event --trigger-resource '
        'may be specified.'):
      self.Run(
          'functions deploy my-test --trigger-event '
          'providers/cloud.pubsub/eventTypes/topic.publish '
          '--trigger-resource topic --trigger-http --stage-bucket buck'
      )

  def testUnknownTriggerEvent(self):
    self.MockUnpackedSourcesDirSize()
    with self.AssertRaisesArgumentErrorRegexp(
        'argument --trigger-event: Invalid choice: \'asdf\'.*'):
      self.Run(
          'functions deploy my-test --trigger-event asdf '
          '--stage-bucket buck')

  def testMissingTriggerResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegexp(FunctionsError, (
        r'You must provide --trigger-resource when using '
        r'--trigger-event=providers/cloud.pubsub/eventTypes/topic.publish')):
      self.Run(
          'functions deploy my-test '
          '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
          '--stage-bucket buck')

  def testInvalidTriggerResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegexp(ArgumentTypeError, 'Invalid value.*@'):
      self.Run(
          'functions deploy my-test '
          '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
          '--trigger-resource @ --stage-bucket buck')


class FunctionsDeployTriggerTest(FunctionsDeployTestBase):

  def testTopicPublish(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.pubsub/eventTypes/topic.publish',
        resource='projects/fake-project/topics/topic')
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
        '--trigger-resource topic --stage-bucket buck')

  def testObjectChange(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.storage/eventTypes/object.change',
        resource='projects/_/buckets/bucket')
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/cloud.storage/eventTypes/object.change '
        '--trigger-resource bucket --stage-bucket buck')

  def testObjectChangeBucketManged(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.storage/eventTypes/object.change',
        resource='projects/_/buckets/bucket')
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/cloud.storage/eventTypes/object.change '
        '--trigger-resource gs://bucket/ --stage-bucket buck')


class FunctionsDeployWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testDeployNoProject(self):
    self.MockUnpackedSourcesDirSize()
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_PROJECT_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')


class FunctionsAlphaTests(FunctionsDeployTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testInvalidTriggerResourceProjectResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegexp(properties.InvalidProjectError, '@'):
      self.Run(
          'functions deploy my-test '
          '--trigger-event providers/firebase.auth/eventTypes/user.create '
          '--trigger-resource @ --stage-bucket buck')

  def testUserCreateExplicitProject(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/firebase.auth/eventTypes/user.create',
        resource='projects/asdf')
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/firebase.auth/eventTypes/user.create '
        '--trigger-resource asdf --stage-bucket buck')

  def testUserCreateExplicitProjectWithNodeModules(self):
    self.MockUnpackedSourcesDirSize()
    self._ExpectCreateFunctionWithModules(
        event_type='providers/firebase.auth/eventTypes/user.create',
        resource='projects/asdf')
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/firebase.auth/eventTypes/user.create '
        '--trigger-resource asdf --stage-bucket buck')

if __name__ == '__main__':
  test_case.main()
