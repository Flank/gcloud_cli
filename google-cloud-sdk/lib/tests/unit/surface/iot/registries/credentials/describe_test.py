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
"""Tests for `gcloud iot registries credentials describe`."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CredentialsDescribeTest(base.CloudIotRegistryBase):

  def SetUp(self):
    x509_details = self.messages.X509CertificateDetails(
        subject='my-registry'
    )

    self.registry_credentials = [
        self._CreateRegistryCredential(
            'dummy contents', x509_details=x509_details),
        self._CreateRegistryCredential('other dummy contents')
    ]

  def testDescribe(self, track):
    self.track = track
    self._ExpectGet(self.registry_credentials)
    results = self.Run(
        'iot registries credentials describe 0'
        '    --format disable '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(results, self.registry_credentials[0])

  def testDescribe_Output(self, track):
    self.track = track
    self._ExpectGet(self.registry_credentials)
    self.Run(
        'iot registries credentials describe 0'
        '    --registry my-registry '
        '    --region us-central1')
    self.AssertOutputEquals("""\
        publicKeyCertificate:
          certificate: dummy contents
          format: X509_CERTIFICATE_PEM
          x509Details:
            subject: my-registry
        """, normalize_space=True)

  def testDescribe_BadIndex(self, track):
    self.track = track
    self._ExpectGet(self.registry_credentials)

    with self.AssertRaisesExceptionMatches(
        util.BadCredentialIndexError,
        'Invalid credential index [2]; registry [my-registry] has 2 '
        'credentials'):
      self.Run(
          'iot registries credentials describe 2'
          '    --format disable '
          '    --registry my-registry '
          '    --region us-central1')

  def testDescribe_RelativeName(self, track):
    self.track = track
    self._ExpectGet(self.registry_credentials)
    registry_name = ('projects/{}/'
                     'locations/us-central1/'
                     'registries/my-registry').format(self.Project())

    results = self.Run(
        'iot registries credentials describe 0'
        '    --format disable '
        '    --registry {} '.format(registry_name))

    self.assertEqual(results, self.registry_credentials[0])


if __name__ == '__main__':
  test_case.main()
