# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for surface.container.binauthz.attestors.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class DescribeTest(base.WithMockGaBinauthz, base.BinauthzTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

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
    try:
      attestor = self.messages.Attestor(
          name='projects/{}/attestors/{}'.format(proj, name),
          updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
          userOwnedGrafeasNote=self.messages.UserOwnedGrafeasNote(
              noteReference='projects/{}/notes/{}'.format(proj, name),
              publicKeys=[
                  self.messages.AttestorPublicKey(
                      asciiArmoredPgpPublicKey=ascii_armored_key,
                      comment=None,
                      id='new_key'),
              ],
          ))
    except AttributeError:
      attestor = self.messages.Attestor(
          name='projects/{}/attestors/{}'.format(proj, name),
          updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
          userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
              noteReference='projects/{}/notes/{}'.format(proj, name),
              publicKeys=[
                  self.messages.AttestorPublicKey(
                      asciiArmoredPgpPublicKey=ascii_armored_key,
                      comment=None,
                      id='new_key'),
              ],
          ))
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name='projects/{}/attestors/{}'.format(proj, name),
    )

    self.mock_client.projects_attestors.Get.Expect(req, response=attestor)

    response = self.RunBinauthz('attestors describe {name}'.format(name=name))

    self.assertEqual(response, attestor)

    # Assert ascii-armored key appears in output.
    self.AssertOutputMatches(
        r'\n[ ]*'.join([''] + ascii_armored_key.splitlines()).rstrip())


class DescribeBetaTest(base.WithMockBetaBinauthz, DescribeTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DescribeAlphaTest(base.WithMockAlphaBinauthz, DescribeBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
