# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Test of the 'dataflow flex_template build' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


class BuildUnitTest(base.DataflowMockingTestBase,
                    sdk_test_base.WithOutputCapture):

  def SetUp(self):
    env_class = base.MESSAGE_MODULE.Environment
    self.fake_environment = env_class()
    self.metadata_file = self.Resource('tests/unit/surface/dataflow/test_data',
                                       'flex_template_metadata.json')

  def testRunBetaMissingSDKLanguage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --sdk-language: Must be specified.'):
      self.Run('dataflow flex-template build '
               'gs://foo --image gcr://foo-image '
               '--metadata-file {}'.format(self.metadata_file))

  def testRunBetaWrongSDKLanguage(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --sdk-language: Invalid choice: \'java\'.'):
      self.Run('dataflow flex-template build '
               '--image gcr://foo-image '
               '--metadata-file {} '
               '--sdk-language java'.format(self.metadata_file))

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --sdk-language: Invalid choice: \'python\'.'):
      self.Run('dataflow flex-template build '
               '--image gcr://foo-image '
               '--metadata-file {} '
               '--sdk-language python'.format(self.metadata_file))

    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --sdk-language: Invalid choice: \'random\'.'):
      self.Run('dataflow flex-template build '
               '--image gcr://foo-image '
               '--metadata-file {} '
               '--sdk-language random'.format(self.metadata_file))

  def testRunBetaNoTemplateFileGCSPath(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument TEMPLATE_FILE_GCS_PATH: Must be specified.'):
      self.Run(
          'dataflow flex-template build '
          '--image gcr://foo-image '
          '--metadata-file {} '
          '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaBadTemplateFileGCSPath(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must begin with \'gs://\''):
      self.Run('dataflow flex-template build gs//foo '
               '--image gcr://foo-image '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must begin with \'gs://\''):
      self.Run('dataflow flex-template build gcs://foo '
               '--image docker.io/foo-image '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must begin with \'gs://\''):
      self.Run('dataflow flex-template build foo '
               '--image foo-image '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Must begin with \'gs://\''):
      self.Run('dataflow flex-template build gs:foo '
               '--image gcr.io/foo-image '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaNoImage(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        ('Exactly one of (--image | --env --flex-template-base-image '
         '--image-gcr-path --jar) must be specified.')):
      self.Run('dataflow flex-template build gs://foo '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaWithImageAndImageGcrPath(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --env --flex-template-base-image --jar: Must be specified.'):
      self.Run('dataflow flex-template build gs://foo '
               '--image gcr.io/foo-image '
               '--image-gcr-path gcr.io/foo-image '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaWithImageGcrPathAndMissingBaseImage(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --flex-template-base-image: Must be specified.'):
      self.Run('dataflow flex-template build gs://foo '
               '--image-gcr-path gcr.io/foo-image '
               '--jar test.jar '
               '--env FLEX_TEMPLATE_JAVA_MAIN_CLASS=SomeClass '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaWithImageGcrPathAndMissingEnv(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --env: Must be specified.'):
      self.Run('dataflow flex-template build gs://foo '
               '--image-gcr-path gcr.io/foo-image '
               '--jar test.jar '
               '--flex-template-base-image JAVA11 '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))

  def testRunBetaWithImageGcrPathAndMissingJars(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --jar: Must be specified.'):
      self.Run('dataflow flex-template build gs://foo '
               '--image-gcr-path gcr.io/foo-image '
               '--env FLEX_TEMPLATE_JAVA_MAIN_CLASS=SomeClass '
               '--flex-template-base-image JAVA11 '
               '--metadata-file {} '
               '--sdk-language JAVA'.format(self.metadata_file))


if __name__ == '__main__':
  test_case.main()
