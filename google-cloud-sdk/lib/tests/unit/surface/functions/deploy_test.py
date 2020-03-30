# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import functools
import os
import zipfile

from googlecloudsdk.api_lib.functions.exceptions import FunctionsError
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.exceptions import RequiredArgumentException
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import archive
from tests.lib import cli_test_base
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
        ],)

  def _MaybeExpectRemoveIamPolicyBinding(self, test_name):
    self._ExpectRemoveIamPolicyBinding(test_name, True, False)

  def _GenerateFunctionWithPubsub(self,
                                  name,
                                  url,
                                  topic,
                                  entry_point=None,
                                  memory=None,
                                  timeout=None,
                                  retry=None,
                                  project=None):
    if project is None:
      project = self.Project()
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        entryPoint=entry_point,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.pubsub.topic.publish',
            resource='projects/{0}/topics/topic'.format(project),
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )
    if memory:
      result.availableMemoryMb = memory
    if timeout:
      result.timeout = timeout
    if retry:
      result.eventTrigger.failurePolicy = self.messages.FailurePolicy(
          retry=self.messages.Retry(),)
    return result

  def _GenerateFunctionWithSource(self, name, repo, topic, entry_point=None):
    if repo:
      source_repository = self.messages.SourceRepository(url=repo)
    else:
      source_repository = None
    return self.messages.CloudFunction(
        name=name,
        sourceRepository=source_repository,
        entryPoint=entry_point,
        eventTrigger=self.messages.EventTrigger(
            eventType='providers/cloud.pubsub/eventTypes/topic.publish',
            resource=topic,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithGcs(self, name, url, bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithTimeout(self, name, url, timeout, bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        timeout=timeout,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithMaxInstances(self, name, url, max_instances, bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        maxInstances=max_instances,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithVPCConnector(self, name, url, vpc_connector, bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        vpcConnector=vpc_connector,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithServiceAccount(self, name, url, service_account,
                                          bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        serviceAccountEmail=service_account,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _GenerateFunctionWithHttp(self,
                                name,
                                url,
                                entry_point=None,
                                timeout=None):
    https_trigger = self.messages.HttpsTrigger()
    result = self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        httpsTrigger=https_trigger,
        entryPoint=entry_point,
        runtime='nodejs6',
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

  def _ExpectFunctionCreateWithPubsub(self,
                                      gcs_dest_url,
                                      entry_point=None,
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
                test_name,
                gcs_dest_url,
                'projects/{0}/topics/topic'.format(project),
                entry_point=entry_point,
                project=project)),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithPubsubAndRepo(self,
                                             source_repository,
                                             entry_point=None):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithSource(
                test_name,
                source_repository,
                'projects/fake-project/topics/topic',
                entry_point=entry_point)),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithGcs(self, gcs_dest_url):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithGcs(test_name, gcs_dest_url,
                                                        'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithTimeout(self, gcs_dest_url):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithTimeout(
                test_name, gcs_dest_url, '30s', 'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithMaxInstances(self,
                                            gcs_dest_url,
                                            max_instances=8):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithMaxInstances(
                test_name, gcs_dest_url, max_instances, 'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFunctionCreateWithClearMaxInstances(self, gcs_dest_url):
    return self._ExpectFunctionCreateWithMaxInstances(
        gcs_dest_url, max_instances=0)

  def _ExpectFunctionCreateWithVPCConnector(self, vpc_connector):

    def Callback(gcs_dest_url):
      test_name = 'projects/{}/locations/{}/functions/my-test'.format(
          self.Project(), self.GetRegion())
      test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                        self.GetRegion())
      self.mock_client.projects_locations_functions.Create.Expect(
          self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
              location=test_location,
              cloudFunction=self._GenerateFunctionWithVPCConnector(
                  test_name, gcs_dest_url, vpc_connector, 'path')),
          self._GenerateActiveOperation('operations/operation'))
      self._MaybeExpectRemoveIamPolicyBinding(test_name)
      self._ExpectGetOperationAndGetFunction(test_name)
      return 0

    return Callback

  def _ExpectFunctionCreateWithClearVPCConnector(self):
    return self._ExpectFunctionCreateWithVPCConnector('')

  def _ExpectFunctionCreateWithServiceAccount(self, gcs_dest_url):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithServiceAccount(
                test_name, gcs_dest_url, 'service-account@google.com', 'path')),
        self._GenerateActiveOperation('operations/operation'))
    self._MaybeExpectRemoveIamPolicyBinding(test_name)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectAddIamPolicyBinding(self, test_name, fail_policy_bind):
    initial_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    updated_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com', 'allUsers'])
        ],
        etag=b'someUniqueEtag',
        version=1)

    self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
        self.messages
        .CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
            resource=test_name),
        response=initial_policy)
    set_request = \
      self.messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=str(test_name),
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=updated_policy))
    if fail_policy_bind:
      self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
          set_request, exception=testutil.CreateTestHttpError(404, 'Not Found'))
    else:
      self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
          set_request, response=updated_policy)

  def _ExpectRemoveIamPolicyBinding(self, test_name, fail_policy_bind,
                                    blank_policy_first):
    initial_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com', 'allUsers'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    updated_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    if blank_policy_first:
      self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
          self.messages
          .CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
              resource=test_name),
          response=self.messages.Policy(etag=b'ACAB'))
      self.mock_client.operations.Get.Expect(
          self.messages.CloudfunctionsOperationsGetRequest(
              name='operations/operation'),
          self._GenerateActiveOperation('operations/operation'))
    self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
        self.messages
        .CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
            resource=test_name),
        response=initial_policy)
    set_request = \
      self.messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=str(test_name),
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=updated_policy))
    if fail_policy_bind:
      self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
          set_request, exception=testutil.CreateTestHttpError(404, 'Not Found'))
    else:
      self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
          set_request, response=updated_policy)

  def _ExpectFunctionCreateWithHttp(self,
                                    gcs_dest_url,
                                    entry_point=None,
                                    allow_unauthenticated=False,
                                    no_allow_unauthenticated=False,
                                    fail_policy_bind=False):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithHttp(
                test_name, gcs_dest_url, entry_point=entry_point)),
        self._GenerateActiveOperation('operations/operation'))
    if allow_unauthenticated:
      self._ExpectAddIamPolicyBinding(test_name, fail_policy_bind)
    elif no_allow_unauthenticated:
      self._ExpectRemoveIamPolicyBinding(test_name, fail_policy_bind, False)
    else:
      assert False, 'should I allow unauth'

    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectFailedFunctionCreate(self, gcs_dest_url):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    self.mock_client.projects_locations_functions.Create.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
            location=test_location,
            cloudFunction=self._GenerateFunctionWithPubsub(
                test_name, gcs_dest_url, 'projects/fake-project/topics/topic')),
        self._GenerateActiveOperation('operations/operation'))
    self._ExpectRemoveIamPolicyBinding(test_name, True, False)
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
            name=updated_function.name), updated_function)
    return 0

  def _ExpectCopyFileToGCS(self, callback):

    def FakeCopyFileToGCS(client_obj, local_path, target_obj_ref):
      del client_obj, local_path
      return self.callback(target_obj_ref.ToUrl())

    self.callback = callback
    self.StartObjectPatch(storage_api.StorageClient, 'CopyFileToGCS',
                          FakeCopyFileToGCS)

  def _RunDeployFromRepoScenario(self, expected_repository, source_args):
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self._ExpectFunctionCreateWithPubsubAndRepo(expected_repository)
    self.Run('functions deploy my-test {0} --trigger-topic topic'.format(
        source_args))

  def _CopyFileToGCSCallback(self, gcs_dest_url, event_type, resource,
                             test_name, test_location):
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
                sourceArchiveUrl=gcs_dest_url,
                labels=self._GetDefaultLabelsMessage(),
                runtime='nodejs6'),
            location=test_location,
        ),
        self._GenerateActiveOperation('operations/operation'),
    )

    self._ExpectRemoveIamPolicyBinding(test_name, True, False)
    self._ExpectGetOperationAndGetFunction(test_name)
    return 0

  def _ExpectCreateFunctionWith(self, event_type, resource):
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    test_name = test_location + '/functions/my-test'
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))

    def CopyCallback(args):
      return self._CopyFileToGCSCallback(args, event_type, resource, test_name,
                                         test_location)

    self._ExpectCopyFileToGCS(CopyCallback)

  def _ExpectCreateFunctionWithModules(self, event_type, resource):
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                      self.GetRegion())
    test_name = test_location + '/functions/my-test'
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))

    def CopyCallback(args):
      return self._CopyFileToGCSCallback(args, event_type, resource, test_name,
                                         test_location)

    self._ExpectCopyFileToGCS(CopyCallback)

  def _ExpectFunctionCreateWithIngressEgressSettings(self, ingress_settings,
                                                     egress_settings):

    def Callback(gcs_dest_url):
      test_name = 'projects/{}/locations/{}/functions/my-test'.format(
          self.Project(), self.GetRegion())
      test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                        self.GetRegion())
      self.mock_client.projects_locations_functions.Create.Expect(
          self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
              location=test_location,
              cloudFunction=self
              ._GenerateFunctionCreateWithIngressEgressSettings(
                  test_name, gcs_dest_url, 'path', ingress_settings,
                  egress_settings)),
          self._GenerateActiveOperation('operations/operation'))
      self._ExpectRemoveIamPolicyBinding(test_name, True, False)
      self._ExpectGetOperationAndGetFunction(test_name)
      return 0

    return Callback

  def _GenerateFunctionCreateWithIngressEgressSettings(self, name, url, bucket,
                                                       ingress_settings,
                                                       egress_settings):
    ingress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='ingress_settings',
        message_enum=self.messages.CloudFunction.IngressSettingsValueValuesEnum,
        custom_mappings=flags.INGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            ingress_settings)
    egress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='egress_settings',
        message_enum=self.messages.CloudFunction
        .VpcConnectorEgressSettingsValueValuesEnum,
        custom_mappings=flags.EGRESS_SETTINGS_MAPPING).GetEnumForChoice(
            egress_settings)
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        vpcConnector='my-vpc',
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
        vpcConnectorEgressSettings=egress_settings_enum,
        ingressSettings=ingress_settings_enum,
    )

  def testCreateWithIngressEgressSettings(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self._ExpectCopyFileToGCS(
        self._ExpectFunctionCreateWithIngressEgressSettings(
            ingress_settings='all', egress_settings='all'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test --vpc-connector my-vpc --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6 --ingress-settings=all '
        '--egress-settings=all')

  def testInvalidIngressSettings(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError, 'argument --ingress-settings: '
        'Invalid choice: \'all-traffic\'.'):
      self.Run('functions deploy my-test --vpc-connector my-vpc '
               '--trigger-bucket path --stage-bucket buck --runtime=nodejs6 '
               '--ingress-settings=all-traffic')

  def testInvalidEgressSettings(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError, 'argument --egress-settings: '
        'Invalid choice: \'private\'.'):
      self.Run('functions deploy my-test --vpc-connector my-vpc '
               '--trigger-bucket path --stage-bucket buck --runtime=nodejs6 '
               '--egress-settings=private')

  def testRaisesVpcConnectorRequiredIfEgressSettingsSpecified(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithHttp)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    with self.assertRaisesRegex(
        RequiredArgumentException, '.*vpc-connector.*'
        'Flag `--vpc-connector` is '
        'required for setting `egress-settings`.'):
      self.Run('functions deploy my-test '
               '--trigger-bucket path '
               '--stage-bucket buck --runtime=nodejs6 '
               '--egress-settings=private-ranges-only')


class FunctionsDeployTest(FunctionsDeployTestBase):

  def testCreateWithPubsub_andEntryPoint(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithPubsub, entry_point='foo_bar'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test --trigger-topic topic '
             '--stage-bucket buck '
             '--entry-point foo_bar --runtime=nodejs6')
    self.AssertErrContains(base.STACKDRIVER_LOG_STDERR_TEMPLATE.format(
        project=self.Project(), build_id=self.GetBuildId()))

  def testCreateWithGcs(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithGcs)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --trigger-bucket path --stage-bucket buck '
        '--runtime=nodejs6')
    self.AssertErrContains(base.STACKDRIVER_LOG_STDERR_TEMPLATE.format(
        project=self.Project(), build_id=self.GetBuildId()))

  def testCreateWithServiceAccount(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithServiceAccount)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --service-account service-account@google.com '
        '--trigger-bucket path --stage-bucket buck --runtime=nodejs6')

  def testCreateWithTimeout(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithTimeout)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test --timeout 30s --trigger-bucket path '
             '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithHttp(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, no_allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6')
    self.AssertErrContains(base.STACKDRIVER_LOG_STDERR_TEMPLATE.format(
        project=self.Project(), build_id=self.GetBuildId()))

  def testFailedCreate(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFailedFunctionCreate)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    with self.assertRaisesRegex(Exception, base.OP_FAILED_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck '
          '--runtime=nodejs6')

  def testFailedZip(self):
    self.MockUnpackedSourcesDirSize()
    error_message_for_zip = 'Error message for ZIP'

    def ThrowingFakeMakeZipFromDir(dest_zip_file, src_dir, predicate=None):
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
    with self.assertRaisesRegex(
        FunctionsError,
        'Error creating a ZIP archive.*{0}'.format(error_message_for_zip)):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck '
          '--runtime=nodejs6')

  def testCreateWithPubsub_specifyProject(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/another/locations/{}/functions/my-test'.format(
        self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithPubsub, project='another'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False, project='another')
    self.Run('functions deploy my-test --trigger-topic topic '
             '--stage-bucket buck --project another --runtime=nodejs6')

  def testDeployNoAuth(self):
    self.MockUnpackedSourcesDirSize()
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_AUTH_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')

  def testCreateExplicitRegion(self):
    self.SetRegion('asia-east1')
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithPubsub)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --trigger-topic topic --stage-bucket buck '
        '--region {} --runtime=nodejs6'.format(self.GetRegion()))

  def testCreateWithMaxInstances(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithMaxInstances)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test --max-instances 8 --trigger-bucket path '
             '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithClearMaxInstances(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())

    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithClearMaxInstances)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --clear-max-instances --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithVPCConnector(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        self._ExpectFunctionCreateWithVPCConnector('avpc'))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --vpc-connector avpc --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithClearVPCConnector(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithClearVPCConnector())
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --clear-vpc-connector --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithEmptyVPCConnector(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithVPCConnector(None))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test --vpc-connector "" --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')


class FunctionsDeployArgumentValidationTest(FunctionsDeployTestBase):

  def testTriggerEventTriggerHttpFlagsSet(self):
    self.MockUnpackedSourcesDirSize()
    with self.AssertRaisesArgumentErrorMatches(
        'argument --trigger-http: At most one of --trigger-bucket | '
        '--trigger-http | --trigger-topic | --trigger-event --trigger-resource '
        'may be specified.'):
      self.Run('functions deploy my-test --trigger-event '
               'providers/cloud.pubsub/eventTypes/topic.publish '
               '--trigger-resource topic --trigger-http --stage-bucket buck')

  def testMissingTriggerResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(
        FunctionsError,
        (r'You must provide --trigger-resource when using '
         r'--trigger-event=providers/cloud.pubsub/eventTypes/topic.publish')):
      self.Run(
          'functions deploy my-test '
          '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
          '--stage-bucket buck')

  def testInvalidTriggerResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(argparse.ArgumentTypeError, 'Invalid value.*@'):
      self.Run(
          'functions deploy my-test '
          '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
          '--trigger-resource @ --stage-bucket buck')

  def testWarningMessageRuntimeNotPresent(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(self._ExpectFunctionCreateWithHttp)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    with self.assertRaisesRegex(RequiredArgumentException, '.*--runtime.*'):
      self.Run('functions deploy my-test --trigger-http --stage-bucket buck')

  def testWarningMessageRuntimeDeprecated(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, no_allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test '
             '--trigger-http --stage-bucket buck --runtime=nodejs6')
    self.AssertErrContains('deprecated')


class FunctionsDeployTriggerTest(FunctionsDeployTestBase):

  def testTopicPublish(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.pubsub/eventTypes/topic.publish',
        resource='projects/fake-project/topics/topic')
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test '
             '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
             '--trigger-resource topic --stage-bucket buck --runtime=nodejs6')

  def testObjectChange(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.storage/eventTypes/object.change',
        resource='projects/_/buckets/bucket')
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test '
             '--trigger-event providers/cloud.storage/eventTypes/object.change '
             '--trigger-resource bucket --stage-bucket buck --runtime=nodejs6')

  def testObjectChangeBucketManged(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/cloud.storage/eventTypes/object.change',
        resource='projects/_/buckets/bucket')
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run(
        'functions deploy my-test '
        '--trigger-event providers/cloud.storage/eventTypes/object.change '
        '--trigger-resource gs://bucket/ --stage-bucket buck --runtime=nodejs6')


class FunctionsDeployWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testDeployNoProject(self):
    self.MockUnpackedSourcesDirSize()
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegex(Exception, base.NO_PROJECT_RESOURCE_ARG_REGEXP):
      self.Run(
          'functions deploy my-test --trigger-topic topic --stage-bucket buck')


class FunctionsBetaTests(FunctionsDeployTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateWithHttpAllowUnauth(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6 --allow-unauthenticated')

  def testCreateWithHttpAllowUnauthFailBindPolicy(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp,
            allow_unauthenticated=True,
            fail_policy_bind=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6 --allow-unauthenticated')
    self.AssertErrContains(
        'WARNING: Setting IAM policy failed, try "gcloud alpha functions '
        'add-iam-policy-binding my-test')

  def testCreateWithPromptedAllowUnauthAtPrompt(self):
    self.WriteInput('y')
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6')

  def testCreateWithPromptedAllowUnauthAtPromptFailBindPolicy(self):
    self.WriteInput('n')
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, no_allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6')
    self.AssertErrContains(
        'WARNING: Function created with limited-access IAM policy. To enable '
        'unauthorized access consider "gcloud alpha functions '
        'add-iam-policy-binding my-test --member=allUsers '
        '--role=roles/cloudfunctions.invoker"')

  def testCreatehWithNoAllowUnauth(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        functools.partial(
            self._ExpectFunctionCreateWithHttp, no_allow_unauthenticated=True))
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run('functions deploy my-test --trigger-http --stage-bucket buck '
             '--runtime=nodejs6 --no-allow-unauthenticated')


class FunctionsAlphaTests(FunctionsBetaTests):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  # Get test coverage of repeated polling to remove IAM policy bindings by doing
  # it for all the alpha tests.
  def _MaybeExpectRemoveIamPolicyBinding(self, test_name):
    self._ExpectRemoveIamPolicyBinding(test_name, True, True)

  def _GenerateFunctionWithBuildWorkerPool(self, name, url, build_worker_pool,
                                           bucket):
    return self.messages.CloudFunction(
        name=name,
        sourceArchiveUrl=url,
        buildWorkerPool=build_worker_pool,
        eventTrigger=self.messages.EventTrigger(
            eventType='google.storage.object.finalize',
            resource='projects/_/buckets/' + bucket,
        ),
        runtime='nodejs6',
        labels=self._GetDefaultLabelsMessage(),
    )

  def _ExpectFunctionCreateWithBuildWorkerPool(self, build_worker_pool):

    def Callback(gcs_dest_url):
      test_name = 'projects/{}/locations/{}/functions/my-test'.format(
          self.Project(), self.GetRegion())
      test_location = 'projects/{}/locations/{}'.format(self.Project(),
                                                        self.GetRegion())
      self.mock_client.projects_locations_functions.Create.Expect(
          self.messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
              location=test_location,
              cloudFunction=self._GenerateFunctionWithBuildWorkerPool(
                  test_name, gcs_dest_url, build_worker_pool, 'path')),
          self._GenerateActiveOperation('operations/operation'))
      self._MaybeExpectRemoveIamPolicyBinding(test_name)
      self._ExpectGetOperationAndGetFunction(test_name)
      return 0

    return Callback

  def _ExpectFunctionCreateWithClearBuildWorkerPool(self):
    return self._ExpectFunctionCreateWithBuildWorkerPool('')

  def testInvalidTriggerResourceProjectResource(self):
    self.MockUnpackedSourcesDirSize()
    with self.assertRaisesRegex(properties.InvalidProjectError, '@'):
      self.Run('functions deploy my-test '
               '--trigger-event providers/firebase.auth/eventTypes/user.create '
               '--trigger-resource @ --stage-bucket buck --runtime=nodejs6')

  def testUserCreateExplicitProject(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self._ExpectCreateFunctionWith(
        event_type='providers/firebase.auth/eventTypes/user.create',
        resource='projects/asdf')
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test '
             '--trigger-event providers/firebase.auth/eventTypes/user.create '
             '--trigger-resource asdf --stage-bucket buck --runtime=nodejs6')

  def testUserCreateExplicitProjectWithNodeModules(self):
    self.MockUnpackedSourcesDirSize()
    self._ExpectCreateFunctionWithModules(
        event_type='providers/firebase.auth/eventTypes/user.create',
        resource='projects/asdf')
    self.ExpectResourceManagerTestIamPolicyBinding(False)
    self.Run('functions deploy my-test '
             '--trigger-event providers/firebase.auth/eventTypes/user.create '
             '--trigger-resource asdf --stage-bucket buck --runtime=nodejs6')

  def testCreateWithBuildWorkerPool(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        self._ExpectFunctionCreateWithBuildWorkerPool('worker'))
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test '
        '--build-worker-pool worker --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithClearBuildWorkerPool(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        self._ExpectFunctionCreateWithClearBuildWorkerPool())
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test '
        '--clear-build-worker-pool --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')

  def testCreateWithEmptyBuildWorkerPool(self):
    self.MockUnpackedSourcesDirSize()
    self.MockChooserAndMakeZipFromFileList()
    self.StartObjectPatch(archive, 'MakeZipFromDir', self.FakeMakeZipFromDir)
    test_name = 'projects/{}/locations/{}/functions/my-test'.format(
        self.Project(), self.GetRegion())
    self._ExpectCopyFileToGCS(
        self._ExpectFunctionCreateWithBuildWorkerPool(None))
    self.ExpectResourceManagerTestIamPolicyBinding(True)
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        exception=testutil.CreateTestHttpError(404, 'Not Found'))
    self.Run(
        'functions deploy my-test '
        '--build-worker-pool "" --trigger-bucket path '
        '--stage-bucket buck --runtime=nodejs6')


if __name__ == '__main__':
  test_case.main()
