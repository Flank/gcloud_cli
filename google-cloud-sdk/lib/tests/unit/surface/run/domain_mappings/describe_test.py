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
from googlecloudsdk.command_lib.run import flags
from tests.lib.surface.run import base


class DomainMappingCreateTest(base.ServerlessSurfaceBase):

  def testDescribe_Succeed(self):
    """Successfully describe a domain mapping."""
    domain_name = 'www.example.com'
    domain_ref = self._DomainmappingRef(domain_name)

    my_mapping = domain_mapping.DomainMapping.New(
        self.mock_serverless_client, domain_ref.namespacesId)
    my_mapping.name = domain_ref.domainmappingsId
    my_mapping.route_name = 'myapp'
    self.operations.GetDomainMapping.return_value = my_mapping

    self.Run('run domain-mappings describe --domain www.example.com')

    self.operations.GetDomainMapping.assert_called_once_with(domain_ref)
    for s in ['spec', 'kind: DomainMapping', 'name: www.example.com',
              'routeName: myapp']:
      self.AssertOutputContains(s)

  def testDescribe_Fail(self):
    """Fail to describe because of wrong domain name."""
    domain_name = 'www.not-mapped.com'
    self.operations.GetDomainMapping.return_value = None
    with self.assertRaises(flags.ArgumentError) as context:
      self.Run('run domain-mappings describe --domain %s' % domain_name)

    self.operations.GetDomainMapping.assert_called_once_with(
        self._DomainmappingRef(domain_name))
    self.assertIn(
        'Cannot find domain mapping for domain name [www.not-mapped.com]',
        str(context.exception))
