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
"""Tests of the 'databases create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.firestore import create_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import api_test_util


class CreateFirestoreDatabaseTest(api_test_util.ApiTestBase):

  REGION = 'us-central'  # Any valid region

  def testCreate_withNoApp_withRegion(self):
    # Set it up so that the app doesn't exist:
    err = http_error.MakeHttpError(code=404)
    self.ExpectGetApplicationRequest(self.Project(), exception=err)

    with self.assertRaises(create_util.AppEngineAppDoesNotExist):
      self.Run('firestore databases create --region=foo')

  def testCreate_withAppMissingRegionFlag(self):
    self.ExpectGetApplicationRequest(self.Project(), location_id=self.REGION)
    with self.assertRaises(create_util.RegionNotSpecified):
      self.Run('firestore databases create')

  def testCreate_withAppWithRegionFlag_mismatch(self):
    self.ExpectGetApplicationRequest(self.Project(), location_id=self.REGION)

    with self.assertRaises(create_util.AppEngineAppRegionDoesNotMatch):
      self.Run('firestore databases create --region=foo')

  def testCreate_withAppWithgRegionFlag_match_success(self):
    self.ExpectGetApplicationRequest(self.Project(), location_id=self.REGION)
    api_client = appengine_api_client.GetApiClientForTrack(
        calliope_base.ReleaseTrack.GA)
    self.ExpectAppengineAppsPatchRequest(
        self.Project(),
        update_mask='databaseType',
        database_type=api_client.messages.Application
        .DatabaseTypeValueValuesEnum.CLOUD_FIRESTORE)

    self.Run('firestore databases create --region={region}'.format(
        region=self.REGION))

  def createAndDbTypeAlreadyMatches_noActions(self):
    api_client = appengine_api_client.GetApiClientForTrack(
        calliope_base.ReleaseTrack.GA)
    self.ExpectGetApplicationRequest(
        self.Project(),
        location_id=self.REGION,
        database_type=api_client.messages.Application
        .DatabaseTypeValueValuesEnum.CLOUD_FIRESTORE)

    self.Run('firestore databases create --region={region}'.format(
        region=self.REGION))


if __name__ == '__main__':
  test_case.main()
