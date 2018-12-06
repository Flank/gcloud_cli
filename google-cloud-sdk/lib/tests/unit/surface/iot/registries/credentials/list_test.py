# -*- coding: utf-8 -*- #
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

"""Tests for `gcloud iot registries credentials list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.cloudiot import base

TABLE_FIELDS = [
    'INDEX',
    'FORMAT',
    'ISSUER',
    'SUBJECT',
    'START_TIME',
    'EXPIRY_TIME',
    'SIGNATURE_ALGORITHM',
    'PUBLIC_KEY_TYPE',
]


class CredentialsListTestGA(base.CloudIotRegistryBase):

  def SetUp(self):
    x509_details = self.messages.X509CertificateDetails(
        expiryTime='2016-01-08T00:00Z',
        issuer='cloudsdk',
        publicKeyType='type',
        signatureAlgorithm='x.509v3',
        startTime='2016-01-01T00:00Z',
        subject='my-registry'
    )
    self.registry_credentials = [
        self._CreateRegistryCredential(self.CERTIFICATE_CONTENTS,
                                       x509_details=x509_details),
        self._CreateRegistryCredential(self.OTHER_CERTIFICATE_CONTENTS),
    ]
    self.header = ' '.join(TABLE_FIELDS)
    self.output_with_details = ' '.join(
        ['0', 'X509_CERTIFICATE_PEM', 'cloudsdk', 'my-registry',
         '2016-01-01T00:00Z', '2016-01-08T00:00Z', 'x.509v3', 'type'])
    self.output_without_details = ' '.join(['1', 'X509_CERTIFICATE_PEM'])
    # Add empty string to end of list because actual output contains a newline
    # at the end of the output.
    self.output = '\n'.join([self.header, self.output_with_details,
                             self.output_without_details, ''])

  def testList(self):
    self._ExpectGet(self.registry_credentials)

    results = self.Run(
        'iot registries credentials list'
        '    --format disable '
        '    --registry my-registry '
        '    --region us-central1')

    self.assertEqual(
        list(results),
        [
            {
                'publicKeyCertificate': {
                    'certificate': self.CERTIFICATE_CONTENTS,
                    'format': 'X509_CERTIFICATE_PEM',
                    'x509Details': {
                        'expiryTime': '2016-01-08T00:00Z',
                        'issuer': 'cloudsdk',
                        'publicKeyType': 'type',
                        'signatureAlgorithm': 'x.509v3',
                        'startTime': '2016-01-01T00:00Z',
                        'subject': 'my-registry'
                    }
                },
                'index': 0
            },
            {
                'publicKeyCertificate': {
                    'certificate': self.OTHER_CERTIFICATE_CONTENTS,
                    'format': 'X509_CERTIFICATE_PEM'
                },
                'index': 1
            },
        ])

  def testList_Output(self):
    self._ExpectGet(self.registry_credentials)

    self.Run(
        'iot registries credentials list'
        '    --registry my-registry '
        '    --region us-central1')

    self.AssertOutputEquals(self.output, normalize_space=True)

  def testList_RelativeName(self):
    self._ExpectGet(self.registry_credentials)

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry').format(self.Project())
    self.Run(
        'iot registries credentials list'
        '    --registry {}'.format(device_name))
    self.AssertOutputEquals(self.output, normalize_space=True)


class CredentialsListTestBeta(CredentialsListTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CredentialsListTestAlpha(CredentialsListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
