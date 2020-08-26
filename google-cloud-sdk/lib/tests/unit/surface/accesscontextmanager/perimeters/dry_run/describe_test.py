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

    directional_policies_diff = ''
    if self.api_version == 'v1alpha':
      directional_policies_diff = """\
IngressPolicies:
   NONE
EgressPolicies:
   NONE
"""
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
""" + directional_policies_diff)


class DryRunDescribeTestAlpha(DryRunDescribeTestBeta):

  def PreSetUp(self):
    self.api_version = 'v1alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _MakeDryRunIngressPolicies(self):
    source1 = self.messages.IngressSource(
        accessLevel='accessPolicies/123/accessLevels/my_other_level')
    source2 = self.messages.IngressSource(resource='projects/234567890')
    ingress_from = self.messages.IngressFrom(
        identities=['user:testUser2@google.com'], sources=[source1, source2])
    method_type = self.messages.ApiAction.ActionTypeValueValuesEnum(
        'PERMISSION')
    action1 = self.messages.ApiAction(
        action='bigquery.jobs.update', actionType=method_type)
    action2 = self.messages.ApiAction(
        action='bigquery.datasets.create', actionType=method_type)
    operation1 = self.messages.ApiOperation(
        serviceName='bigquery.googleapis.com', actions=[action1, action2])
    ingress_to = self.messages.IngressTo(operations=[operation1])
    return [self.messages.IngressPolicy(
            ingressFrom=ingress_from, ingressTo=ingress_to)]


  def _MakeDryRunEgressPolicies(self):
    method_type = self.messages.ApiAction.ActionTypeValueValuesEnum('METHOD')
    permission_type = self.messages.ApiAction.ActionTypeValueValuesEnum(
        'PERMISSION')
    action1 = self.messages.ApiAction(
        action='TableDataService.List', actionType=method_type)
    action2 = self.messages.ApiAction(
        action='bigquery.datasets.create', actionType=permission_type)
    operation1 = self.messages.ApiOperation(
        serviceName='bigquery.googleapis.com', actions=[action1, action2])
    egress_to = self.messages.EgressTo(
        operations=[operation1], resources=['projects/234567890'])
    return [self.messages.EgressPolicy(egressTo=egress_to)]

  def testDescribeDirectionalPolicies_SingeleDifference(self):
    self.SetUpForAPI(self.api_version)
    perimeter_with_status = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=None,
        access_levels=None,
        ingress_policies=self._MakeIngressPolicies(),
        egress_policies=self._MakeEgressPolicies(),
        restricted_services=None)

    perimeter_with_spec = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=None,
        access_levels=None,
        restricted_services=None,
        ingress_policies=self._MakeDryRunIngressPolicies(),
        egress_policies=self._MakeDryRunEgressPolicies(),
        dry_run=True)
    final_perimeter = perimeter_with_spec
    final_perimeter.status = perimeter_with_status.status

    self._ExpectGet(final_perimeter)

    self.Run('access-context-manager perimeters dry-run describe MY_PERIMETER'
             '   --policy 123')

    base_diff = """\
name: MY_PERIMETER
title: Perimeter 1
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
   NONE
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
"""
    ingress_policies_diff = """\
IngressPolicies:
   ingressFrom:
     identities:
      -user:testUser@google.com
      +user:testUser2@google.com
     sources:
      -accessLevel: accessPolicies/123/accessLevels/my_level
      +accessLevel: accessPolicies/123/accessLevels/my_other_level
      -resource: projects/123456789
      +resource: projects/234567890
   ingressTo:
     operations:
       actions:
        -action: method_for_all
        +action: bigquery.jobs.update
        -actionType: METHOD
        +actionType: PERMISSION
        -action: method_for_one
        +action: bigquery.datasets.create
        -actionType: METHOD
        +actionType: PERMISSION
      -serviceName: chemisttest.googleapis.com
      +serviceName: bigquery.googleapis.com
"""
    egress_policies_diff = """\
EgressPolicies:
  -egressFrom:
    -allowedIdentity: ANY_IDENTITY
   egressTo:
     operations:
       actions:
        -action: method_for_all
        +action: TableDataService.List
         actionType: METHOD
        -action: method_for_one
        +action: bigquery.datasets.create
        -actionType: METHOD
        +actionType: PERMISSION
      -serviceName: chemisttest.googleapis.com
      +serviceName: bigquery.googleapis.com
     resources:
      -projects/123456789
      +projects/234567890
"""
    self.AssertOutputEquals(base_diff + ingress_policies_diff + '  \n' +
                            egress_policies_diff + '  \n')

  def testDescribeDirectionalPolicies_MultipleDifferences(self):
    self.SetUpForAPI(self.api_version)
    perimeter_with_status = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=None,
        access_levels=None,
        ingress_policies=self._MakeIngressPolicies(),
        egress_policies=self._MakeEgressPolicies(),
        restricted_services=None)

    perimeter_with_spec = self._MakePerimeter(
        'MY_PERIMETER',
        title='Perimeter 1',
        resources=None,
        access_levels=None,
        restricted_services=None,
        ingress_policies=self._MakeIngressPolicies() + self._MakeDryRunIngressPolicies(),
        egress_policies=self._MakeEgressPolicies() + self._MakeDryRunEgressPolicies(),
        dry_run=True)
    final_perimeter = perimeter_with_spec
    final_perimeter.status = perimeter_with_status.status

    self._ExpectGet(final_perimeter)

    self.Run('access-context-manager perimeters dry-run describe MY_PERIMETER'
             '   --policy 123')

    base_diff = """\
name: MY_PERIMETER
title: Perimeter 1
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
   NONE
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
"""
    ingress_policies_diff = """\
IngressPolicies:
   ingressFrom:
     identities:
       user:testUser@google.com
     sources:
       accessLevel: accessPolicies/123/accessLevels/my_level
       resource: projects/123456789
   ingressTo:
     operations:
       actions:
         action: method_for_all
         actionType: METHOD
         action: method_for_one
         actionType: METHOD
       serviceName: chemisttest.googleapis.com
  +ingressFrom:
    +identities:
      +user:testUser2@google.com
    +sources:
      +accessLevel: accessPolicies/123/accessLevels/my_other_level
      +resource: projects/234567890
  +ingressTo:
    +operations:
      +actions:
        +action: bigquery.jobs.update
        +actionType: PERMISSION
        +action: bigquery.datasets.create
        +actionType: PERMISSION
      +serviceName: bigquery.googleapis.com
"""
    egress_policies_diff = """\
EgressPolicies:
   egressFrom:
     allowedIdentity: ANY_IDENTITY
   egressTo:
     operations:
       actions:
         action: method_for_all
         actionType: METHOD
         action: method_for_one
         actionType: METHOD
       serviceName: chemisttest.googleapis.com
     resources:
       projects/123456789
  +egressTo:
    +operations:
      +actions:
        +action: TableDataService.List
        +actionType: METHOD
        +action: bigquery.datasets.create
        +actionType: PERMISSION
      +serviceName: bigquery.googleapis.com
    +resources:
      +projects/234567890
"""
    self.AssertOutputEquals(base_diff + ingress_policies_diff + '  \n' +
                            egress_policies_diff + '  \n')

if __name__ == '__main__':
  test_case.main()
