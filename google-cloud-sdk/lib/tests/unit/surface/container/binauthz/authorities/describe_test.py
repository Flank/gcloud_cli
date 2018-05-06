# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for surface.container.binauthz.authorities.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class DescribeTest(base.BinauthzMockedPolicyClientUnitTest):

  def testSuccess_WithPublicKey(self):
    ascii_armored_key = textwrap.dedent("""
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        aBcDeFg
        aBcDeFg
        aBcDeFg
        -----END PGP PUBLIC KEY BLOCK-----
    """)

    name = 'bar'
    proj = self.Project()
    aa = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, name),
        systemOwnedDrydockNote=None,
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, name),
            publicKeys=[
                self.messages.AttestationAuthorityPublicKey(
                    asciiArmoredPgpPublicKey=ascii_armored_key,
                    comment=None,
                    id='new_key'),
            ],
        ))
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesGetRequest(  # pylint: disable=line-too-long
        name='projects/{}/attestationAuthorities/{}'.format(proj, name),
    )

    self.client.projects_attestationAuthorities.Get.Expect(
        req, response=aa)

    response = self.RunBinauthz('authorities describe {name}'.format(name=name))

    self.assertEqual(response, aa)

    # Assert ascii-armored key appears in output.
    self.AssertOutputMatches(
        r'\n[ ]*'.join([''] + ascii_armored_key.splitlines()).rstrip())


if __name__ == '__main__':
  test_case.main()
