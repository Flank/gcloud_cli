# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Unit tests for the `run domain-mappings create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import domain_mapping
from tests.lib.surface.run import base


class DomainMappingCreateTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.domain_name = 'www.example.com'
    self.domain_ref = self._DomainmappingRef(self.domain_name)

    self.domain_mapping = domain_mapping.DomainMapping.New(
        self.mock_serverless_client, self.domain_ref.namespacesId)
    self.domain_mapping.name = self.domain_ref.domainmappingsId
    self.domain_mapping.route_name = 'myapp'
    messages = self.mock_serverless_client.MESSAGES_MODULE
    self.domain_mapping.status.resourceRecords.append(
        messages.ResourceRecord(
            rrdata='216.239.32.21',
            type=messages.ResourceRecord.TypeValueValuesEnum.A))

    self.operations.CreateDomainMapping.return_value = (
        self.domain_mapping.status.resourceRecords)

  def testDomainMappingCreate(self):
    """Create a domain mapping."""

    self.Run(
        'run domain-mappings create --service myapp --domain www.example.com')

    self.operations.CreateDomainMapping.assert_called_once_with(
        self.domain_ref, 'myapp')
    self.AssertOutputContains(
        """RECORD TYPE CONTENTS
        A 216.239.32.21""", normalize_space=True)
