# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for build-artifacts print-settings maven."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.build_artifacts import exceptions as cba_exceptions
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class MavenTests(sdk_test_base.WithLogCapture, cli_test_base.CliTestBase):

  def testMaven(self):
    cmd = ' '.join([
        'alpha', 'build-artifacts', 'print-settings', 'maven',
        '--repository=my-repo'
    ])
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
Please insert following snippet into your pom.xml

======================================================
<project>
  <distributionManagement>
    <snapshotRepository>
      <id>cloud-build-artifacts</id>
      <url>buildartifacts://maven.pkg.dev/fake-project/my-repo</url>
    </snapshotRepository>
    <repository>
      <id>cloud-build-artifacts</id>
      <url>buildartifacts://maven.pkg.dev/fake-project/my-repo</url>
    </repository>
  </distributionManagement>

  <repositories>
    <repository>
      <id>cloud-build-artifacts</id>
      <url>buildartifacts://maven.pkg.dev/fake-project/my-repo</url>
      <releases>
        <enabled>true</enabled>
      </releases>
      <snapshots>
        <enabled>true</enabled>
      </snapshots>
    </repository>
  </repositories>

  <build>
    <extensions>
      <extension>
        <groupId>com.google.cloud.buildartifacts</groupId>
        <artifactId>buildartifacts-maven-wagon</artifactId>
        <version>1.0.0</version>
      </extension>
    </extensions>
  </build>
</project>
======================================================

""",
        normalize_space=True)

  def testMissingRepo(self):
    cmd = ' '.join(['alpha', 'build-artifacts', 'print-settings', 'maven'])
    with self.assertRaises(cba_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Failed to find attribute [repository]')


if __name__ == '__main__':
  test_case.main()
