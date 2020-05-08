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
"""Base class for all SSL certificates tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class SslCertificatesTestBase(e2e_test_base.BaseTest):
  """Base class for all SslCertificates tests."""

  def UniqueName(self):
    return next(e2e_utils.GetResourceNameGenerator(
        prefix='compute-ssl-certificate-test'))

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(False)
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.certificate = self.messages.SslCertificate
    self.managed = self.messages.SslCertificateManagedSslCertificate
    self.ssl_cert_names = []

  def TearDown(self):
    for name in self.ssl_cert_names:
      self.CleanUpResource(name, 'ssl-certificates', scope=e2e_test_base.GLOBAL)

  def _AdditionalProperty(self, key, value):
    dsv = self.managed.DomainStatusValue
    return dsv.AdditionalProperty(
        key=key,
        value=dsv.AdditionalProperty.ValueValueValuesEnum(value))

  def DictToCert(self, d):
    """Builds messages.SslCertificate from dict returned by gcloud list."""

    # Each element in d is string and need to be converted to proper type.
    d['id'] = int(d['id'])
    d['type'] = self.messages.SslCertificate.TypeValueValuesEnum(d['type'])
    if 'managed' in d:
      m = d['managed']
      m['status'] = self.managed.StatusValueValuesEnum(m['status'])
      m['domainStatus'] = self.managed.DomainStatusValue(
          additionalProperties=[
              self._AdditionalProperty(domain, m['domainStatus'][domain])
              for domain in m['domainStatus']])
    return self.messages.SslCertificate(**d)
