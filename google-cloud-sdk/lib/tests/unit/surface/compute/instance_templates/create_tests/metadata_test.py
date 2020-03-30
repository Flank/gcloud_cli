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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --metadata x=y,z=1,a=b,c=d
        """)

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instance-templates create template-1
          --metadata-from-file x={},y={}
        """.format(metadata_file1, metadata_file2))

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='x', value='hello'),
            m.Metadata.ItemsValueListEntry(
                key='y', value='hello\nand\ngoodbye'),
        ]))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataAndMetadataFromFile(self):
    m = self.messages

    metadata_file1 = self.Touch(self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute instance-templates create template-1
          --metadata a=x,b=y,z=d
          --metadata-from-file x={},y={}
        """.format(metadata_file1, metadata_file2))

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='x'),
            m.Metadata.ItemsValueListEntry(key='b', value='y'),
            m.Metadata.ItemsValueListEntry(key='x', value='hello'),
            m.Metadata.ItemsValueListEntry(
                key='y', value='hello\nand\ngoodbye'),
            m.Metadata.ItemsValueListEntry(key='z', value='d'),
        ]))

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithMetadataContainingDuplicateKeys(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Encountered duplicate metadata key \[x\].'):
      self.Run("""
          compute instance-templates create template-1
            --metadata x=y,z=1
            --metadata-from-file x=file-1
          """)

    self.CheckRequests()

  def testWithMetadataFromNonExistentFile(self):
    metadata_file = self.Touch(self.temp_path, 'file-1', contents='hello')
    with self.assertRaisesRegex(
        files.Error,
        r'Unable to read file \[garbage\]: .*No such file or directory'):
      self.Run("""
          compute instance-templates create template-1
            --metadata-from-file x={},y=garbage
          """.format(metadata_file))

    self.CheckRequests()


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
