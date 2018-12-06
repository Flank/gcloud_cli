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
"""Tests for command_lib.binauth.binauthz_command_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.binauthz import util as binauthz_command_util
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class ReplaceImageUrlSchemeTest(binauthz_test_base.BinauthzUnitTestBase,
                                parameterized.TestCase):

  def SetUp(self):
    self.digest = 'sha256:{}'.format(
        self.GenerateValidBogusLookingRandomSha256())

  @parameterized.parameters(
      ('https://docker.io/some_repo', 'https://docker.io/some_repo'),
      ('//docker.io/some_repo', 'https://docker.io/some_repo'),
      ('docker.io/some_repo', 'https://docker.io/some_repo'),
      ('foo://docker.io/some_repo', 'https://docker.io/some_repo'),
  )
  def testReplaceWithNonEmptyScheme(self, good_prefix, expected_prefix):
    good_url = '{}@{}'.format(good_prefix, self.digest)
    expected_url = '{}@{}'.format(expected_prefix, self.digest)
    self.assertEqual(
        binauthz_command_util._ReplaceImageUrlScheme(good_url, 'https'),
        expected_url)

  @parameterized.parameters(
      ('https://docker.io/some_repo', 'docker.io/some_repo'),
      ('//docker.io/some_repo', 'docker.io/some_repo'),
      ('docker.io/some_repo', 'docker.io/some_repo'),
      ('foo://docker.io/some_repo', 'docker.io/some_repo'),
  )
  def testReplaceWithEmptyScheme(self, good_prefix, expected_prefix):
    good_url = '{}@{}'.format(good_prefix, self.digest)
    expected_url = '{}@{}'.format(expected_prefix, self.digest)
    self.assertEqual(
        binauthz_command_util._ReplaceImageUrlScheme(good_url, ''),
        expected_url)

  def testMissingNetloc(self):
    bad_url = 'https:///some_repo@{}'.format(self.digest)  # NOTYPO
    with self.assertRaises(binauthz_command_util.BadImageUrlError):
      binauthz_command_util._ReplaceImageUrlScheme(bad_url, scheme='')


class NormalizeArtifactUrlTest(binauthz_test_base.BinauthzUnitTestBase):

  def SetUp(self):
    self.digest = 'sha256:{}'.format(
        self.GenerateValidBogusLookingRandomSha256())
    self.bad_digest = 'sha256:123'

  def testAlreadyNormalized(self):
    normalized_url = binauthz_command_util.NormalizeArtifactUrl(
        'https://docker.io/some_repo@' + self.digest)
    self.assertEqual('https://docker.io/some_repo@' + self.digest,
                     normalized_url)

  def testHttpScheme(self):
    normalized_url = binauthz_command_util.NormalizeArtifactUrl(
        'http://docker.io/some_repo@' + self.digest)
    self.assertEqual('https://docker.io/some_repo@' + self.digest,
                     normalized_url)

  def testNoScheme(self):
    normalized_url = binauthz_command_util.NormalizeArtifactUrl(
        'docker.io/some_repo@' + self.digest)
    self.assertEqual('https://docker.io/some_repo@' + self.digest,
                     normalized_url)

  def testBadDigest(self):
    with self.assertRaises(binauthz_command_util.BadImageUrlError):
      binauthz_command_util.NormalizeArtifactUrl('https://docker.io/some_repo@'
                                                 + self.bad_digest)


class MakeSignaturePayloadTest(binauthz_test_base.BinauthzUnitTestBase):

  def SetUp(self):
    self.repository = 'docker.io/nginblah'
    self.digest = 'sha256:{}'.format(
        self.GenerateValidBogusLookingRandomSha256())

  def testGoodUrl(self):
    sig = binauthz_command_util.MakeSignaturePayload(
        'docker.io/nginblah@{}'.format(self.digest))
    self.assertEqual(self.repository,
                     sig['critical']['identity']['docker-reference'])
    self.assertEqual(self.digest,
                     sig['critical']['image']['docker-manifest-digest'])
    self.assertEqual('Google cloud binauthz container signature',
                     sig['critical']['type'])

  def testBadUrl(self):
    with self.assertRaises(binauthz_command_util.BadImageUrlError):
      binauthz_command_util.MakeSignaturePayload(
          'docker.io/nginblah@sha256:123')


if __name__ == '__main__':
  test_case.main()
