# -*- coding: utf-8 -*- #
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

"""Tests for surface.container.binauthz.attestors.list."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class ListTest(base.WithMockBetaBinauthz, base.BinauthzTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSuccess_SinglePage(self):
    name1 = 'bar'
    proj = self.Project()
    attestor1 = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name1),
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name1),
            publicKeys=[
                self.messages.AttestorPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='0638AttestorDD940361EA2D7F14C58C124F0E663DA097'),
                self.messages.AttestorPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='92BF3E5381EF8364A6DFC6FC70ACF5E5D04087BA'),
            ],
        ))
    name2 = 'baz'
    attestor2 = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, name2),
        updateTime=times.FormatDateTime(datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference='projects/{}/notes/{}'.format(proj, name2),
            publicKeys=[
                self.messages.AttestorPublicKey(
                    asciiArmoredPgpPublicKey='',
                    comment=None,
                    id='7A3DD2310A6A07DF224479C2CFFDC297113486B0'),
            ],
        ))
    req = self.messages.BinaryauthorizationProjectsAttestorsListRequest(  # pylint: disable=line-too-long
        pageSize=500,
        pageToken=None,
        parent='projects/{}'.format(proj),
    )
    attestor_list = self.messages.ListAttestorsResponse(
        attestors=[attestor1, attestor2],
        nextPageToken=None)

    self.mock_client.projects_attestors.List.Expect(req, response=attestor_list)

    self.RunBinauthz('attestors list')

    expected_list = textwrap.dedent('''
        +------+---------------------------------+-----------------+
        | NAME |               NOTE              | NUM_PUBLIC_KEYS |
        +------+---------------------------------+-----------------+
        | bar  | projects/fake-project/notes/bar | 2               |
        | baz  | projects/fake-project/notes/baz | 1               |
        +------+---------------------------------+-----------------+
    ''').lstrip()

    self.AssertOutputEquals(expected_list)

  def testNoResults(self):
    proj = self.Project()
    req = self.messages.BinaryauthorizationProjectsAttestorsListRequest(  # pylint: disable=line-too-long
        pageSize=500,
        pageToken=None,
        parent='projects/{}'.format(proj),
    )
    attestor_list = self.messages.ListAttestorsResponse(
        attestors=[],
        nextPageToken=None)

    self.mock_client.projects_attestors.List.Expect(req, response=attestor_list)

    self.RunBinauthz('attestors list')

    self.AssertOutputMatches('')


class ListAlphaTest(base.WithMockAlphaBinauthz, ListTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
