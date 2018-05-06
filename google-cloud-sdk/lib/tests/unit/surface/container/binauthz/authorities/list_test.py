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

"""Tests for surface.container.binauthz.authorities.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class ListTest(base.BinauthzMockedPolicyClientUnitTest):

  def testSuccess_SinglePage(self):
    name1 = 'bar'
    proj = self.Project()
    aa1 = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, name1),
        systemOwnedDrydockNote=None,
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, name1),
            publicKeys=[
                self.messages.AttestationAuthorityPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='0638AADD940361EA2D7F14C58C124F0E663DA097'),
                self.messages.AttestationAuthorityPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='92BF3E5381EF8364A6DFC6FC70ACF5E5D04087BA'),
            ],
        ))
    name2 = 'baz'
    aa2 = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, name2),
        systemOwnedDrydockNote=None,
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='providers/{}/notes/{}'.format(proj, name2),
            publicKeys=[
                self.messages.AttestationAuthorityPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='7A3DD2310A6A07DF224479C2CFFDC297113486B0'),
            ],
        ))
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesListRequest(  # pylint: disable=line-too-long
        pageSize=500,
        pageToken=None,
        parent='projects/{}'.format(proj),
    )
    aa_list = self.messages.ListAttestationAuthoritiesResponse(
        attestationAuthorities=[aa1, aa2],
        nextPageToken=None)

    self.client.projects_attestationAuthorities.List.Expect(
        req, response=aa_list)

    self.RunBinauthz('authorities list')

    expected_list = textwrap.dedent('''
        +------+----------------------------------+-----------------+
        | NAME |               NOTE               | NUM_PUBLIC_KEYS |
        +------+----------------------------------+-----------------+
        | bar  | providers/fake-project/notes/bar | 2               |
        | baz  | providers/fake-project/notes/baz | 1               |
        +------+----------------------------------+-----------------+
    ''').lstrip()

    self.AssertOutputEquals(expected_list)

  def testNoResults(self):
    proj = self.Project()
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesListRequest(  # pylint: disable=line-too-long
        pageSize=500,
        pageToken=None,
        parent='projects/{}'.format(proj),
    )
    aa_list = self.messages.ListAttestationAuthoritiesResponse(
        attestationAuthorities=[],
        nextPageToken=None)

    self.client.projects_attestationAuthorities.List.Expect(
        req, response=aa_list)

    self.RunBinauthz('authorities list')

    self.AssertOutputMatches('')


if __name__ == '__main__':
  test_case.main()
