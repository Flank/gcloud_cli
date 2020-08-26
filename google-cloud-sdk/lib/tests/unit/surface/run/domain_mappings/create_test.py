# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions
from tests.lib.surface.run import base
import mock


class DomainMappingCreateTestBeta(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self._SetDomainRef('www.example.com')
    self.launch_stage_changes = mock.NonCallableMock()
    self.StartObjectPatch(
        config_changes,
        'SetLaunchStageAnnotationChange',
        return_value=self.launch_stage_changes)

  def _SetDomainRef(self, domain_name='www.example.com', project=None):
    self.domain_name = domain_name
    if project:
      self.domain_ref = self._DomainmappingRef(self.domain_name, project)
    else:
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
        self.domain_mapping)

  def testDomainMappingCreateVerifiedDomain(self):
    """Create a domain mapping."""

    with mock.patch(
        'googlecloudsdk.api_lib.run.global_methods.GetServerlessClientInstance',
        return_value=self.mock_serverless_client):
      verified_domains = [
          self.mock_serverless_client.MESSAGES_MODULE.AuthorizedDomain(
              id='www.example.com')
      ]
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListVerifiedDomains',
          return_value=verified_domains):
        self.Run('run domain-mappings create '
                 '--service myapp --domain www.example.com')

        self.operations.CreateDomainMapping.assert_called_once_with(
            self.domain_ref, 'myapp', [self.launch_stage_changes], False)
        self.AssertOutputContains(
            """NAME RECORD TYPE CONTENTS
            myapp A 216.239.32.21""",
            normalize_space=True)

  def testDomainMappingCreateUnverifiedDomainRegional(self):
    """Create a domain mapping."""

    with mock.patch(
        'googlecloudsdk.api_lib.run.global_methods.GetServerlessClientInstance',
        return_value=self.mock_serverless_client):
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListVerifiedDomains',
          return_value=[]):
        with self.assertRaises(exceptions.DomainMappingCreationError):
          self.Run('run domain-mappings create '
                   '--service myapp --domain www.example.com')

      verified_domains = [
          self.mock_serverless_client.MESSAGES_MODULE.AuthorizedDomain(
              id='www.not-example.com')
      ]
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListVerifiedDomains',
          return_value=verified_domains):
        with self.assertRaises(exceptions.DomainMappingCreationError):
          self.Run('run domain-mappings create '
                   '--service myapp --domain www.example.com')
        self.AssertErrContains('www.not-example.com')

  def testDomainMappingCreateAlreadyExistsPrompts(self):
    """Create a domain mapping and prompt and try again if its already in use."""

    self.operations.CreateDomainMapping.side_effect = [
        exceptions.DomainMappingAlreadyExistsError(), self.domain_mapping
    ]

    with mock.patch(
        'googlecloudsdk.api_lib.run.global_methods.GetServerlessClientInstance',
        return_value=self.mock_serverless_client):
      verified_domains = [
          self.mock_serverless_client.MESSAGES_MODULE.AuthorizedDomain(
              id='www.example.com')
      ]
      with mock.patch(
          'googlecloudsdk.api_lib.run.global_methods.ListVerifiedDomains',
          return_value=verified_domains):
        self.WriteInput('y\n')
        self.Run('run domain-mappings create '
                 '--service myapp --domain www.example.com')
        self.AssertOutputContains(
            """NAME RECORD TYPE CONTENTS
            myapp A 216.239.32.21""",
            normalize_space=True)

  def testDomainMappingCreateUnverifiedDomainGKE(self):
    """Create a domain mapping."""

    self._SetDomainRef(project='default')

    self.Run('run domain-mappings create '
             '--cluster mycluster --cluster-location mylocation --platform gke '
             '--service myapp --domain www.example.com')

    self.operations.CreateDomainMapping.assert_called_once_with(
        self.domain_ref, 'myapp', [self.launch_stage_changes], False)
    self.AssertOutputContains(
        """NAME RECORD TYPE CONTENTS
        myapp A 216.239.32.21""",
        normalize_space=True)


class DomainMappingCreateTestAlpha(DomainMappingCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
