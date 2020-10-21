# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
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

  def SetUpForAPI(self, api_version):
    self.include_unrestricted_services = {
        'v1alpha': False,
        'v1beta': True,
        'v1': False
    }[api_version]

    self.support_service_filters = {
        'v1alpha': True,
        'v1beta': True,
        'v1': True
    }[api_version]

    self.support_directional_policies = {
        'v1alpha': True,
        'v1beta': False,
        'v1': False
    }[api_version]

    self.client = mock.Client(
        client_class=apis.GetClientClass(self._API_NAME, api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(self._API_NAME, api_version)

  BASIC_LEVEL_SPEC = ('[{"ipSubnetworks": ["127.0.0.1/24"]}, '
                      '{"members": ["user:example@example.com"]}]')

  CUSTOM_LEVEL_SPEC = 'expression: "inIpRange(origin.ip, [\'127.0.0.1/24\']"'

  ACCESS_LEVEL_SPECS_BASIC = """
      [
        {
          "name": "accessPolicies/1234/accessLevels/myLevel1",
          "title": "replacement level 1",
          "description": "level description 1",
          "basic": {
            "conditions": [
                  {"ipSubnetworks": ["127.0.0.1/24"]},
                  {"members": ["user:example@example.com"]}
            ],
            "combiningFunction": "AND"
          }
        },
        {
          "name": "accessPolicies/1234/accessLevels/myLevel2",
          "title": "replacement level 2",
          "description": "level description 2",
          "basic": {
            "conditions": [
              {"ipSubnetworks": ["127.0.0.1/24"]},
              {"members": ["user:example@example.com"]}
            ],
            "combiningFunction": "AND"
          }
        }
      ]
    """

  ACCESS_LEVEL_SPECS_BASIC_CUSTOM = """
      [
        {
          "name": "accessPolicies/1234/accessLevels/myLevel1",
          "title": "replacement level 1",
          "description": "level description 1",
          "basic": {
            "conditions": [
                  {"ipSubnetworks": ["127.0.0.1/24"]},
                  {"members": ["user:example@example.com"]}
            ],
            "combiningFunction": "AND"
          }
        },
        {
          "name": "accessPolicies/1234/accessLevels/myLevel2",
          "title": "replacement level 2",
          "description": "level description 2",
          "custom": {
            "expr": {
              "expression": "inIpRange(origin.ip, ['127.0.0.1/24'])"
            }
          }
        }
      ]
    """

  SERVICE_PERIMETERS_SPECS = """
      [
        {
          "name": "accessPolicies/123/servicePerimeters/myPerimeter1",
          "title": "replacement perimeter 1",
          "description": "Very long description of my service perimeter",
          "status": {
            "resources": [
              "projects/12345",
              "projects/67890"
            ],
            "accessLevels": [
              "accessPolicies/123/accessLevels/MY_LEVEL",
              "accessPolicies/123/accessLevels/MY_LEVEL_2"
            ],
            "restrictedServices": ["storage.googleapis.com"]
          }
        },
        {
          "name": "accessPolicies/123/servicePerimeters/myPerimeter2",
          "title": "replacement perimeter 2",
          "description": "Very long description of my service perimeter",
          "status": {
            "resources": [
              "projects/12345",
              "projects/67890"
            ],
            "accessLevels": [
              "accessPolicies/123/accessLevels/MY_LEVEL",
              "accessPolicies/123/accessLevels/MY_LEVEL_2"
            ],
            "restrictedServices": ["storage.googleapis.com"]
          }
        }
      ]
    """

  INGRESS_POLICIES_SPECS = """
      [
        {
          "ingressFrom": {
            "identities": [
              "user:testUser@google.com"
            ],
            "sources": [
              {
                "accessLevel": "accessPolicies/123/accessLevels/my_level"
              },
              {
                "resource": "projects/123456789"
              }
            ]
          },
          "ingressTo": {
            "operations": [
              {
                "actions": [
                  {
                    "action": "method_for_all",
                    "actionType": "METHOD"
                  },
                  {
                    "action": "method_for_one",
                    "actionType": "METHOD"
                  }
                ],
                "serviceName": "chemisttest.googleapis.com"
              }
            ]
          }
        }
      ]
    """

  EGRESS_POLICIES_SPECS = """
      [
        {
          "egressFrom": {
            "allowedIdentity": "ANY_IDENTITY"
          },
          "egressTo": {
            "operations": [
              {
                "actions": [
                  {
                    "action": "method_for_all",
                    "actionType": "METHOD"
                  },
                  {
                    "action": "method_for_one",
                    "actionType": "METHOD"
                  }
                ],
                "serviceName": "chemisttest.googleapis.com"
              }
            ],
            "resources": [
              "projects/123456789"
            ]
          }
        }
      ]
    """

  def _ExpectGetOperation(self, name, resource_name=None):
    if resource_name:
      response = encoding.DictToMessage({'name': resource_name},
                                        self.messages.Operation.ResponseValue)
    else:
      response = None

    self.client.operations.Get.Expect(
        self.messages.AccesscontextmanagerOperationsGetRequest(name=name,),
        self.messages.Operation(name=name, done=True, response=response))

  def _MakeBasicLevel(self,
                      name,
                      combining_function=None,
                      description=None,
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
            ]),
        description=description,
        name=name,
        title=title)

  def _MakeCustomLevel(self,
                       name,
                       expression=None,
                       description=None,
                       title=None):
    return self.messages.AccessLevel(
        custom=self.messages.CustomLevel(
            expr=self.messages.Expr(expression=expression)),
        description=description,
        name=name,
        title=title)

  def _MakePerimeter(
      self,
      id_='MY_PERIMETER',
      title='My Perimeter',
      description='Very long description of my service perimeter',
      restricted_services=('storage.googleapis.com',),
      unrestricted_services=('*',),
      access_levels=('MY_LEVEL', 'MY_LEVEL_2'),
      resources=('projects/12345', 'projects/67890'),
      type_=None,
      policy='123',
      vpc_allowed_services=None,
      enable_vpc_accessible_services=None,
      dry_run=False,
      ingress_policies=[],
      egress_policies=[]):

    if type_:
      type_ = self.messages.ServicePerimeter.PerimeterTypeValueValuesEnum(type_)

    config = self.messages.ServicePerimeterConfig()

    if access_levels is not None:
      config.accessLevels = access_levels = list(
          map('accessPolicies/123/accessLevels/{}'.format, access_levels))
    if resources is not None:
      config.resources = resources
    if restricted_services is not None:
      config.restrictedServices = restricted_services

    if self.include_unrestricted_services:
      config.unrestrictedServices = unrestricted_services

    if self.support_service_filters:
      self._FillInServiceFilterFields(config, vpc_allowed_services,
                                      enable_vpc_accessible_services)

    if self.support_directional_policies:
      config.ingressPolicies = ingress_policies
      config.egressPolicies = egress_policies

    if not dry_run:
      return self.messages.ServicePerimeter(
          description=description,
          name='accessPolicies/123/servicePerimeters/' + id_,
          title=title,
          perimeterType=type_,
          status=config)
    else:
      return self.messages.ServicePerimeter(
          description=description,
          name='accessPolicies/123/servicePerimeters/' + id_,
          title=title,
          perimeterType=type_,
          useExplicitDryRunSpec=True,
          spec=config)

  def _FillInServiceFilterFields(self, status, vpc_allowed_services,
                                 enable_vpc_accessible_services):
    vpc_config = None
    if vpc_allowed_services is not None:
      if vpc_config is None:
        vpc_config = self.messages.VpcAccessibleServices()
      vpc_config.allowedServices = vpc_allowed_services
    if enable_vpc_accessible_services is not None:
      if vpc_config is None:
        vpc_config = self.messages.VpcAccessibleServices()
      vpc_config.enableRestriction = enable_vpc_accessible_services
    if vpc_config is not None:
      status.vpcAccessibleServices = vpc_config

  def _ExpectListPolicies(self, organization_name, policies):
    if isinstance(policies, Exception):
      response = None
      exception = policies
    else:
      response = self.messages.ListAccessPoliciesResponse(
          accessPolicies=policies)
      exception = None

    self.client.accessPolicies.List.Expect(
        self.messages.AccesscontextmanagerAccessPoliciesListRequest(
            parent=organization_name,),
        response,
        exception=exception)

  def _ExpectSearchOrganizations(self, filter_, organizations):
    if isinstance(organizations, Exception):
      response = None
      exception = organizations
    else:
      response = self.resource_manager_messages.SearchOrganizationsResponse(
          organizations=organizations)
      exception = None

    self.resource_manager_client.organizations.Search.Expect(
        self.resource_manager_messages.SearchOrganizationsRequest(
            filter=filter_,),
        response,
        exception=exception)

  def _MakeIngressPolicies(self):
    source1 = self.messages.IngressSource(
        accessLevel='accessPolicies/123/accessLevels/my_level')
    source2 = self.messages.IngressSource(resource='projects/123456789')
    ingress_from = self.messages.IngressFrom(
        identities=['user:testUser@google.com'], sources=[source1, source2])
    method_type = self.messages.ApiAction.ActionTypeValueValuesEnum('METHOD')
    action1 = self.messages.ApiAction(
        action='method_for_all', actionType=method_type)
    action2 = self.messages.ApiAction(
        action='method_for_one', actionType=method_type)
    operation1 = self.messages.ApiOperation(
        serviceName='chemisttest.googleapis.com', actions=[action1, action2])
    ingress_to = self.messages.IngressTo(operations=[operation1])
    return [
        self.messages.IngressPolicy(
            ingressFrom=ingress_from, ingressTo=ingress_to)
    ]

  def _MakeEgressPolicies(self):
    allowed_identity_any = self.messages.EgressFrom.AllowedIdentityValueValuesEnum(
        'ANY_IDENTITY')
    egress_from = self.messages.EgressFrom(allowedIdentity=allowed_identity_any)
    method_type = self.messages.ApiAction.ActionTypeValueValuesEnum('METHOD')
    action1 = self.messages.ApiAction(
        action='method_for_all', actionType=method_type)
    action2 = self.messages.ApiAction(
        action='method_for_one', actionType=method_type)
    operation1 = self.messages.ApiOperation(
        serviceName='chemisttest.googleapis.com', actions=[action1, action2])
    egress_to = self.messages.EgressTo(
        operations=[operation1], resources=['projects/123456789'])
    return [
        self.messages.EgressPolicy(egressFrom=egress_from, egressTo=egress_to)
    ]

  def _MakeGcpUserAccessBinding(self, access_level, group_key=None, name=None):
    return self.messages.GcpUserAccessBinding(
        name=name, groupKey=group_key, accessLevels=[access_level])
