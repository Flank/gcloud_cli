# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Base class for all access context manager tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from six.moves import map


class Base(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
           sdk_test_base.WithLogCapture):
  """Base class for Access Context Manager unit tests."""

  _API_NAME = 'accesscontextmanager'

  def SetUp(self):
    self.client = None
    self.messages = None
    self.StartPatch('time.sleep')  # For calls that poll operations

    # The default account, 'fake_account', won't do because it has no domain.
    properties.VALUES.core.account.Set('user@example.com')

    self.resource_manager_client = mock.Client(
        client_class=apis.GetClientClass('cloudresourcemanager', 'v1'))
    self.resource_manager_client.Mock()
    self.addCleanup(self.resource_manager_client.Unmock)
    self.resource_manager_messages = apis.GetMessagesModule(
        'cloudresourcemanager', 'v1')

  def SetUpForTrack(self, track):
    self.track = track
    api_version = {base.ReleaseTrack.ALPHA: 'v1alpha'}[track]
    self.client = mock.Client(
        client_class=apis.GetClientClass(self._API_NAME, api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(self._API_NAME, api_version)

  LEVEL_SPEC = ('[{"ipSubnetworks": ["127.0.0.1/24"]}, '
                '{"members": ["user:example@example.com"]}]')

  def _ExpectGetOperation(self, name, resource_name=None):
    if resource_name:
      response = encoding.DictToMessage({'name': resource_name},
                                        self.messages.Operation.ResponseValue)
    else:
      response = None

    self.client.operations.Get.Expect(
        self.messages.AccesscontextmanagerOperationsGetRequest(
            name=name,
        ),
        self.messages.Operation(name=name, done=True, response=response))

  def _MakeBasicLevel(self, name, combining_function=None, description=None,
                      title=None):
    m = self.messages
    combining_function_enum = m.BasicLevel.CombiningFunctionValueValuesEnum
    combining_function = combining_function_enum(combining_function)
    return self.messages.AccessLevel(
        basic=self.messages.BasicLevel(
            combiningFunction=combining_function,
            conditions=[
                self.messages.Condition(ipSubnetworks=['127.0.0.1/24']),
                self.messages.Condition(members=['user:example@example.com']),
            ]
        ),
        createTime=None,
        description=description,
        name=name,
        title=title,
        updateTime=None)

  def _MakePerimeter(
      self,
      id_='MY_PERIMTER',
      title='My Perimeter',
      description='Very long description of my service perimeter',
      restricted_services=('storage.googleapis.com',),
      unrestricted_services=('compute.googleapis.com',),
      access_levels=('MY_LEVEL', 'MY_LEVEL_2'),
      resources=('projects/12345', 'projects/67890'),
      type_=None,
      policy='MY_POLICY'):
    if type_:
      type_ = self.messages.AccessZone.ZoneTypeValueValuesEnum(type_)
    return self.messages.AccessZone(
        accessLevels=list(map(
            'accessPolicies/MY_POLICY/accessLevels/{}'.format, access_levels
        )),
        description=description,
        name='accessPolicies/MY_POLICY/accessZones/' + id_,
        resources=resources,
        restrictedServices=restricted_services,
        unrestrictedServices=unrestricted_services,
        title=title,
        zoneType=type_
    )

  def _ExpectListPolicies(self, organization_name, policies):
    if isinstance(policies, Exception):
      response = None
      exception = policies
    else:
      response = self.messages.ListAccessPoliciesResponse(
          accessPolicies=policies
      )
      exception = None

    self.client.accessPolicies.List.Expect(
        self.messages.AccesscontextmanagerAccessPoliciesListRequest(
            parent=organization_name,
        ),
        response,
        exception=exception
    )

  def _ExpectSearchOrganizations(self, filter_, organizations):
    if isinstance(organizations, Exception):
      response = None
      exception = organizations
    else:
      response = self.resource_manager_messages.SearchOrganizationsResponse(
          organizations=organizations
      )
      exception = None

    self.resource_manager_client.organizations.Search.Expect(
        self.resource_manager_messages.SearchOrganizationsRequest(
            filter=filter_,
        ),
        response,
        exception=exception
    )
