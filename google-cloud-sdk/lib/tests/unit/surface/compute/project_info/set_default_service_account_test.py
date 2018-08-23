# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the project-info set-default-service-account subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'alpha')

SERVICE_ACCOUNT_FLAG_CANNOT_BE_EMPTY_MESSAGE = (
    'Missing required argument [--service-account]: must be specified with a '
    'service account. To clear the default service account use '
    '[--no-service-account].')


class ProjectInfoSetDefaultServiceAccountTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = base.ReleaseTrack.ALPHA

  def testNoFlagSpecified(self):
    with self.AssertRaisesToolExceptionMatches(
        SERVICE_ACCOUNT_FLAG_CANNOT_BE_EMPTY_MESSAGE):
      self.Run("""
          compute project-info set-default-service-account
          """)

    self.CheckRequests()

  def testClearAndSetFlagsSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --service-account: At most one of --service-account | '
        '--no-service-account may be specified.'):
      self.Run("""
          compute project-info set-default-service-account
          --service-account test@developers.gserviceaccount.com
          --no-service-account
          """)

    self.CheckRequests()

  def testSetServiceAccountWithNoAccount(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --service-account: expected one argument'):
      self.Run("""
          compute project-info set-default-service-account
            --service-account
          """)

    self.CheckRequests()

  def testClearWithNoServiceAccountFlag(self):
    self.Run("""
        compute project-info set-default-service-account
          --no-service-account
        """)

    self.CheckRequests(
        [(self.compute_alpha.projects,
          'SetDefaultServiceAccount',
          messages.ComputeProjectsSetDefaultServiceAccountRequest(
              project='my-project',
              projectsSetDefaultServiceAccountRequest=
              messages.ProjectsSetDefaultServiceAccountRequest()
          ))],
    )

  def testSetDefaultWithServiceAccount(self):
    self.Run("""
        compute project-info set-default-service-account
          --service-account test@developers.gserviceaccount.com
        """)

    self.CheckRequests(
        [(self.compute_alpha.projects,
          'SetDefaultServiceAccount',
          messages.ComputeProjectsSetDefaultServiceAccountRequest(
              project='my-project',
              projectsSetDefaultServiceAccountRequest=
              messages.ProjectsSetDefaultServiceAccountRequest(
                  email='test@developers.gserviceaccount.com'
              )
          ))],
    )


if __name__ == '__main__':
  test_case.main()
