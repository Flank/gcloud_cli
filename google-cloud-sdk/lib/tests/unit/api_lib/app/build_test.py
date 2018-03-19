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
"""Unit tests for command_lib.app.build."""

from googlecloudsdk.api_lib.app import build
from tests.lib import sdk_test_base
from tests.lib.api_lib.util import build_base


class BuildArtifactTest(sdk_test_base.WithLogCapture,
                        build_base.BuildBase):

  def testMakeImageFromOp(self):
    artifact = build.BuildArtifact.MakeImageArtifactFromOp(self.build_op)
    self.assertEqual(artifact.identifier, 'image-name')

  def testMakeBuildFromOp(self):
    artifact = build.BuildArtifact.MakeBuildIdArtifactFromOp(self.build_op)
    self.assertEqual(artifact.identifier, 'build-id')

  def testMakeBuildOptionsArtifact(self):
    artifact = build.BuildArtifact.MakeBuildOptionsArtifact({
        'build': 'veryfast'})
    self.assertTrue(artifact.IsBuildOptions())
