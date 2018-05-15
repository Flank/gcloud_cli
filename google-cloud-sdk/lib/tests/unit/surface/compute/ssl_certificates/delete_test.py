# Copyright 2015 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SslCertificatesDeleteTest(test_base.BaseTest):

  def testWithSingleNetwork(self):
    messages = self.messages
    self.Run("""
        compute ssl-certificates delete cert-1 --quiet
        """)

    self.CheckRequests(
        [(self.compute.sslCertificates,
          'Delete',
          messages.ComputeSslCertificatesDeleteRequest(
              sslCertificate='cert-1',
              project='my-project'))],
    )

  def testWithManyCertificates(self):
    messages = self.messages
    self.Run("""
        compute ssl-certificates delete cert-1 cert-2 cert-3 --quiet
        """)

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
    self.Run("""
        compute ssl-certificates delete cert-1 cert-2 cert-3
        """)

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
      self.Run("""
          compute ssl-certificates delete cert-1 cert-2 cert-3
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
