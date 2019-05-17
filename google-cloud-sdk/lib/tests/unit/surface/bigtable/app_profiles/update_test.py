# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Test of the 'update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.bigtable import base


class AppProfileUpdateTestsGA(base.BigtableV2TestBase,
                              waiter_test_base.CloudOperationsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def ExpectOp(self):
    self.ExpectOperation(self.client.operations, 'operations/operation-name',
                         self.client.projects_instances_appProfiles,
                         'appProfiles/my-app-profile')

  def SetUp(self):
    self.app_profile_update_mock = self.StartObjectPatch(
        app_profiles,
        'Update',
        return_value=self.msgs.Operation(name='operations/operation-name'))
    self.app_profile_ref = util.GetAppProfileRef('my-instance',
                                                 'my-app-profile')

  def testUpdateMultiCluster(self):
    self.ExpectOp()
    self.Run('bigtable app-profiles update my-app-profile '
             '--instance my-instance --description my-description '
             '--route-any')
    self.app_profile_update_mock.assert_called_once_with(
        self.app_profile_ref,
        cluster=None,
        description='my-description',
        multi_cluster=True,
        transactional_writes=False,
        force=False)

  def testUpdateSingleCluster(self):
    self.ExpectOp()
    self.Run('bigtable app-profiles update my-app-profile '
             '--instance my-instance --description my-description '
             '--route-to my-cluster')
    self.app_profile_update_mock.assert_called_once_with(
        self.app_profile_ref,
        cluster='my-cluster',
        description='my-description',
        multi_cluster=False,
        transactional_writes=False,
        force=False)

  def testUpdateTransactional(self):
    self.ExpectOp()
    self.Run('bigtable app-profiles update my-app-profile '
             '--instance my-instance --description my-description '
             '--route-to my-cluster --transactional-writes')
    self.app_profile_update_mock.assert_called_once_with(
        self.app_profile_ref,
        cluster='my-cluster',
        description='my-description',
        multi_cluster=False,
        transactional_writes=True,
        force=False)

  def testUpdateHATransactionalInvalid(self):
    with self.AssertRaisesArgumentError():
      self.Run('bigtable app-profiles update my-app-profile '
               '--instance my-instance --description my-description '
               '--route-any --transactional-writes')
      self.app_profile_update_mock.assert_not_called()


class AppProfileUpdateTestsBeta(AppProfileUpdateTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class AppProfileUpdateTestsAlpha(AppProfileUpdateTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
