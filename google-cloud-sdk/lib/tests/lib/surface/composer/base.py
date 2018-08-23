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
"""Base classes for Composer tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.surface.composer import kubectl_util
import six


class _ComposerBase(cli_test_base.CliTestBase):
  """Base class for all Composer tests."""

  def SetTrack(self, track):
    self.track = track
    self.messages = api_util.GetMessagesModule(release_track=self.track)


class ComposerUnitTestBase(sdk_test_base.WithFakeAuth, _ComposerBase):
  """Base class for Composer unit tests."""

  # TODO(b/67371929):Refactor test cases to create resources in funtions as
  # opposed to storing them all as constants in this base class
  LOCATION_NAME_FMT = 'projects/{0}/locations/{1}'
  ENVIRONMENT_NAME_FMT = LOCATION_NAME_FMT + '/environments/{2}'
  OPERATION_NAME_FMT = LOCATION_NAME_FMT + '/operations/{2}'
  TEST_PROJECT = 'google.com:test-project'
  TEST_LOCATION = 'us-location1'
  TEST_ENVIRONMENT_ID = 'test-environment'
  TEST_ENVIRONMENT_ID2 = 'test-environment2'
  TEST_OPERATION_UUID = '11111111-1111-1111-1111-111111111111'
  TEST_OPERATION_UUID2 = '22222222-2222-2222-2222-222222222222'
  TEST_GKE_CLUSTER = 'test-gke-cluster'
  TEST_CLUSTER_LOCATION = 'us-central1-a'

  TEST_ENVIRONMENT_NAME = ENVIRONMENT_NAME_FMT.format(
      TEST_PROJECT, TEST_LOCATION, TEST_ENVIRONMENT_ID)
  TEST_ENVIRONMENT_NAME2 = ENVIRONMENT_NAME_FMT.format(
      TEST_PROJECT, TEST_LOCATION, TEST_ENVIRONMENT_ID2)
  TEST_LOCATION_NAME = LOCATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION)
  TEST_OPERATION_NAME = OPERATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION,
                                                  TEST_OPERATION_UUID)
  TEST_OPERATION_NAME2 = OPERATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION,
                                                   TEST_OPERATION_UUID2)

  def _SetTestGcsBucket(self):
    self.test_gcs_bucket_path = 'gs://test-bucket'
    self.test_gcs_bucket = storage_util.BucketReference.FromBucketUrl(
        self.test_gcs_bucket_path)

  def SetTrack(self, track):
    super(ComposerUnitTestBase, self).SetTrack(track)
    self.mock_client = api_mock.Client(
        apis.GetClientClass(
            api_util.COMPOSER_API_NAME,
            api_util.GetApiVersion(release_track=self.track)))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

  def MakeEnvironment(self,
                      project,
                      location,
                      environment_id,
                      config=None,
                      state=None,
                      labels=None):
    environment_name = self.ENVIRONMENT_NAME_FMT.format(project, location,
                                                        environment_id)
    environment = self.messages.Environment()
    if environment_name is not None:
      environment.name = environment_name
    if config is not None:
      environment.config = config
    if state is not None:
      environment.state = state
    if labels is not None:
      environment.labels = ComposerUnitTestBase._MakeLabelsValue(
          labels, self.messages)
    return environment

  def MakeEnvironmentWithStateAndClusterLocation(
      self, state, cluster_location=TEST_CLUSTER_LOCATION):
    return self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.messages.EnvironmentConfig(
            gkeCluster=self.TEST_GKE_CLUSTER,
            nodeConfig=self.messages.NodeConfig(location=cluster_location)),
        state=state)

  def MakeOperation(self,
                    project,
                    location,
                    uuid,
                    done=False,
                    error=None,
                    metadata=None,
                    response=None):
    op = self.messages.Operation(
        name=self.OPERATION_NAME_FMT.format(project, location, uuid),
        done=done,
        error=error,
        metadata=metadata,
        response=response)

    return op

  def ExpectOperationGet(self,
                         project,
                         location,
                         operation_id,
                         response=None,
                         exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.ComposerProjectsLocationsOperationsGetRequest(
            name=self.OPERATION_NAME_FMT.format(project, location,
                                                operation_id)),
        response=response,
        exception=exception)

  @staticmethod
  def _MakeLabelsValue(labels_dict, messages):
    """Constructs an instance of LabelsValue from a dict.

    The returned instance should be used as the labels property of an
    Environment message.

    Args:
      labels_dict: dict(str,str), the dict to convert to LabelsValue proto.
      messages: the Compoer client library messages.

    Returns:
      LabelsValue, the labels_dict converted to LabelsValue proto.
    """
    additional_property = (messages.Environment.LabelsValue.AdditionalProperty)
    labels_value = messages.Environment.LabelsValue

    return labels_value(additionalProperties=[
        additional_property(key=key, value=value)
        for key, value in six.iteritems(labels_dict)
    ])


class ComposerE2ETestBase(e2e_base.WithServiceAuth, _ComposerBase):
  """Base class for Composer e2e tests.

  Composer environments take upwards of 10 minutes to create, and approximately
  5 minutes to delete and update. Due to a 2 minute limit on e2e tests
  it is not possible to create or delete environments. Instead, Composer e2e
  tests assume existing environments in the integration test project.

  The assumptions currently held are:
  - All existing environments are created in us-central1.
  - The existing environments are in 'RUNNING' state, meaning they have been
    created successfully.
  - There is at least one existing environment.

  """


class EnvironmentsUnitTest(ComposerUnitTestBase):
  """Base class for Composer Environments unit tests."""

  def ExpectEnvironmentCreate(self,
                              project,
                              location,
                              environment_id,
                              config=None,
                              state=None,
                              labels=None,
                              response=None,
                              exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_environments.Create.Expect(
        self.messages.ComposerProjectsLocationsEnvironmentsCreateRequest(
            environment=self.MakeEnvironment(
                project,
                location,
                environment_id,
                labels=labels,
                config=config,
                state=state),
            parent=self.LOCATION_NAME_FMT.format(project, location)),
        response=response,
        exception=exception)

  def ExpectEnvironmentDelete(self,
                              project,
                              location,
                              environment_id,
                              response=None,
                              exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_environments.Delete.Expect(
        self.messages.ComposerProjectsLocationsEnvironmentsDeleteRequest(
            name=self.ENVIRONMENT_NAME_FMT.format(project, location,
                                                  environment_id)),
        response=response,
        exception=exception)

  def ExpectEnvironmentGet(self,
                           project,
                           location,
                           environment_id,
                           response=None,
                           exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_environments.Get.Expect(
        self.messages.ComposerProjectsLocationsEnvironmentsGetRequest(
            name=self.ENVIRONMENT_NAME_FMT.format(project, location,
                                                  environment_id)),
        response=response,
        exception=exception)

  def ExpectEnvironmentsList(self,
                             project,
                             location,
                             page_size,
                             response_list=None,
                             exception=None):
    if response_list is None and exception is None:
      response_list = [self.messages.Empty()]
    page_token = None
    for mock_response in response_list:
      self.mock_client.projects_locations_environments.List.Expect(
          self.messages.ComposerProjectsLocationsEnvironmentsListRequest(
              parent=six.text_type(
                  self.LOCATION_NAME_FMT.format(project, location)),
              pageSize=page_size,
              pageToken=page_token),
          response=mock_response,
          exception=None)
      page_token = mock_response.nextPageToken

  def ExpectEnvironmentPatch(self,
                             project,
                             location,
                             environment_id,
                             update_mask=None,
                             patch_environment=None,
                             response=None,
                             exception=None):
    """Expects an Environments API Patch call with the provided data.

    If the call is not made as specified, fails the testcase.

    Args:
      project: project name of the environment.
      location: location of the environment.
      environment_id: id for the environment.
      update_mask: a string fieldmask for the patch call.
      patch_environment: an Environment resource supplying data for the patch.
      response: the object to return as a response to the call.
      exception: if not None, the exception raised when the call is made.
    """
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_environments.Patch.Expect(
        self.messages.ComposerProjectsLocationsEnvironmentsPatchRequest(
            name=self.ENVIRONMENT_NAME_FMT.format(project, location,
                                                  environment_id),
            updateMask=update_mask,
            environment=patch_environment),
        response=response,
        exception=exception)

  def RunEnvironments(self, *args):
    return self.Run(['composer', 'environments'] + list(args))


class OperationsUnitTest(ComposerUnitTestBase):
  """Base class for Composer Operations unit tests."""

  def ExpectOperationDelete(self,
                            project,
                            location,
                            operation_id,
                            response=None,
                            exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_operations.Delete.Expect(
        self.messages.ComposerProjectsLocationsOperationsDeleteRequest(
            name=self.OPERATION_NAME_FMT.format(project, location,
                                                operation_id)),
        response=response,
        exception=exception)

  def ExpectOperationsList(self,
                           project,
                           location,
                           page_size,
                           response_list=None,
                           exception=None):
    if response_list is None and exception is None:
      response_list = [self.messages.Empty()]
    page_token = None
    for mock_response in response_list:
      self.mock_client.projects_locations_operations.List.Expect(
          self.messages.ComposerProjectsLocationsOperationsListRequest(
              name=self.LOCATION_NAME_FMT.format(project, location),
              pageSize=page_size,
              pageToken=page_token),
          response=mock_response,
          exception=None)
      page_token = mock_response.nextPageToken

  def RunOperations(self, *args):
    return self.Run(['composer', 'operations'] + list(args))


class KubectlShellingUnitTest(EnvironmentsUnitTest):
  """Base class for Environments unit tests that shell out to kubectl.
  """
  TEST_GCLOUD_PATH = '/fake/path/to/gcloud'
  TEST_KUBECTL_PATH = '/fake/path/to/kubectl'

  def SetUp(self):
    self.StartObjectPatch(files, 'FindExecutableOnPath',
                          self._FakeFindExecutableOnPath)

  def MakeGetPodsCallback(self, pods_statuses):
    """Constructs an execution callback to use with kubectl_util.FakeExec.

    The callback is for a call to kubectl get pods and can return pods with
    specific statuses.

    Args:
      pods_statuses: list of tuple(str, str), pairs of (pod name, pod status)
          that will be formatted and output by the callback.

    Returns:
      Fake result of 'kubectl get pods' execution with desired pod_statuses.
    """
    output = '\n'.join(
        '{}\t{}'.format(pod, status) for pod, status in pods_statuses)

    def _GetPodsCallback(args, **kwargs):
      kubectl_util.AssertListHasPrefix(self, args,
                                       [self.TEST_KUBECTL_PATH, 'get', 'pods'])
      if kwargs.get('out_func') is not None:
        kwargs['out_func'](output)
      return 0

    return _GetPodsCallback

  @contextlib.contextmanager
  def FakeTemporaryKubeconfig(self, *args):
    yield

  @staticmethod
  def _FakeFindExecutableOnPath(executable, *_):
    if executable == 'gcloud':
      return KubectlShellingUnitTest.TEST_GCLOUD_PATH
    elif executable == 'kubectl':
      return KubectlShellingUnitTest.TEST_KUBECTL_PATH
    else:
      return None


class StorageApiCallingUnitTest(EnvironmentsUnitTest):
  """Base class for Environments unit tests that call the Cloud Storage API."""

  def SetUp(self):
    self._SetTestGcsBucket()
    self.mock_storage_client = api_mock.Client(
        apis.GetClientClass('storage', 'v1'))
    self.storage_messages = apis.GetMessagesModule('storage', 'v1')
    self.mock_storage_client.Mock()
    self.addCleanup(self.mock_storage_client.Unmock)

  def MakeEnvironmentWithBucket(self):
    return self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.messages.EnvironmentConfig(
            dagGcsPrefix=self.test_gcs_bucket_path + '/dags'))

  def ExpectObjectList(self, bucket_ref, prefix, responses=None,
                       exception=None):
    if exception:
      self.mock_storage_client.objects.List.Expect(
          self.storage_messages.StorageObjectsListRequest(
              bucket=bucket_ref.bucket, prefix=prefix),
          exception=exception)
      return
    if not responses:
      responses = [self.messages.Empty()]
    page_token = None
    for mock_response in responses:
      self.mock_storage_client.objects.List.Expect(
          self.storage_messages.StorageObjectsListRequest(
              bucket=bucket_ref.bucket, prefix=prefix, pageToken=page_token),
          response=mock_response,
          exception=None)
      page_token = mock_response.nextPageToken

  def ExpectObjectGet(self, object_ref, response=None, exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_storage_client.objects.Get.Expect(
        self.storage_messages.StorageObjectsGetRequest(
            bucket=object_ref.bucket, object=object_ref.name),
        response=response,
        exception=exception)

  def ExpectObjectInsert(self, object_ref, response=None, exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_storage_client.objects.Insert.Expect(
        self.storage_messages.StorageObjectsInsertRequest(
            bucket=object_ref.bucket, name=object_ref.name),
        response=response,
        exception=exception)


class GsutilShellingUnitTest(EnvironmentsUnitTest):
  """Base class for Environments unit tests that shell out to gsutil."""
  TEST_GSUTIL_PATH = '/fake/path/to/gsutil'
  EXPECTED_LINUX_PATH = [TEST_GSUTIL_PATH]
  EXPECTED_WINDOWS_PATH = ['cmd', '/c', TEST_GSUTIL_PATH + '.cmd']

  def SetUp(self):
    self._SetTestGcsBucket()
    self.StartPatch(
        'googlecloudsdk.api_lib.storage.storage_util._GetGsutilPath',
        return_value=self.TEST_GSUTIL_PATH)

  def MakeEnvironmentWithBucket(self):
    return self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.messages.EnvironmentConfig(
            dagGcsPrefix=self.test_gcs_bucket_path + '/dags'))

  def MakeGsutilExecCallback(self, expected_args_to_gsutil):

    def _GsutilExecCallback(args, **_):
      path = self.EXPECTED_LINUX_PATH
      if platforms.OperatingSystem.Current(
      ) == platforms.OperatingSystem.WINDOWS:
        path = self.EXPECTED_WINDOWS_PATH
      expected_args = path + expected_args_to_gsutil
      self.assertEquals(expected_args, args)
      return 0

    return _GsutilExecCallback
