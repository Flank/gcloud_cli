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
"""Tests for gcloud app domain-mappings."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib.surface.app import domain_mappings_base


class DomainMappingsListTest(domain_mappings_base.DomainMappingsBase):

  def testListDomainMappings(self):
    mappings = [
        self.MakeDomainMapping('*.example.com', '1',
                               self._ManagementTypeFromString('MANUAL')),
        self.MakeDomainMapping('example2.com', '2',
                               self._ManagementTypeFromString('AUTOMATIC')),
        self.MakeDomainMapping('example3.com', '3',
                               self._ManagementTypeFromString('AUTOMATIC')),
    ]

    self.ExpectListDomainMappings(mappings)
    self.Run('app domain-mappings list')
    self.AssertOutputEquals(
        """\
        ID            SSL_CERTIFICATE_ID  SSL_MANAGEMENT_TYPE  PENDING_AUTO_CERT
        *.example.com   1                   MANUAL
        example2.com    2                   AUTOMATIC
        example3.com    3                   AUTOMATIC
        """,
        normalize_space=True)


class DomainMappingsListBetaTest(domain_mappings_base.DomainMappingsBase):
  APPENGINE_API_VERSION = 'v1beta'

  def testListDomainMappings(self):
    mappings = [
        self.MakeDomainMapping('*.example.com', '1',
                               self._ManagementTypeFromString('MANUAL')),
        self.MakeDomainMapping('example2.com', '2',
                               self._ManagementTypeFromString('AUTOMATIC')),
        self.MakeDomainMapping('example3.com', '3', None),
    ]

    self.ExpectListDomainMappings(mappings)
    self.Run('beta app domain-mappings list')
    self.AssertOutputEquals(
        """\
        ID            SSL_CERTIFICATE_ID  SSL_MANAGEMENT_TYPE  PENDING_AUTO_CERT
        *.example.com   1                   MANUAL
        example2.com    2                   AUTOMATIC
        example3.com    3                   AUTOMATIC
        """,
        normalize_space=True)
