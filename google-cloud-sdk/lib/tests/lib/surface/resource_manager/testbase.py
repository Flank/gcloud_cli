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
"""Base classes for all folders tests."""

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.resource_manager import folders
from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error

_URL_ROOT = 'http://cloudresourcemanager.googleapis.com/v2alpha1/folders/'
_BAD_ID_URL = _URL_ROOT + 'BAD_ID?someParam=true&other=false'
_SECRET_ID_URL = _URL_ROOT + 'SECRET_ID?someParam=true&other=false'

HTTP_403_ERR = http_error.MakeHttpError(403, url=_SECRET_ID_URL)
HTTP_404_ERR = http_error.MakeHttpError(404, url=_BAD_ID_URL)


class CrmUnitTestBase(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):
  """Base class for all CRM unit tests with fake auth and mocks."""

  def Project(self):
    return None

  def SetUp(self):
    self.mock_folders = self._SetUpMockCrmClient(
        folders.FOLDERS_API_VERSION).folders
    mock_v1 = self._SetUpMockCrmClient('v1')
    self.mock_operations = mock_v1.operations
    self.mock_liens = mock_v1.liens

  def _SetUpMockCrmClient(self, version):
    client = mock.Client(
        apis.GetClientClass('cloudresourcemanager', version),
        real_client=apis.GetClientInstance(
            'cloudresourcemanager', version, no_http=True))
    client.Mock()
    self.addCleanup(client.Unmock)
    return client


class FoldersUnitTestBase(CrmUnitTestBase):
  """Base class for all Folders unit tests with fake auth and mocks."""

  messages = folders.FoldersMessages()

  ACTIVE = messages.Folder.LifecycleStateValueValuesEnum.ACTIVE
  DELETED = messages.Folder.LifecycleStateValueValuesEnum.DELETE_REQUESTED

  TEST_FOLDER = messages.Folder(
      name=u'folders/58219052',
      parent=u'organizations/24521',
      displayName=u'Test Folder For Testing',
      lifecycleState=ACTIVE)

  ANOTHER_TEST_FOLDER = messages.Folder(
      name=u'folders/67045082',
      parent=u'organizations/24521',
      displayName=u'Another Test Folder For Testing',
      lifecycleState=ACTIVE)

  UPDATED_TEST_FOLDER = messages.Folder(
      name=u'folders/58219052',
      parent=u'organizations/24521',
      displayName=u'Test Folder Updated To Be More Awesome',
      lifecycleState=ACTIVE)

  DELETED_TEST_FOLDER = messages.Folder(
      name=u'folders/58219052',
      parent=u'organizations/24521',
      displayName=u'Test Folder For Testing',
      lifecycleState=DELETED)

  TEST_FOLDER_WITH_FOLDER_PARENT = messages.Folder(
      name=u'folders/58219052',
      parent=u'folders/12345',
      displayName=u'Test Folder For Testing',
      lifecycleState=ACTIVE)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _GetTestIamPolicy(self, clear_fields=None):
    """Creates a test IAM policy.

    Args:
        clear_fields: list of policy fields to clear.
    Returns:
        IAM policy.
    """
    policy = self.messages.Policy(
        auditConfigs=[
            self.messages.AuditConfig(
                auditLogConfigs=[
                    self.messages.AuditLogConfig(
                        logType=self.messages.AuditLogConfig.
                        LogTypeValueValuesEnum.ADMIN_READ,),
                ],
                service=u'allServices',)
        ],
        bindings=[
            self.messages.Binding(
                role=u'roles/resourcemanager.projectCreator',
                members=[u'domain:foo.com'],),
            self.messages.Binding(
                role=u'roles/resourcemanager.organizationAdmin',
                members=[u'user:admin@foo.com'],),
        ],
        etag='someUniqueEtag',
        version=1,)

    if clear_fields is None:
      clear_fields = []

    for field in clear_fields:
      policy.reset(field)

    return policy

  def RunFolders(self, *command):
    return self.Run(['resource-manager', 'folders'] + list(command))


class OperationsUnitTestBase(CrmUnitTestBase):
  """Base class for all Operations unit tests with fake auth and mocks."""

  TEST_OPERATION = operations.OperationsMessages().Operation(
      name=u'operations/fc.58219052', done=False)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def RunOperations(self, *command):
    return self.Run(['resource-manager', 'operations'] + list(command))


class LiensUnitTestBase(CrmUnitTestBase):
  """Base class for all Liens unit tests with fake auth and mocks."""

  def SetUp(self):
    self.test_lien = liens.LiensMessages().Lien(
        name=u'liens/p1234-abc',
        origin=u'unittest.googlecloudsdk',
        reason=u'player\' gotta play',
        restrictions=[u'resourcemanager.projects.delete'])

  def RunLiens(self, *command):
    return self.Run(['alpha', 'resource-manager', 'liens'] + list(command))


class OrgPoliciesUnitTestBase(cli_test_base.CliTestBase,
                              sdk_test_base.WithFakeAuth):
  """Base class for all Org Policies unit tests with fake auth and mocks."""

  PROJECT_ARG = ['--project', 'test-project']
  ORG_ARG = ['--organization', 'test-org']
  FOLDER_ARG = ['--folder', 'test-folder']
  WRONG_ARG = ['--No-SuCh-FlAg', 'no-such-flag']

  messages = org_policies.OrgPoliciesMessages()

  VALUE_ZERO = 'valueZero'
  VALUE_A = 'valueA'
  VALUE_B = 'valueB'
  ORIGINAL_VALUES = [VALUE_ZERO]
  NEW_VALUES = [VALUE_ZERO, VALUE_A, VALUE_B]
  WHITELIST_CONSTRAINT = 'constraints/goodService.betterWhitelist'
  BLACKLIST_CONSTRAINT = 'constraints/goodService.betterBlacklist'
  TEST_CONSTRAINT = 'constraints/goodService.betterFeatureOne'

  def SetUp(self):
    mock_client = self._SetUpMockCrmClient(
        org_policies.ORG_POLICIES_API_VERSION)
    self.mock_projects = mock_client.projects
    self.mock_organizations = mock_client.organizations
    self.mock_folders = mock_client.folders

  def _SetUpMockCrmClient(self, version):
    client = mock.Client(
        apis.GetClientClass('cloudresourcemanager', version),
        real_client=apis.GetClientInstance(
            'cloudresourcemanager', version, no_http=True))
    client.Mock()
    self.addCleanup(client.Unmock)
    return client

  def RunOrgPolicies(self, *command):
    return self.Run(['beta', 'resource-manager', 'org-policies'] +
                    list(command))

  def ExpectedSetRequest(self, arg, policy):
    msg = self.messages
    if arg == self.PROJECT_ARG:
      return msg.CloudresourcemanagerProjectsSetOrgPolicyRequest(
          projectsId=self.PROJECT_ARG[1],
          setOrgPolicyRequest=msg.SetOrgPolicyRequest(policy=policy))
    elif arg == self.ORG_ARG:
      return msg.CloudresourcemanagerOrganizationsSetOrgPolicyRequest(
          organizationsId=self.ORG_ARG[1],
          setOrgPolicyRequest=msg.SetOrgPolicyRequest(policy=policy))
    elif arg == self.FOLDER_ARG:
      return msg.CloudresourcemanagerFoldersSetOrgPolicyRequest(
          foldersId=self.FOLDER_ARG[1],
          setOrgPolicyRequest=msg.SetOrgPolicyRequest(policy=policy))

  def ExpectedGetRequest(self, arg, constraint):
    msg = self.messages
    if arg == self.PROJECT_ARG:
      return msg.CloudresourcemanagerProjectsGetOrgPolicyRequest(
          projectsId=self.PROJECT_ARG[1],
          getOrgPolicyRequest=msg.GetOrgPolicyRequest(constraint=constraint))
    elif arg == self.ORG_ARG:
      return msg.CloudresourcemanagerOrganizationsGetOrgPolicyRequest(
          organizationsId=self.ORG_ARG[1],
          getOrgPolicyRequest=msg.GetOrgPolicyRequest(constraint=constraint))
    elif arg == self.FOLDER_ARG:
      return msg.CloudresourcemanagerFoldersGetOrgPolicyRequest(
          foldersId=self.FOLDER_ARG[1],
          getOrgPolicyRequest=msg.GetOrgPolicyRequest(constraint=constraint))

  def TestPolicy(self):
    return self.messages.OrgPolicy(
        constraint=self.TEST_CONSTRAINT,
        booleanPolicy=self.messages.BooleanPolicy(enforced=True))

  def WhitelistPolicy(self, allowed_values):
    return self.messages.OrgPolicy(
        constraint=self.WHITELIST_CONSTRAINT,
        listPolicy=self.messages.ListPolicy(allowedValues=allowed_values))

  def AllowAllPolicy(self):
    return self.messages.OrgPolicy(
        constraint=self.WHITELIST_CONSTRAINT,
        listPolicy=self.messages.ListPolicy(
            allValues=self.messages.ListPolicy.AllValuesValueValuesEnum.ALLOW))

  def BlacklistPolicy(self, denied_values):
    return self.messages.OrgPolicy(
        constraint=self.BLACKLIST_CONSTRAINT,
        listPolicy=self.messages.ListPolicy(deniedValues=denied_values))

  def DenyAllPolicy(self):
    return self.messages.OrgPolicy(
        constraint=self.BLACKLIST_CONSTRAINT,
        listPolicy=self.messages.ListPolicy(
            allValues=self.messages.ListPolicy.AllValuesValueValuesEnum.DENY))
