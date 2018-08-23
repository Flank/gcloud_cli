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
"""Tests that exercise 'gcloud alpha kms keys versions get-public-key'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.kms import base

EXPECTED_PEM = """-----BEGIN PUBLIC KEY-----
  MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6FYPL0VA8OHSw8fdc9nd
  pTty5PodtKARVC9iQ7Fu4StUiAcVL8VhBs06WQ1TyYVPY0e1pA59+rW6EqtBPIVL
  M2RZax2ieBjOGJRs1cabz0SnyIu4g9LdYf9gO1FBejMJuJDPd7DY8/yQmRk65Iq3
  mwym2huE79z//gZ4cWbMNnkd+IhZyiq7P21kSUYkliXEY6El4jECA1dfsnQnr9he
  Cmk2eCAX3BGOKzkmgxd9nKoupQaxS+pjxtrQGDIaMc3WejQBCT7tGo72vh8myC82
  3doK5WyphCH7dQMg3EkHb5IxOBnqG69rWyT5g6gdlya6tv1m1h1XI3n87hCESwWY
  rBricZs9P9pZVT+otoONRGOZd1j0F2XdCVjLP8HnYH3Tr4HOsK32qHpoO+9UKkmT
  IwbPdbUmtuR8xur/NUu5MfHRb8bmwlIqcg++Su28eJ7OikvdBlUIslO4sfsPS3wt
  tpZ6/KKeSdLd6Di3M1NYgnP9aiDPQgnNjCvyq3BnOVtyIEmUlSvTlKiFPs95jkVa
  NohC62O5YZI+iOdK1w3x6blbkYR3urRWmTqYa9IVo5wtING5cHt/42Exq8V/RtLy
  kZ7mq0uMYiX9G7EODOySVijHBF4+RhIEoiLS0gziUeh7PPu8YiN47e/PmBM3DwLl
  9TgasANPqmwASf+2JaWyRoUCAwEAAQ==
  -----END PUBLIC KEY-----"""


class KeysVersionsGetPublicKeyTest(base.KmsMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.key_name = self.project_name.Descendant('global/my_kr/my_key/')
    self.version_name = self.key_name.Descendant('3')

  def testGetPublicKeySuccess(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions
    output_path = self.Touch(self.temp_path, name='pem')

    ckv.GetPublicKey.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(  # pylint: disable=line-too-long
            name=self.version_name.RelativeName()),
        self.messages.PublicKey(pem=EXPECTED_PEM))

    self.Run('kms keys versions get-public-key {version} --location={location} '
             '--keyring={keyring} --key={key} --output-file={output}'.format(
                 version=self.version_name.version_id,
                 location=self.version_name.location_id,
                 keyring=self.version_name.key_ring_id,
                 key=self.version_name.crypto_key_id,
                 output=output_path))

    self.AssertFileEquals(EXPECTED_PEM, output_path)

  def testGetPublicKeyStdioSuccess(self):
    ckv = self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions

    ckv.GetPublicKey.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(  # pylint: disable=line-too-long
            name=self.version_name.RelativeName()),
        self.messages.PublicKey(pem=EXPECTED_PEM))

    self.Run('kms keys versions get-public-key {version} --location={location} '
             '--keyring={keyring} --key={key}'.format(
                 version=self.version_name.version_id,
                 location=self.version_name.location_id,
                 keyring=self.version_name.key_ring_id,
                 key=self.version_name.crypto_key_id))

    self.AssertOutputContains(EXPECTED_PEM, normalize_space=True)

  def testMissingId(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [version]: version id must be non-empty.'):
      self.Run('kms keys versions get-public-key {}/cryptoKeyVersions/'.format(
          self.key_name.RelativeName()))


if __name__ == '__main__':
  test_case.main()
