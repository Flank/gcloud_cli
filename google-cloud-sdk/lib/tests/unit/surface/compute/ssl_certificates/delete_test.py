# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the SSL certificates delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SslCertificatesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self.prefix = ''
    self._compute_api = self.compute_v1.sslCertificates

  def RunDelete(self, command):
    self.Run(self.prefix + ' compute ssl-certificates delete ' + command)

  def testWithSingleNetwork(self):
    messages = self.messages
    self.RunDelete('cert-1 --quiet')

    self.CheckRequests(
        [(self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-1',
              project='my-project'))],
    )

  def testWithManyCertificates(self):
    messages = self.messages
    self.RunDelete('cert-1 cert-2 cert-3 --quiet')

    self.CheckRequests(
        [(self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-1',
              project='my-project')),

         (self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-2',
              project='my-project')),

         (self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.RunDelete('cert-1 cert-2 cert-3')

    self.CheckRequests(
        [(self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-1',
              project='my-project')),

         (self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-2',
              project='my-project')),

         (self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('cert-1 cert-2 cert-3')

    self.CheckRequests()

  def testWithSingleNetworkRegion(self):
    messages = self.messages
    self.RunDelete('--region us-west-1 cert-1 --quiet')

    self.CheckRequests([
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-1', project='my-project', region='us-west-1'))
    ],)

  def testWithManyCertificatesRegion(self):
    messages = self.messages
    self.RunDelete('--region us-west-1 cert-1 cert-2 cert-3 --quiet')

    self.CheckRequests([
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-1', project='my-project',
             region='us-west-1')),
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-2', project='my-project',
             region='us-west-1')),
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-3', project='my-project', region='us-west-1'))
    ],)

  def testPromptingWithYesRegion(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.RunDelete('--region us-west-1 cert-1 cert-2 cert-3')

    self.CheckRequests([
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-1', project='my-project',
             region='us-west-1')),
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-2', project='my-project',
             region='us-west-1')),
        (self.compute.regionSslCertificates, 'Delete',
         messages.ComputeRegionSslCertificatesDeleteRequest(
             sslCertificate='cert-3', project='my-project', region='us-west-1'))
    ],)

  def testPromptingWithNoRegion(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('--region us-west-1 cert-1 cert-2 cert-3')

    self.CheckRequests()


class SslCertificatesDeleteBetaTest(SslCertificatesDeleteTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.prefix = 'beta'
    self._compute_api = self.compute_beta.sslCertificates


class SslCertificatesDeleteAlphaTest(SslCertificatesDeleteBetaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.prefix = 'alpha'
    self._compute_api = self.compute_alpha.sslCertificates


if __name__ == '__main__':
  test_case.main()
