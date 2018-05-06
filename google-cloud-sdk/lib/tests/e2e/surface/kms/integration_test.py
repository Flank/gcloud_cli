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
"""Integration tests for gcloud kms commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os

from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptoKeysTest(base.KmsE2ETestBase):

  def SetUp(self):
    self.glbl = 'global'
    self.keyring = next(self.keyring_namer)
    self.RunKms('keyrings', 'create', self.keyring, '--location', self.glbl)

  def testCreateWithLabels(self):
    cryptokey = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl, '--purpose', 'encryption', '--labels',
                'k1=v1')

    # Check describe returns labels.
    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', cryptokey, '--keyring',
                          self.keyring, '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey))
    self.AssertOutputContains('k1: v1')

    # Check list returns labels.
    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'list', '--keyring', self.keyring,
                          '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey))
    self.AssertOutputContains(
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey))
    self.AssertOutputContains('k1: v1')

  def testIamCommands(self):
    cryptokey = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl, '--purpose', 'encryption')

    self.RunKms('keys', 'get-iam-policy', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl)
    # default expected output for new cryptokey
    self.AssertOutputContains('etag: ACAB')
    self.ClearOutput()

    policy_file = self.Touch(
        self.temp_path,
        contents="""{{
  "etag": "ACAB",
  "bindings": [ {{ "members": ["serviceAccount:{0}"], "role": "roles/owner" }} ]
}}
""".format(self.Account()))
    self.RunKms('keys', 'set-iam-policy', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl, policy_file)
    etag = yaml.load(self.GetOutput())['etag']
    self.ClearOutput()

    files.WriteFileContents(policy_file, """{{
  "etag": "{0}"
}}
""".format(etag))
    self.RunKms('keys', 'set-iam-policy', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl, policy_file)
    # "bindings" is not mentioned, so it should be unchanged.
    self.AssertOutputContains("""bindings:
- members:
  - serviceAccount:{0}
  role: roles/owner
""".format(self.Account()))
    etag = yaml.load(self.GetOutput())['etag']
    self.ClearOutput()

    files.WriteFileContents(policy_file, """{{
  "etag": "{0}",
  "bindings": []
}}
""".format(etag))
    self.RunKms('keys', 'set-iam-policy', cryptokey, '--keyring', self.keyring,
                '--location', self.glbl, policy_file)
    # "bindings" is set to [], so all entries should be removed.
    self.AssertOutputNotContains('bindings:')

  def testCreateList(self):
    # Create 2 cryptokeys, check that both are shown by list command
    cryptokey_a = next(self.cryptokey_namer)
    cryptokey_b = next(self.cryptokey_namer)

    self.RunKms('keys', 'list', '--keyring', self.keyring, '--location',
                self.glbl)
    self.AssertOutputNotContains(
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey_a))

    self.RunKms('keys', 'create', cryptokey_a, '--keyring', self.keyring,
                '--location', self.glbl, '--purpose', 'encryption')

    self.RunKms('keys', 'create', cryptokey_b, '--keyring', self.keyring,
                '--location', self.glbl, '--purpose', 'encryption')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'list', '--keyring', self.keyring,
                          '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey_b))
    self.AssertOutputContains(
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, cryptokey_a))

  def testSetRotationSchedule(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring, '--location',
                self.glbl, '--purpose', 'encryption', '--labels', 'k1=v1')

    self.RunKms('keys', 'set-rotation-schedule', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--next-rotation-time', '11-23-2099')

    self.RunKms('keys', 'set-rotation-schedule', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--next-rotation-time',
                '11-23-2099 21:34')

    self.RunKms('keys', 'set-rotation-schedule', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--rotation-period', '115d')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring', self.keyring,
                          '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, ck))
    self.AssertOutputContains('k1: v1')
    self.AssertOutputContains('nextRotationTime: \'2099-11-24T05:34:00Z\'')
    self.AssertOutputContains('rotationPeriod: 9936000s')

  def testUpdateCommands(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--purpose', 'encryption',
                '--labels', 'k1=v1')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring',
                          self.keyring, '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, ck))
    self.AssertOutputContains('k1: v1')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--next-rotation-time',
                '11-23-2099 21:34')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--rotation-period', '115d',
                '--update-labels', 'k1=v0')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring',
                          self.keyring, '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, ck))
    self.AssertOutputContains('k1: v0')
    self.AssertOutputContains('nextRotationTime: \'2099-11-24T05:34:00Z\'')
    self.AssertOutputContains('rotationPeriod: 9936000s')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--remove-rotation-schedule')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--update-labels', 'k1=v2,k2=v3')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring',
                          self.keyring, '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, ck))
    self.AssertOutputContains('k1: v2')
    self.AssertOutputContains('k2: v3')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--remove-labels', 'k1,k2')

    self.RunKms('keys', 'update', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--primary-version', '1',
                '--update-labels', 'k1=v1')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring',
                          self.keyring, '--location', self.glbl),
        'projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}'.format(
            self.Project(), self.glbl, self.keyring, ck))
    self.AssertOutputContains('k1: v1')

  def testEncryptDecrypt(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring, '--location',
                self.glbl, '--purpose', 'encryption')

    plaintext = os.urandom(32 * 1024)
    pt_path = self.Touch(self.temp_path, 'plaintext', contents=plaintext)
    aad_path = self.Touch(self.temp_path, 'aad', contents=os.urandom(16 * 1024))
    ct_path = self.Touch(self.temp_path, 'ciphertext')
    dc_path = self.Touch(self.temp_path, 'decrypted')

    self.RunKms('encrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--plaintext-file', pt_path, '--ciphertext-file',
                ct_path, '--additional-authenticated-data-file', aad_path)

    self.RunKms('decrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--ciphertext-file', ct_path, '--plaintext-file',
                dc_path, '--additional-authenticated-data-file', aad_path)

    # AssertFileEquals opens the file in text mode, which causes issues on
    # Windows.
    with open(dc_path, 'rb') as f:
      decrypted = f.read()
    self.assertEqual(plaintext, decrypted)

  def testEncryptDecryptWithStdio(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring, '--location',
                self.glbl, '--purpose', 'encryption')

    plaintext = os.urandom(32 * 1024)

    self.WriteBinaryInput(plaintext)
    self.RunKms('encrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--plaintext-file', '-', '--ciphertext-file', '-')
    ciphertext = self.GetOutputBytes()
    self.ClearOutput()

    self.WriteBinaryInput(ciphertext)
    self.RunKms('decrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--ciphertext-file', '-', '--plaintext-file', '-')
    self.assertEqual(plaintext, self.GetOutputBytes())

  def testEncryptDecryptWithNonPrimaryVersion(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring, '--location',
                self.glbl, '--purpose', 'encryption')
    # Make a new version and mark it primary.
    self.RunKms('keys', 'versions', 'create', '--key', ck, '--keyring',
                self.keyring, '--location', self.glbl, '--primary')

    plaintext = os.urandom(32 * 1024)
    pt_path = self.Touch(self.temp_path, 'plaintext', contents=plaintext)
    ct_path = self.Touch(self.temp_path, 'ciphertext')
    dc_path = self.Touch(self.temp_path, 'decrypted')

    # Primary should be version '2', now; encrypt with version '1'.
    self.RunKms('encrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--plaintext-file', pt_path, '--ciphertext-file',
                ct_path, '--version', '1')

    # Decrypt infers the correct version.
    self.RunKms('decrypt', '--keyring', self.keyring, '--location', self.glbl,
                '--key', ck, '--ciphertext-file', ct_path, '--plaintext-file',
                dc_path)

    # AssertFileEquals opens the file in text mode, which causes issues on
    # Windows.
    with open(dc_path, 'rb') as f:
      decrypted = f.read()
    self.assertEqual(plaintext, decrypted)

  def testUpdatePrimaryVersion(self):
    ck = next(self.cryptokey_namer)

    self.RunKms('keys', 'create', ck, '--keyring', self.keyring, '--location',
                self.glbl, '--purpose', 'encryption', '--labels', 'k1=v1')

    # Make a new version.
    self.RunKms('keys', 'versions', 'create', '--key', ck, '--keyring',
                self.keyring, '--location', self.glbl)

    # Make the new version primary, CryptoKeyVersion ids are monotamically
    # increasing, 1,2,3..., set the primary key to be the CryptoKeyVersion with
    # id 2, the one we just made above.
    self.RunKms('keys', 'set-primary-version', ck, '--keyring', self.keyring,
                '--location', self.glbl, '--version', '2')

    self.ReRunUntilOutputContains(
        self.FormatCmdKms('keys', 'describe', ck, '--keyring', self.keyring,
                          '--location', self.glbl),
        ('projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}/'
         'cryptoKeyVersions/2').format(self.Project(), self.glbl, self.keyring,
                                       ck))
    self.AssertOutputContains(
        ('projects/{0}/locations/{1}/keyRings/{2}/cryptoKeys/{3}/'
         'cryptoKeyVersions/2').format(self.Project(), self.glbl, self.keyring,
                                       ck))
    self.AssertOutputContains('k1: v1')


if __name__ == '__main__':
  test_case.main()
