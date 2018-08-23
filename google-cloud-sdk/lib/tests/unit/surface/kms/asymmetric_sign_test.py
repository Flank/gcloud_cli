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
"""Tests that exercise the 'gcloud alpha kms asymmetric-sign' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib
import os
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.kms import base


class AsymmetricSignTest(base.KmsMockTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.version_name = self.project_name.Descendant('global/my_kr/my_key/2')

  def testAsymmetricSignSuccess(self):
    input_path = self.Touch(
        self.temp_path, name='input_data', contents=r'Hello 2018\o/\o/\o/')
    signature_path = self.Touch(self.temp_path, name='signature')

    self.kms.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.AsymmetricSign.Expect(  # pylint: disable=line-too-long
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricSignRequest(  # pylint: disable=line-too-long
            name=self.version_name.RelativeName(),
            asymmetricSignRequest=self.messages.AsymmetricSignRequest(
                digest=self.messages.Digest(
                    sha512=hashlib.sha512(r'Hello 2018\o/\o/\o/'.encode(
                        'utf-8')).digest()))),
        response=self.messages.AsymmetricSignResponse(
            signature=b'some signature'))

    self.Run('kms asymmetric-sign --location={location} '
             '--keyring={keyring} --key={key} --version={version} '
             '--digest-algorithm=sha512 --input-file={file} '
             '--signature-file={signature}'.format(
                 location=self.version_name.location_id,
                 keyring=self.version_name.key_ring_id,
                 key=self.version_name.crypto_key_id,
                 version=self.version_name.version_id,
                 file=input_path,
                 signature=signature_path))

    self.AssertBinaryFileEquals(b'some signature', signature_path)

  def testAsymmetricSignMissingCryptoKeyVersion(self):
    input_path = self.Touch(
        self.temp_path, name='input_data', contents=r'Hello 2018\o/\o/\o/')

    with self.assertRaisesRegexp(resources.RequiredFieldOmittedException,
                                 'value for.*is required but was not provided'):
      self.Run('kms asymmetric-sign --location={location} '
               '--keyring={keyring} --key={key} --digest-algorithm=sha512 '
               '--input-file={file}'.format(
                   location=self.version_name.location_id,
                   keyring=self.version_name.key_ring_id,
                   key=self.version_name.crypto_key_id,
                   file=input_path))

  def testAsymmetricSignMissingInputFile(self):
    input_path = os.path.join(self.temp_path, 'file-that-does-not-exist')

    with self.assertRaisesRegexp(files.MissingFileError,
                                 'Unable to read file.*No such file'):
      self.Run('kms asymmetric-sign --location={location} --keyring={keyring} '
               '--key={key} --version={version} --digest-algorithm=sha512 '
               '--input-file={file}'.format(
                   location=self.version_name.location_id,
                   keyring=self.version_name.key_ring_id,
                   key=self.version_name.crypto_key_id,
                   version=self.version_name.version_id,
                   file=input_path))


if __name__ == '__main__':
  test_case.main()
