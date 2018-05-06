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

"""Tests for surface.container.binauthz.authorities.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime

from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class CreateTest(base.BinauthzMockedPolicyClientUnitTest):

  def SetUp(self):
    self.name = 'bar'
    proj = self.Project()
    self.note_ref = 'providers/{}/notes/{}'.format(proj, self.name)
    self.aa = self.messages.AttestationAuthority(
        name='projects/{}/attestationAuthorities/{}'.format(proj, self.name),
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_ref,
            publicKeys=[],
        ))
    self.req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesCreateRequest(  # pylint: disable=line-too-long
        attestationAuthority=self.aa,
        attestationAuthorityId=self.name,
        parent='projects/{}'.format(proj),
    )

    self.updated_aa = copy.deepcopy(self.aa)
    self.updated_aa.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

  def testSuccess(self):
    self.client.projects_attestationAuthorities.Create.Expect(
        self.req, response=self.updated_aa)

    response = self.RunBinauthz(
        'authorities create --authority-note={note} {name}'.format(
            note=self.note_ref, name=self.name))

    self.assertEqual(response, self.updated_aa)

  def testSuccess_DestructuredNote(self):
    self.client.projects_attestationAuthorities.Create.Expect(
        self.req, response=self.updated_aa)

    response = self.RunBinauthz(
        'authorities create --authority-note={note} '
        '--authority-note-project={proj} {name}'.format(
            proj=self.Project(), note=self.name, name=self.name))

    self.assertEqual(response, self.updated_aa)


if __name__ == '__main__':
  test_case.main()
