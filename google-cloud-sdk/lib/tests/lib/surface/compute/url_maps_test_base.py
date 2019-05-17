# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Common component for url maps testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import difflib

from apitools.base.py import encoding
from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class UrlMapsTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for url maps test."""

  def _GetApiName(self):
    """Returns the API name for the specified release track."""
    if self.track == calliope_base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif self.track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  def SetUp(self):
    api_name = self._GetApiName()

    self.apitools_client = api_mock.Client(
        core_apis.GetClientClass('compute', api_name),
        real_client=core_apis.GetClientInstance(
            'compute', api_name, no_http=True))
    self.apitools_client.Mock()
    self.addCleanup(self.apitools_client.Unmock)
    self.messages = self.apitools_client.MESSAGES_MODULE

    self.resources = resources.Registry()
    self.resources.RegisterApiByName('compute', api_name)

  def GetUrlMapRef(self, name, region=None):
    params = {'project': self.Project()}
    if region:
      collection = 'compute.regionUrlMaps'
      params['region'] = region
    else:
      collection = 'compute.urlMaps'

    return self.resources.Parse(name, params=params, collection=collection)

  def ExpectGetRequest(self, url_map_ref, url_map=None, exception=None):
    if url_map_ref.Collection() == 'compute.regionUrlMaps':
      service = self.apitools_client.regionUrlMaps
      request_type = self.messages.ComputeRegionUrlMapsGetRequest
    else:
      service = self.apitools_client.urlMaps
      request_type = self.messages.ComputeUrlMapsGetRequest

    service.Get.Expect(
        request=request_type(**url_map_ref.AsDict()),
        response=url_map,
        exception=exception)

  def ExpectPatchRequest(self, url_map_ref, url_map=None, exception=None):
    if url_map_ref.Collection() == 'compute.regionUrlMaps':
      service = self.apitools_client.regionUrlMaps
      request_type = self.messages.ComputeRegionUrlMapsPatchRequest
      expected_request = request_type(
          urlMap=url_map_ref.Name(),
          project=self.Project(),
          urlMapResource=url_map,
          region=url_map_ref.region)
    else:
      service = self.apitools_client.urlMaps
      request_type = self.messages.ComputeUrlMapsPatchRequest
      expected_request = request_type(
          urlMap=url_map_ref.Name(),
          project=self.Project(),
          urlMapResource=url_map)

    service.Patch.Expect(
        request=expected_request,
        response=self.messages.Operation(
            name='operation-X',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING),
        exception=exception)

  def ExpectInsertRequest(self, url_map_ref, url_map=None, exception=None):
    if url_map_ref.Collection() == 'compute.regionUrlMaps':
      service = self.apitools_client.regionUrlMaps
      request_type = self.messages.ComputeRegionUrlMapsInsertRequest
      expected_request = request_type(
          urlMap=url_map, project=self.Project(), region=url_map_ref.region)
    else:
      service = self.apitools_client.urlMaps
      request_type = self.messages.ComputeUrlMapsInsertRequest
      expected_request = request_type(urlMap=url_map, project=self.Project())

    service.Insert.Expect(
        request=expected_request,
        response=self.messages.Operation(
            name='operation-X',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING),
        exception=exception)

  def AssertMessagesEqual(self, expected, actual):
    if expected != actual:
      raise MessageEqualityAssertionError(expected, actual)

  def MakeTestUrlMap(self, messages, api):
    return messages.UrlMap(
        name='url-map-1',
        defaultService='https://www.googleapis.com/compute/' + api +
        '/projects/my-project/global/backendServices/default-service',
        selfLink='https://www.googleapis.com/compute/' + api +
        '/projects/my-project/global/urlMaps/url-map-1')


class MessageEqualityAssertionError(AssertionError):
  """Extend AssertionError with difference between two protos in message."""

  def __init__(self, expected, actual):
    expected_repr = encoding.MessageToRepr(expected, multiline=True)
    actual_repr = encoding.MessageToRepr(actual, multiline=True)

    expected_lines = expected_repr.splitlines()
    actual_lines = actual_repr.splitlines()

    diff_lines = difflib.unified_diff(expected_lines, actual_lines)

    message = '\n'.join(['expected: {expected}', 'actual: {actual}', 'diff:'] +
                        list(diff_lines)).format(
                            expected=expected_repr, actual=actual_repr)
    super(MessageEqualityAssertionError, self).__init__(message)
