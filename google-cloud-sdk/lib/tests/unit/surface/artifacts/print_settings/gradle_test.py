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
"""Tests for artifacts print-settings gradle."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.artifacts import base


class GradleTestsBeta(base.ARTestBase):

  def PreSetUp(self):
    super(GradleTestsBeta, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def testGradle(self):
    cmd = [
        'artifacts', 'print-settings', 'gradle', '--repository=my-repo',
        '--location=us'
    ]
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.MAVEN)
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
// Insert following snippet into your build.gradle
// see docs.gradle.org/current/userguide/publishing_maven.html

plugins {
  id "maven-publish"
  id "com.google.cloud.artifactregistry.gradle-plugin" version "2.1.0"
}

publishing {
  repositories {
    maven {
      url "artifactregistry://us-maven.pkg.dev/fake-project/my-repo"
    }
  }
}

repositories {
  maven {
    url "artifactregistry://us-maven.pkg.dev/fake-project/my-repo"
  }
}

""",
        normalize_space=True)

  def testGradleJsonKeyInput(self):
    with files.TemporaryDirectory() as tmp_dir:
      key_file = os.path.join(tmp_dir, 'path/to/key.json')
      self.WriteKeyFile(key_file)
      cmd = [
          'artifacts', 'print-settings', 'gradle', '--repository=my-repo',
          '--location=us',
          '--json-key=%s' % key_file
      ]
      self.SetListLocationsExpect('us')
      self.SetGetRepositoryExpect(
          'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.MAVEN)

      self.Run(cmd)
      self.AssertOutputEquals(
          """\
// Move the secret to ~/.gradle.properties
def artifactRegistryMavenSecret = "eyJhIjoiYiJ9"

// Insert following snippet into your build.gradle
// see docs.gradle.org/current/userguide/publishing_maven.html

plugins {
  id "maven-publish"
}

publishing {
  repositories {
    maven {
      url "https://us-maven.pkg.dev/fake-project/my-repo"
      credentials {
        username = "_json_key_base64"
        password = "$artifactRegistryMavenSecret"
      }
    }
  }
}

repositories {
  maven {
    url "https://us-maven.pkg.dev/fake-project/my-repo"
    credentials {
      username = "_json_key_base64"
      password = "$artifactRegistryMavenSecret"
    }
    authentication {
      basic(BasicAuthentication)
    }
  }
}

""",
          normalize_space=True)

  def testGradleJsonKeyConfig(self):
    self.SetUpCreds()
    cmd = [
        'artifacts', 'print-settings', 'gradle', '--repository=my-repo',
        '--location=asia'
    ]
    self.SetListLocationsExpect('asia')
    self.SetGetRepositoryExpect(
        'asia', 'my-repo', self.messages.Repository.FormatValueValuesEnum.MAVEN)

    self.Run(cmd)
    self.AssertOutputEquals(
        """\
// Move the secret to ~/.gradle.properties
def artifactRegistryMavenSecret = "ewogICJjbGllbnRfZW1haWwiOiAiYmFyQGRldmVsb3Blci5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogImJhci5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuYXNkZlxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAia2V5LWlkIiwKICAidHlwZSI6ICJzZXJ2aWNlX2FjY291bnQiCn0="

// Insert following snippet into your build.gradle
// see docs.gradle.org/current/userguide/publishing_maven.html

plugins {
  id "maven-publish"
}

publishing {
  repositories {
    maven {
      url "https://asia-maven.pkg.dev/fake-project/my-repo"
      credentials {
        username = "_json_key_base64"
        password = "$artifactRegistryMavenSecret"
      }
    }
  }
}

repositories {
  maven {
    url "https://asia-maven.pkg.dev/fake-project/my-repo"
    credentials {
      username = "_json_key_base64"
      password = "$artifactRegistryMavenSecret"
    }
    authentication {
      basic(BasicAuthentication)
    }
  }
}

""",
        normalize_space=True)

  def testMissingRepo(self):
    cmd = ['artifacts', 'print-settings', 'gradle']
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Failed to find attribute [repository]')

  def testInvalidLocation(self):
    cmd = [
        'artifacts', 'print-settings', 'gradle', '--repository=my-repo',
        '--location=invalid'
    ]
    self.SetListLocationsExpect('us')
    with self.assertRaises(ar_exceptions.UnsupportedLocationError):
      self.Run(cmd)
    self.AssertErrContains(
        'invalid is not a valid location. Valid locations are')

  def testInvalidRepoType(self):
    cmd = [
        'artifacts', 'print-settings', 'gradle', '--repository=my-repo',
        '--location=us'
    ]
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Invalid repository type NPM. Valid type is MAVEN')


class GradleTestsAlpha(GradleTestsBeta):

  def PreSetUp(self):
    super(GradleTestsAlpha, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
