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

"""Tests for surface.container.binauthz.attestors.update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import datetime

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class UpdateTest(base.WithMockBetaBinauthz, base.BinauthzTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.name = 'bar'
    proj = self.Project()
    self.note_ref = 'projects/{}/notes/{}'.format(proj, self.name)
    self.attestor = self.messages.Attestor(
        name='projects/{}/attestors/{}'.format(proj, self.name),
        description='foo',
        updateTime=times.FormatDateTime(
            datetime.datetime.utcnow()),
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_ref,
            publicKeys=[],
        ))

  def testSuccess_UpdateDescription(self):
    updated_attestor = copy.deepcopy(self.attestor)
    updated_attestor.description = 'msg'

    self.mock_client.projects_attestors.Get.Expect(
        self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
            name=self.attestor.name,
        ),
        self.attestor)
    self.mock_client.projects_attestors.Update.Expect(updated_attestor,
                                                      updated_attestor)

    response = self.RunBinauthz(
        'attestors update {name} --description=msg'.format(name=self.name))

    self.assertEqual(updated_attestor, response)

  def testSuccess_UnsetDescription(self):
    updated_attestor = copy.deepcopy(self.attestor)
    updated_attestor.description = ''

    self.mock_client.projects_attestors.Get.Expect(
        self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
            name=self.attestor.name,
        ),
        self.attestor)
    self.mock_client.projects_attestors.Update.Expect(updated_attestor,
                                                      updated_attestor)

    response = self.RunBinauthz(
        'attestors update {name} --description=""'.format(name=self.name))

    self.assertEqual(updated_attestor, response)

  def testSuccess_NoUpdate(self):
    self.mock_client.projects_attestors.Get.Expect(
        self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
            name=self.attestor.name,
        ),
        self.attestor)
    self.mock_client.projects_attestors.Update.Expect(self.attestor,
                                                      self.attestor)

    response = self.RunBinauthz(
        'attestors update {name}'.format(name=self.name))

    self.assertEqual(self.attestor, response)


class UpdateAlphaTest(base.WithMockAlphaBinauthz, UpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
