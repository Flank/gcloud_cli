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
"""Tests for the `container binauthz create-signature-payload` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from string import Template
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class BinauthzAttestationsSurfaceTest(sdk_test_base.WithFakeAuth,
                                      cli_test_base.CliTestBase,
                                      binauthz_test_base.BinauthzUnitTestBase):

  def SetUp(self):
    # We don't get our track from the base binauthz test because `CliTestBase`
    # clobbers it in its SetUp.
    self.track = base.ReleaseTrack.ALPHA
    self.artifact_url = self.GenerateArtifactUrl()

  def testGoodUrl(self):
    sig = binauthz_command_util.MakeSignaturePayload(self.artifact_url)
    self.RunBinauthz([
        'create-signature-payload',
        '--artifact-url',
        self.artifact_url,
    ])
    expected_result = Template(
        textwrap.dedent("""\
      {
        "critical": {
          "identity": {
            "docker-reference": "${docker_reference}"
          },
          "image": {
            "docker-manifest-digest": "${docker_manifest_digest}"
          },
          "type": "Google cloud binauthz container signature"
        }
      }
      """))
    self.AssertOutputEquals(
        expected_result.substitute({
            'docker_reference':
                sig['critical']['identity']['docker-reference'],
            'docker_manifest_digest':
                sig['critical']['image']['docker-manifest-digest']
        }))

  def testBadUrl(self):
    expected_error = ('Invalid digest: sha256:123, must be at least 71 '
                      'characters')
    with self.AssertRaisesExceptionMatches(
        binauthz_command_util.BadImageUrlError, expected_error):
      self.RunBinauthz([
          'create-signature-payload',
          '--artifact-url',
          'docker.io/nginblah@sha256:123',
      ])


if __name__ == '__main__':
  sdk_test_base.main()
