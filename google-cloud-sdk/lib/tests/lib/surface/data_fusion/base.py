# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Base classes for Data Fusion tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
import six


class _DatafusionTestBase(cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DatafusionE2ETestBase(e2e_base.WithServiceAuth, _DatafusionTestBase):
  """Base class for Datafusion e2e tests.

  Datafusion instances take upwards of 10 minutes to create, delete, and
  restart. Due to a 2 minute limit on e2e tests
  it is not possible to create or delete instances. Instead, Datafusion e2e
  tests assume existing instances in the integration test project.

  The assumptions currently held are:
  - All existing instances are created in us-central1.
  - The existing instances are in 'RUNNING' state, meaning they have been
    created successfully.
  - There is at least one existing instances.

  """


class DatafusionUnitTestBase(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):
  """Base class for Data Fusion unit tests."""

  LOCATION_NAME_FMT = 'projects/{0}/locations/{1}'
  INSTANCE_NAME_FMT = LOCATION_NAME_FMT + '/instances/{2}'
  OPERATION_NAME_FMT = LOCATION_NAME_FMT + '/operations/{2}'
  TEST_PROJECT = 'fake-project'
  TEST_LOCATION = 'us-location1'
  TEST_ZONE = 'us-location1c'
  TEST_INSTANCE = 'instance-name'
  TEST_TYPE = 'enterprise'
  TEST_VERSION = '6.1.0.0'
  TEST_OPTIONS = 'opt1=x,opt2=y'
  TEST_OPTIONS_DICT = {'opt1': 'x', 'opt2': 'y'}
  TEST_OPERATION_UUID = '11111111-1111-1111-1111-111111111111'
  TEST_OPERATION_UUID2 = '22222222-2222-2222-2222-222222222222'

  TEST_LOCATION_NAME = LOCATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION)
  TEST_INSTANCE_NAME = INSTANCE_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION,
                                                TEST_INSTANCE)
  TEST_OPERATION_NAME = OPERATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION,
                                                  TEST_OPERATION_UUID)
  TEST_OPERATION_NAME2 = OPERATION_NAME_FMT.format(TEST_PROJECT, TEST_LOCATION,
                                                   TEST_OPERATION_UUID2)
  DATAFUSION = 'datafusion'
  API_VERSION = 'v1beta1'

  def SetUp(self):
    self.messages = apis.GetMessagesModule(self.DATAFUSION, self.API_VERSION)
    self.mock_client = api_mock.Client(
        apis.GetClientClass(self.DATAFUSION, self.API_VERSION))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

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

  def MakeInstance(self,
                   zone,
                   edition,
                   enable_stackdriver_logging,
                   enable_stackdriver_monitoring,
                   options=None,
                   labels=None):
    if not options:
      options = {}
    if not labels:
      labels = {}
    instance = self.messages.Instance(
        zone=zone,
        type=edition,
        enableStackdriverLogging=enable_stackdriver_logging,
        enableStackdriverMonitoring=enable_stackdriver_monitoring,
        options=encoding.DictToAdditionalPropertyMessage(
            options, self.messages.Instance.OptionsValue, True),
        labels=encoding.DictToAdditionalPropertyMessage(
            labels, self.messages.Instance.LabelsValue, True))
    return instance

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

  def ExpectOperationGet(self,
                         project,
                         location,
                         operation_id,
                         response=None,
                         exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.DatafusionProjectsLocationsOperationsGetRequest(
            name=self.OPERATION_NAME_FMT.format(project, location,
                                                operation_id)),
        response=response,
        exception=exception)


class OperationsUnitTest(DatafusionUnitTestBase):
  """Base class for Datafusion Operations unit tests."""

  def ExpectOperationDelete(self,
                            project,
                            location,
                            operation_id,
                            response=None,
                            exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_operations.Delete.Expect(
        self.messages.DatafusionProjectsLocationsOperationsDeleteRequest(
            name=self.OPERATION_NAME_FMT.format(project, location,
                                                operation_id)),
        response=response,
        exception=exception)

  def ExpectOperationsList(self,
                           project,
                           location,
                           response_list=None,
                           exception=None):
    if response_list is None and exception is None:
      response_list = [self.messages.Empty()]
    page_token = None
    for mock_response in response_list:
      self.mock_client.projects_locations_operations.List.Expect(
          self.messages.DatafusionProjectsLocationsOperationsListRequest(
              name=self.LOCATION_NAME_FMT.format(project, location),
              pageToken=page_token),
          response=mock_response,
          exception=None)
      page_token = mock_response.nextPageToken

  def RunOperations(self, *args):
    return self.Run(['beta', 'data-fusion', 'operations'] + list(args))


class InstancesUnitTest(DatafusionUnitTestBase):
  """Base class for Datafusion Instances unit tests."""

  def ExpectInstanceCreate(self,
                           project,
                           location,
                           instance_id,
                           zone,
                           edition=None,
                           enable_stackdriver_logging=False,
                           enable_stackdriver_monitoring=False,
                           options=None,
                           labels=None,
                           response=None,
                           exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    if edition is None:
      edition = self.messages.Instance.TypeValueValuesEnum.BASIC
    self.mock_client.projects_locations_instances.Create.Expect(
        self.messages.DatafusionProjectsLocationsInstancesCreateRequest(
            instance=self.MakeInstance(
                zone,
                edition,
                enable_stackdriver_logging,
                enable_stackdriver_monitoring,
                options,
                labels),
            instanceId=instance_id,
            parent=self.LOCATION_NAME_FMT.format(project, location)),
        response=response,
        exception=exception)

  def ExpectInstanceDelete(self,
                           instance_id,
                           response=None,
                           exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_instances.Delete.Expect(
        self.messages.DatafusionProjectsLocationsInstancesDeleteRequest(
            name=instance_id),
        response=response,
        exception=exception)

  def ExpectInstanceGet(self,
                        project,
                        location,
                        instance_id,
                        response=None,
                        exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_instances.Get.Expect(
        self.messages.DatafusionProjectsLocationsInstancesGetRequest(
            name=self.INSTANCE_NAME_FMT.format(project, location,
                                               instance_id)),
        response=response,
        exception=exception)

  def ExpectInstanceRestart(self,
                            project,
                            location,
                            instance_id,
                            response=None,
                            exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    self.mock_client.projects_locations_instances.Restart.Expect(
        self.messages.DatafusionProjectsLocationsInstancesRestartRequest(
            name=self.INSTANCE_NAME_FMT.format(project, location,
                                               instance_id)),
        response=response,
        exception=exception)

  def ExpectInstanceUpdate(self,
                           project,
                           location,
                           instance_id,
                           version,
                           response=None,
                           exception=None):
    if response is None and exception is None:
      response = self.messages.Empty()
    name = self.INSTANCE_NAME_FMT.format(project, location, instance_id)
    self.mock_client.projects_locations_instances.Patch.Expect(
        self.messages.DatafusionProjectsLocationsInstancesPatchRequest(
            instance=self.messages.Instance(
                name=name,
                version=version,
                enableStackdriverLogging=False,
                enableStackdriverMonitoring=False,
                labels=encoding.DictToAdditionalPropertyMessage(
                    {}, self.messages.Instance.LabelsValue, True)),
            name=name),
        response=response,
        exception=exception)

  def ExpectInstancesList(self,
                          project,
                          location,
                          response_list=None,
                          exception=None):
    if response_list is None and exception is None:
      response_list = [self.messages.Empty()]
    page_token = None
    for mock_response in response_list:
      self.mock_client.projects_locations_instances.List.Expect(
          self.messages.DatafusionProjectsLocationsInstancesListRequest(
              parent=six.text_type(
                  self.LOCATION_NAME_FMT.format(project, location)),
              pageToken=page_token),
          response=mock_response,
          exception=exception)
      page_token = mock_response.nextPageToken

  def RunInstances(self, *args):
    return self.Run(['beta', 'data-fusion', 'instances'] + list(args))
