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

"""Tests for surface.container.binauthz.authorities.delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.container.binauthz import base


class DeleteTest(base.BinauthzMockedPolicyClientUnitTest):

  def testSuccess_ExistingAuthority(self):
    name = 'bar'
    proj = self.Project()
    req = self.messages.BinaryauthorizationProjectsAttestationAuthoritiesDeleteRequest(  # pylint: disable=line-too-long
        name='projects/{}/attestationAuthorities/{}'.format(proj, name),
    )

    self.client.projects_attestationAuthorities.Delete.Expect(
        req, response=self.messages.Empty())

    response = self.RunBinauthz('authorities delete {name}'.format(name=name))

    self.assertIsNone(response)


if __name__ == '__main__':
  test_case.main()
