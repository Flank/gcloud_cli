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
"""Tests for gcloud app domain-mappings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib.surface.app import domain_mappings_base


class DomainMappingsCommandTest(domain_mappings_base.DomainMappingsBase):

  def testCreateDomainMapping(self):
    self.ExpectCreateDomainMapping('*.example.com', '1', 'MANUAL')
    self.Run("""app domain-mappings create
                *.example.com --certificate-id=1""")
    self.AssertErrContains('Created [*.example.com].')

  def testCreateDomainMapping_manualManagement(self):
    self.ExpectCreateDomainMapping('*.example.com', '1', 'MANUAL')
    self.Run("""app domain-mappings create
                *.example.com --certificate-id=1
                --certificate-management=MANUAL""")
    self.AssertErrContains('Created [*.example.com].')

  def testCreateDomainMapping_default_autoManagement(self):
    self.ExpectCreateDomainMapping('example.com', None, 'AUTOMATIC')
    self.Run('app domain-mappings create example.com')
    self.AssertErrContains('Created [example.com].')

  def testCreateDomainMapping_autoManagement(self):
    self.ExpectCreateDomainMapping('example.com', None, 'AUTOMATIC')
    self.Run("""app domain-mappings create
                example.com --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Created [example.com].')

  def testCreateDomainMappingNoManagementSpecified_autoManagement(self):
    self.ExpectCreateDomainMapping('example.com', None, 'AUTOMATIC')
    self.Run("""app domain-mappings create example.com""")
    self.AssertErrContains('Created [example.com].')

  def testCreateDomainMapping_autoManagementFailsWithCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings create
                  *.example.com --certificate-id=1
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [certificate-id]')


class DomainMappingsBetaCommandTest(domain_mappings_base.DomainMappingsBase):
  APPENGINE_API_VERSION = 'v1beta'

  def testCreateDomainMapping(self):
    self.ExpectCreateDomainMapping('*.example.com', '1', 'MANUAL')
    self.Run("""beta app domain-mappings create
                *.example.com --certificate-id=1""")
    self.AssertErrContains('Created [*.example.com].')
