# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud access-context-manager perimeters dry-run describe`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


class DryRunDescribeTestBeta(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, perimeter):
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
        request_type(name=perimeter.name), perimeter)

  def testDescribe(self):
    self.SetUpForAPI(self.api_version)
    perimeter_with_status = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=['projects/123', 'projects/456'],
        restricted_services=[
            'storage.googleapis.com', 'bigtable.googleapis.com'
        ])
    perimeter_with_spec = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=['projects/456', 'projects/789'],
        restricted_services=[
            'bigtable.googleapis.com', 'bigquery.googleapis.com'
        ],
        dry_run=True)
    final_perimeter = perimeter_with_spec
    final_perimeter.status = perimeter_with_status.status

    self._ExpectGet(final_perimeter)

    self.Run('access-context-manager perimeters dry-run describe MY_PERIMETER'
             '   --policy 123')

    self.AssertOutputEquals("""\
name: MY_PERIMETER
title: Perimeter 1
type: PERIMETER_TYPE_REGULAR
resources:
  +projects/789
  -projects/123
   projects/456
restrictedServices:
  +bigquery.googleapis.com
  -storage.googleapis.com
   bigtable.googleapis.com
accessLevels:
   accessPolicies/123/accessLevels/MY_LEVEL
   accessPolicies/123/accessLevels/MY_LEVEL_2
vpcAccessibleServices:
   NONE
""")


class DryRunDescribeTestAlpha(DryRunDescribeTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
