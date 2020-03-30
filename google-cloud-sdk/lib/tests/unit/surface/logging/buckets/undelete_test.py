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

"""Tests of the 'buckets undelete' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class BucketsUndeleteTest(base.LoggingTestBase):

  def testUndeleteSuccess(self):
    self.mock_client_v2.projects_locations_buckets.Undelete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsUndeleteRequest(
            name='projects/my-project/locations/global/buckets/porkpie'),
        self.msgs.Empty())
    self.RunLogging(
        'buckets undelete porkpie --location=global',
        calliope_base.ReleaseTrack.ALPHA)

  def testUndeleteSuccessOrganization(self):
    self.mock_client_v2.projects_locations_buckets.Undelete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsUndeleteRequest(
            name='organizations/1234/locations/global/buckets/porkpie'),
        self.msgs.Empty())
    self.RunLogging(
        'buckets undelete porkpie --location=global --organization=1234',
        calliope_base.ReleaseTrack.ALPHA)

  def testUneleteNoPerms(self):
    self.mock_client_v2.projects_locations_buckets.Undelete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsUndeleteRequest(
            name='projects/my-project/locations/global/buckets/porkpie'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('buckets undelete porkpie --location=global -q',
                         calliope_base.ReleaseTrack.ALPHA)

  def testUndeleteNoProject(self):
    self.RunWithoutProject('buckets undelete porkpie --location=global',
                           calliope_base.ReleaseTrack.ALPHA)

  def testUndeleteNoAuth(self):
    self.RunWithoutAuth('buckets undelete porkpie --location=global',
                        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
