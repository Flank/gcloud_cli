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

"""Base for Dataproc tests that need to mock compute."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import base_api

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
import mock


class _IsInstance(object):

  def __init__(self, cls):
    self.cls = cls

  def __eq__(self, value):
    return isinstance(value, self.cls)


class BaseComputeUnitTest(cli_test_base.CliTestBase):
  """Base test for all Dataproc gcloud tests that call compute."""

  SUBNET = 'test-subnetwork'

  def GetComputeApiVersion(self):
    if self.track == calliope_base.ReleaseTrack.GA:
      return 'v1'
    elif self.track == calliope_base.ReleaseTrack.BETA:
      return 'beta'
    return 'alpha'

  def SetUp(self):
    # Used by compute to find current zone for prompting.
    self.compute_messages = apis.GetMessagesModule('compute',
                                                   self.GetComputeApiVersion())

  def SubnetUri(self):
    return ('https://www.googleapis.com/compute/{track}/projects/'
            '{project}/regions/us-central1/subnetworks/test-subnetwork'.format(
                track=self.GetComputeApiVersion(), project=self.Project()))

  def ImageUri(self):
    return ('https://www.googleapis.com/compute/{track}/projects/'
            '{project}/global/images/test-image'.format(
                track=self.GetComputeApiVersion(), project=self.Project()))

  # Copied from compute.tests.unit.test_resources with slight modifications
  def GetZones(self):
    return [
        self.compute_messages.Zone(
            name='us-central1-a',
            region=('https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/regions/us-central1'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project())),
            status=self.compute_messages.Zone.StatusValueValuesEnum.UP,
            selfLink=('https://www.googleapis.com/compute/{track}/projects/'
                      '{project}/zones/us-central1-a'.format(
                          track=self.GetComputeApiVersion(),
                          project=self.Project())),
            deprecated=self.compute_messages.DeprecationStatus(
                state=(self.compute_messages.DeprecationStatus.
                       StateValueValuesEnum.DEPRECATED),
                deleted='2015-03-29T00:00:00.000-07:00',
                replacement=(
                    'https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/zones/us-central1-b'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project())))),
        self.compute_messages.Zone(
            name='us-central1-b',
            status=self.compute_messages.Zone.StatusValueValuesEnum.UP,
            region=('https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/regions/us-central1'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project())),
            selfLink=('https://www.googleapis.com/compute/{track}/projects/'
                      '{project}/zones/us-central1-b'.format(
                          track=self.GetComputeApiVersion(),
                          project=self.Project()))),
        self.compute_messages.Zone(
            name='europe-west1-a',
            status=self.compute_messages.Zone.StatusValueValuesEnum.UP,
            region=('https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/regions/europe-west1'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project())),
            selfLink=('https://www.googleapis.com/compute/{track}/projects/'
                      '{project}/zones/europe-west1-a'.format(
                          track=self.GetComputeApiVersion(),
                          project=self.Project()))),
        self.compute_messages.Zone(
            name='europe-west1-b',
            status=self.compute_messages.Zone.StatusValueValuesEnum.DOWN,
            region=('https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/regions/europe-west1'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project())),
            selfLink=('https://www.googleapis.com/compute/{track}/projects/'
                      '{project}/zones/europe-west1-a'.format(
                          track=self.GetComputeApiVersion(),
                          project=self.Project())),
            deprecated=self.compute_messages.DeprecationStatus(
                state=(self.compute_messages.DeprecationStatus.
                       StateValueValuesEnum.DELETED),
                deleted='2015-03-29T00:00:00.000-07:00',
                replacement=(
                    'https://www.googleapis.com/compute/{track}/projects/'
                    '{project}/zones/europe-west1-a'.format(
                        track=self.GetComputeApiVersion(),
                        project=self.Project()))))
    ]

  def MockCompute(self):
    self.compute_requests_patcher = self.StartPatch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)

  def ExpectListZones(self, requests=None, responses=None):
    if not requests:
      requests = [(_IsInstance(base_api.BaseApiService), 'List', mock.ANY)]
    if not responses:
      responses = self.GetZones()

    self.compute_requests_patcher.return_value = iter(responses)

    def check_requests():
      self.compute_requests_patcher.assert_called_once_with(
          requests=requests, batch_url=mock.ANY, errors=mock.ANY,
          http=mock.ANY, progress_tracker=None)
    self.addCleanup(check_requests)
