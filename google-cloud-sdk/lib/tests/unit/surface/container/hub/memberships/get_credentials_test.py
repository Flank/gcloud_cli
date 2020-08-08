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
"""Tests for tests.unit.surface.container.hub.memberships.get_credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.hub import api_util as hubapi_util
from googlecloudsdk.command_lib.container.hub import gwkubeconfig_util as kconfig
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import config as core_config
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.container.hub.memberships import base

FAKE_SDK_BIN_PATH = os.path.join('fake', 'bin', 'path')
TEST_PROJECT_ID = 'fake-project'
TEST_PROJECT_NUMBER = 12321
TEST_MEMBERSHIP = 'my-cluster'
ALPHA_EXPECTED_KUBECONFIG = """apiVersion: v1
clusters:
- cluster:
    server: https://connectgateway.googleapis.com/v1alpha1/projects/12321/memberships/my-cluster
  name: connectgateway_fake-project_my-cluster
contexts:
- context:
    cluster: connectgateway_fake-project_my-cluster
    user: connectgateway_fake-project_my-cluster
  name: connectgateway_fake-project_my-cluster
current-context: connectgateway_fake-project_my-cluster
kind: Config
preferences: {}
users:
- name: connectgateway_fake-project_my-cluster
  user:
    auth-provider:
      config:
        cmd-args: config config-helper --format=json
        cmd-path: fake/bin/path/gcloud
        expiry-key: '{.credential.token_expiry}'
        token-key: '{.credential.access_token}'
      name: gcp
"""


class GetCredentialsTestAlpha(base.MembershipsTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    fake_bin_path = self.StartPropertyPatch(core_config.Paths, 'sdk_bin_path')
    fake_bin_path.return_value = FAKE_SDK_BIN_PATH
    self.name = 'projects/{project_id}/locations/global/memberships/{membership}'.format(
        project_id=TEST_PROJECT_ID, membership=TEST_MEMBERSHIP)
    self.description = TEST_MEMBERSHIP
    self.test_id = 'fake-uid'

  @test_case.Filters.DoNotRunOnWindows
  def testGetCredentialsNormalCase(self):
    # set up mocking for IAM checking
    required_permissions = [
        'gkehub.memberships.get',
        'gkehub.gateway.get',
    ]
    self.SetUpIamMocking(required_permissions)
    # set up mocking for GetMembership
    mock_get_membership = self.StartObjectPatch(hubapi_util, 'GetMembership')
    membership = self._MakeMembership(
        name=self.name, description=self.description, external_id=self.test_id)
    mock_get_membership.return_value = membership
    self.StartObjectPatch(
        project_util, 'GetProjectNumber', return_value=TEST_PROJECT_NUMBER)
    # run register command for the membership
    self.RunCommand([TEST_MEMBERSHIP])

    # check the generated kubeconfig content
    path = kconfig.Kubeconfig.DefaultPath()
    with open(path, 'r') as fp:
      self.assertEqual(fp.read(), ALPHA_EXPECTED_KUBECONFIG)

  @test_case.Filters.DoNotRunOnWindows
  def testGetCredentialsNormalCaseForAutopush(self):
    # set up mocking for IAM checking
    required_permissions = [
        'gkehub.memberships.get',
        'gkehub.gateway.get',
    ]
    self.SetUpIamMocking(required_permissions)
    # set up mocking for GetMembership
    mock_get_membership = self.StartObjectPatch(hubapi_util, 'GetMembership')
    membership = self._MakeMembership(
        name=self.name, description=self.description, external_id=self.test_id)
    mock_get_membership.return_value = membership
    self.StartObjectPatch(
        project_util, 'GetProjectNumber', return_value=TEST_PROJECT_NUMBER)
    # set up endpoints overridding
    properties.PersistProperty(
        properties.VALUES.api_endpoint_overrides.gkehub,
        'https://autopush-gkehub.sandbox.googleapis.com/')
    # run register command for the membership
    self.RunCommand([TEST_MEMBERSHIP])

    expected_kubeconfig_autopush = ALPHA_EXPECTED_KUBECONFIG.replace(
        'connectgateway.googleapis.com',
        'autopush-connectgateway.sandbox.googleapis.com')
    # check the generated kubeconfig content
    path = kconfig.Kubeconfig.DefaultPath()
    with open(path, 'r') as fp:
      self.assertEqual(fp.read(), expected_kubeconfig_autopush)

  def testGetCredentialsNonExistingMembership(self):
    # set up mocking for IAM checking
    required_permissions = [
        'gkehub.memberships.get',
        'gkehub.gateway.get',
    ]
    self.SetUpIamMocking(required_permissions)
    # set up mocking for GetMembership: NotFound
    mock_get_membership = self.StartObjectPatch(hubapi_util, 'GetMembership')
    mock_get_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)
    with self.assertRaises(calliope_exceptions.HttpException):
      self.RunCommand(['non-exist-membership'])

  def testGetCredentialsIAMCheckFail(self):
    # set up mocking for IAM checking
    self.SetUpIamMocking([])  # empty permission
    with self.AssertRaisesExceptionMatches(
        Exception, 'caller doesn\'t have sufficient permission'):
      self.RunCommand([TEST_MEMBERSHIP])

  def RunCommand(self, params):
    """Runs the 'get-credentials' command with the provided params.

    Args:
      params: A list of parameters to pass to the 'get-credentials' command.

    Returns:
      The results of self.Run() with the provided params.

    Raises:
      Any exception raised by self.Run()
    """
    prefix = ['container', 'hub', 'memberships', 'get-credentials']
    return self.Run(prefix + params)

  def SetUpIamMocking(self, permissions):
    mock_test_permission = self.StartObjectPatch(projects_api,
                                                 'TestIamPermissions')
    messages = core_apis.GetMessagesModule('cloudresourcemanager', 'v1')
    mock_test_permission.return_value = messages.TestIamPermissionsResponse(
        permissions=permissions)
