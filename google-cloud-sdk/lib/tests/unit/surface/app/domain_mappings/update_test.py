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


class DomainMappingsUpdateTest(domain_mappings_base.DomainMappingsBase):

  def testUpdateDomainMapping(self):
    self.ExpectUpdateDomainMapping(
        '*.example.com', '1234', 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('app domain-mappings update *.example.com --certificate-id=1234')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_managed(self):
    self.ExpectUpdateDomainMapping(
        '*.example.com', '1234', 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('app domain-mappings update *.example.com --certificate-id=1234')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_clearCert(self):
    self.ExpectUpdateDomainMapping(
        '*.example.com', None, 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('app domain-mappings update *.example.com --no-certificate-id')
    self.AssertErrContains('Updated [*.example.com].')

  def testUpdateDomainMapping_autoManagementFailsWithCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update
                  *.example.com --certificate-id=1
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [certificate-id]')

  def testUpdateDomainMapping_autoManagementFailsWithNoCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update
                  *.example.com --no-certificate-id
                  --certificate-management=AUTOMATIC""")
    self.AssertErrContains('Invalid value for [no-certificate-id]')

  def testUpdateDomainMapping_manualManagementFailsWithNoCert(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.Run("""app domain-mappings update *.example.com
                  --certificate-management=MANUAL""")
    self.AssertErrContains('Invalid value for [certificate-id]')


class DomainMappingsUpdateBetaTest(domain_mappings_base.DomainMappingsBase):
  APPENGINE_API_VERSION = 'v1beta'

  def testUpdateDomainMapping(self):
    self.ExpectUpdateDomainMapping(
        '*.example.com', '1234', 'MANUAL',
        'sslSettings.certificateId,sslSettings.sslManagementType')
    self.Run('beta app domain-mappings update *.example.com '
             '--certificate-id=1234')
    self.AssertErrContains('Updated [*.example.com].')
