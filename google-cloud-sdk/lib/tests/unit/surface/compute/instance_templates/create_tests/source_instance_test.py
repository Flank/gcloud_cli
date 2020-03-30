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
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithSourceInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
        """)

    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(self.compute_uri +
                        '/projects/my-project/zones/asia-east1-a/'
                        'instances/tkul-konnn-test'),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithSourceInstanceAndConfigureDisk(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=true,device-name=foo,instantiate-from=source-image
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(m.DiskInstantiationConfig
                         .InstantiateFromValueValuesEnum)('SOURCE_IMAGE'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(self.compute_uri +
                        '/projects/my-project/zones/asia-east1-a/'
                        'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithSourceInstanceAndConfigureBlankDisk(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=true,device-name=foo,instantiate-from=blank
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(
            m.DiskInstantiationConfig.InstantiateFromValueValuesEnum)('BLANK'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(self.compute_uri +
                        '/projects/my-project/zones/asia-east1-a/'
                        'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithSourceInstanceAndConfigureDiskNoAutoDelete(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --source-instance tkul-konnn-test --source-instance-zone asia-east1-a
          --configure-disk auto-delete=false,device-name=foo,instantiate-from=source-image
        """)

    disk_config = m.DiskInstantiationConfig(
        autoDelete=False,
        deviceName='foo',
        instantiateFrom=(m.DiskInstantiationConfig
                         .InstantiateFromValueValuesEnum)('SOURCE_IMAGE'),
    )
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(self.compute_uri +
                        '/projects/my-project/zones/asia-east1-a/'
                        'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithSourceInstanceAndConfigureDiskCustomImage(self):
    m = self.messages
    self.Run('compute instance-templates create template-1 '
             '--source-instance tkul-konnn-test '
             '--source-instance-zone asia-east1-a '
             '--configure-disk auto-delete=true,device-name=foo,'
             'instantiate-from=custom-image,'
             'custom-image=projects/image-project/global/images/my-image')

    disk_config = m.DiskInstantiationConfig(
        autoDelete=True,
        deviceName='foo',
        instantiateFrom=(m.DiskInstantiationConfig
                         .InstantiateFromValueValuesEnum)('CUSTOM_IMAGE'),
        customImage='projects/image-project/global/images/my-image')
    template = m.InstanceTemplate(
        name='template-1',
        sourceInstance=(self.compute_uri +
                        '/projects/my-project/zones/asia-east1-a/'
                        'instances/tkul-konnn-test'),
        sourceInstanceParams=m.SourceInstanceParams(
            diskConfigs=[
                disk_config,
            ],),
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


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
