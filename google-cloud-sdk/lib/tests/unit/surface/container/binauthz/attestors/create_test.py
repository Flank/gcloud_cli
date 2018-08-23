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

"""Tests for surface.container.binauthz.attestors.create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime

from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class CreateTest(base.BinauthzMockedBetaPolicyClientUnitTest):

  def SetUp(self):
    self.name = 'bar'
    proj = self.Project()
    self.note_ref = 'projects/{}/notes/{}'.format(proj, self.name)
    self.description = 'an attestor'
    self.attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, self.name),
        description=self.description,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_ref,
            publicKeys=[],
        ))
    self.req = self.messages.BinaryauthorizationProjectsAttestorsCreateRequest(  # pylint: disable=line-too-long
        attestor=self.attestor,
        attestorId=self.name,
        parent='projects/{}'.format(proj),
    )

    self.updated_attestor = copy.deepcopy(self.attestor)
    self.updated_attestor.updateTime = times.FormatDateTime(
        datetime.datetime.utcnow())

  def testSuccess(self):
    self.client.projects_attestors.Create.Expect(
        self.req, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors create '
        '--attestation-authority-note={note} '
        '--description="{desc}" '
        '{name}'.format(
            note=self.note_ref, desc=self.description, name=self.name))

    self.assertEqual(response, self.updated_attestor)

  def testSuccess_DestructuredNote(self):
    self.client.projects_attestors.Create.Expect(
        self.req, response=self.updated_attestor)

    response = self.RunBinauthz(
        'attestors create '
        '--attestation-authority-note={note} '
        '--attestation-authority-note-project={proj} '
        '--description="{desc}" '
        '{name}'.format(
            proj=self.Project(), note=self.name, desc=self.description,
            name=self.name))

    self.assertEqual(response, self.updated_attestor)


if __name__ == '__main__':
  test_case.main()
