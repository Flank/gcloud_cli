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
"""Tests for googlecloudsdk.api_lib.accesscontextmanager.zones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib.surface import accesscontextmanager


class FakePerimeterRef(object):

  def RelativeName(self):
    return 'SOME_PERIMETER'


class ZonesTest(accesscontextmanager.Base):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _ExpectGet(self, name):
    m = self.messages
    get_req_type = (
        m.AccesscontextmanagerAccessPoliciesServicePerimetersGetRequest)
    self.client.accessPolicies_servicePerimeters.Get.Expect(
        get_req_type(name=name), {})

  def _ExpectPatch(self, perimeter_ref, perimeter_update, update_mask):
    perimeter_name = perimeter_ref.RelativeName()
    m = self.messages
    req_type = m.AccesscontextmanagerAccessPoliciesServicePerimetersPatchRequest
    self.client.accessPolicies_servicePerimeters.Patch.Expect(
        req_type(
            name=perimeter_name,
            servicePerimeter=perimeter_update,
            updateMask=update_mask),
        self.messages.Operation(name='operations/my-op', done=False))
    self._ExpectGetOperation('operations/my-op')
    self._ExpectGet(perimeter_name)

  def testPatchDryRunConfig(self):
    self.SetUpForAPI(self.api_version)
    client = zones.Client(self.client)
    perimeter_update = self.messages.ServicePerimeter(
        useExplicitDryRunSpec=True,
        spec=self.messages.ServicePerimeterConfig(
            resources=['projects/123', 'projects/456'],
            restrictedServices=['bigquery.googleapis.com']))
    perimeter_ref = FakePerimeterRef()
    self._ExpectPatch(
        perimeter_ref, perimeter_update,
        'spec.resources,spec.restrictedServices,useExplicitDryRunSpec')

    client.PatchDryRunConfig(
        perimeter_ref,
        resources=['projects/123', 'projects/456'],
        restricted_services=['bigquery.googleapis.com'])

  def testUnsetSpec_unsetUseExplictDryRunSpecFlag(self):
    self.SetUpForAPI(self.api_version)
    client = zones.Client(self.client)
    perimeter_update = self.messages.ServicePerimeter(
        useExplicitDryRunSpec=False, spec=None)
    perimeter_ref = FakePerimeterRef()
    self._ExpectPatch(perimeter_ref, perimeter_update,
                      'spec,useExplicitDryRunSpec')
    client.UnsetSpec(perimeter_ref, False)

  def testUnsetSpec_setUseExplictDryRunSpecFlag(self):
    self.SetUpForAPI(self.api_version)
    client = zones.Client(self.client)
    perimeter_update = self.messages.ServicePerimeter(
        useExplicitDryRunSpec=True, spec=None)
    perimeter_ref = FakePerimeterRef()
    self._ExpectPatch(perimeter_ref, perimeter_update,
                      'spec,useExplicitDryRunSpec')
    client.UnsetSpec(perimeter_ref, True)
