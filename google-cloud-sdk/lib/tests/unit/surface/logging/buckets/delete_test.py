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

"""Tests of the 'buckets delete' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class BucketsDeleteTest(base.LoggingTestBase):

  def testDeletePromptNo(self):
    self.WriteInput('n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunLogging(
          'buckets delete porkpie --location=global',
          calliope_base.ReleaseTrack.ALPHA)

  def testDeletePromptYes(self):
    self.WriteInput('Y')
    self.mock_client_v2.projects_locations_buckets.Delete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsDeleteRequest(
            name='projects/my-project/locations/global/buckets/porkpie'),
        self.msgs.Empty())
    self.RunLogging(
        'buckets delete porkpie --location=global',
        calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrContains('Deleted')

  def testDeletePromptYesOrganization(self):
    self.WriteInput('Y')
    self.mock_client_v2.projects_locations_buckets.Delete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsDeleteRequest(
            name='organizations/1234/locations/global/buckets/porkpie'),
        self.msgs.Empty())
    self.RunLogging(
        'buckets delete porkpie --location=global --organization=1234',
        calliope_base.ReleaseTrack.ALPHA)
    self.AssertErrContains('Deleted')

  def testDeleteNoPerms(self):
    self.mock_client_v2.projects_locations_buckets.Delete.Expect(
        self.msgs.LoggingProjectsLocationsBucketsDeleteRequest(
            name='projects/my-project/locations/global/buckets/porkpie'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('buckets delete porkpie --location=global -q',
                         calliope_base.ReleaseTrack.ALPHA)

  def testDeleteNoProject(self):
    self.RunWithoutProject('buckets delete porkpie --location=global',
                           calliope_base.ReleaseTrack.ALPHA)

  def testDeleteNoAuth(self):
    self.RunWithoutAuth('buckets delete porkpie --location=global',
                        calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
