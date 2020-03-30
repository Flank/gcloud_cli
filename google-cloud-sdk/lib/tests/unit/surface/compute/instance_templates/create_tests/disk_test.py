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

  def testAttachmentOfExistingBootDisk(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Disk(name='disk-1'),
        ],
        [],
    ])

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=False,
            boot=True,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            source=('disk-1'),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            source=('disk-2'),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
    ])

    self.CheckRequests([(self.compute.instanceTemplates, 'Insert',
                         m.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template,
                             project='my-project',
                         ))],)

  def testLocalSSDsAndBootDisk(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Disk(name='disk-1'),
        ],
        [],
    ])

    # Ensures that the boot disk is placed at index 0 of the disks
    # list.
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-2
          --disk name=disk-1,boot=yes
          --local-ssd ''
          --local-ssd interface=NVME
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=False,
            boot=True,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            source=('disk-1'),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            source=('disk-2'),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=True,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='local-ssd')),
            mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
            type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
        m.AttachedDisk(
            autoDelete=True,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='local-ssd')),
            interface=(m.AttachedDisk.InterfaceValueValuesEnum.NVME),
            mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
            type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
    ])

    self.CheckRequests([(self.compute.instanceTemplates, 'Insert',
                         m.ComputeInstanceTemplatesInsertRequest(
                             instanceTemplate=template,
                             project='my-project',
                         ))],)

  def testSimpleDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-1'),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testComplexDiskOptionWithSingleDiskAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='x',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-1'),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testComplexDiskOptionsWithManyDisksAndSingleInstance(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --disk name=disk-1,mode=rw,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y,auto-delete=yes
          --disk boot=no,device-name=z,name=disk-3,mode=rw
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='x',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-1'),
        m.AttachedDisk(
            autoDelete=True,
            boot=False,
            deviceName='y',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-2'),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='z',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-3'),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testDiskOptionWithNoName(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[name\] is missing in \[--disk\]. \[--disk\] value must be of the '
        r'form \[name=NAME \[mode={ro,rw}\] \[boot={yes,no}\] '
        r'\[device-name=DEVICE_NAME\] \[auto-delete={yes,no}\]\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk mode=rw,device-name=x,boot=no
          """)

    self.CheckRequests()

  def testDiskOptionWithBadMode(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[mode\] in \[--disk\] must be \[rw\] or \[ro\], not '
        r'\[READ_WRITE\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=READ_WRITE,device-name=x
          """)

    self.CheckRequests()

  def testDiskOptionWithBadBoot(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[boot\] in \[--disk\] must be \[yes\] or \[no\], not '
        r'\[No\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,device-name=x,boot=No
          """)

    self.CheckRequests()

  def testDiskOptionWithBootDiskAndImageOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. One boot disk was '
        r'specified through \[--disk\] and another through \[--image\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=rw,boot=yes
            --image image-1
          """)

    self.CheckRequests()

  def testDiskOptionWithManyBootDisks(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Each instance can have exactly one boot disk. At least two boot disks '
        r'were specified through \[--disk\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk name=disk-1,mode=rw,boot=yes
            --disk name=disk-2,mode=ro,boot=no
            --disk name=disk-3,mode=rw,boot=yes
          """)

    self.CheckRequests()

  def testComplexDiskOptionsWithManyDisks(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='image-1',
                selfLink=('{compute}/projects/my-project/global/images/'
                          'image-1'.format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --boot-disk-device-name boot-disk
          --boot-disk-size 100GB
          --boot-disk-type pd-ssd
          --no-boot-disk-auto-delete
          --disk name=disk-1,mode=ro,device-name=x,boot=no
          --disk name=disk-2,mode=ro,device-name=y
          --disk boot=no,device-name=z,name=disk-3,mode=ro
          --image image-1
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=False,
            boot=True,
            deviceName='boot-disk',
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=('{compute}/projects/my-project/global/images'
                             '/image-1'.format(compute=self.compute_uri)),
                diskSizeGb=100,
                diskType='pd-ssd'),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='x',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-1'),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='y',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-2'),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            deviceName='z',
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT,
            source='disk-3'),
    ])

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(image='image-1', project='my-project'))],
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

  def testWithCreateDisks(self):
    m = self.messages

    self.Run(
        'compute instance-templates create template-1 '
        '  --create-disk name=disk-1,size=10GB,mode=ro,type=SSD,image=debian-8,'
        'image-project=debian-cloud,description=testDescription,'
        'disk-resource-policy='
        'https://compute.googleapis.com/compute/projects/'
        'cloudsdktest/regions/central2-a/resourcePolicies/testpolicy')

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            initializeParams=m.AttachedDiskInitializeParams(
                diskName='disk-1',
                description='testDescription',
                diskSizeGb=10,
                sourceImage=(self.compute_uri +
                             '/projects/debian-cloud/global/images'
                             '/debian-8'),
                diskType='SSD',
                resourcePolicies=[
                    'https://compute.googleapis.com/'
                    'compute/projects/'
                    'cloudsdktest/regions/central2-a/'
                    'resourcePolicies/testpolicy'
                ]),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_ONLY,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testWithMultipleCreateDisks(self):
    m = self.messages

    self.Run('compute instance-templates create template-1 '
             '  --create-disk type=SSD'
             '  --create-disk image=debian-8,image-project=debian-cloud')

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            initializeParams=m.AttachedDiskInitializeParams(diskType='SSD'),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=False,
            boot=False,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=(self.compute_uri +
                             '/projects/debian-cloud/global/images'
                             '/debian-8')),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalNVDIMM(self):
    self.Run("""
        compute instance-templates create template-1
          --local-nvdimm ''
        """)

    m = self.messages
    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=True,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='aep-nvdimm')),
            interface=m.AttachedDisk.InterfaceValueValuesEnum.NVDIMM,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalNVDIMMWithSize(self):
    self.Run("""
        compute instance-templates create template-1
          --local-nvdimm size=3TB
        """)

    m = self.messages
    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=True,
            diskSizeGb=3072,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='aep-nvdimm')),
            interface=m.AttachedDisk.InterfaceValueValuesEnum.NVDIMM,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.SCRATCH),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalSSDRequestWithSize(self):
    self.Run("""
        compute instance-templates create template-1
          --local-ssd ''
          --local-ssd interface=NVME,size=750
        """)

    m = self.messages
    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=self._default_image,),
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        m.AttachedDisk(
            autoDelete=True,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='local-ssd')),
            mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
            type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
        m.AttachedDisk(
            autoDelete=True,
            diskSizeGb=750,
            initializeParams=(m.AttachedDiskInitializeParams(
                diskType='local-ssd')),
            interface=(m.AttachedDisk.InterfaceValueValuesEnum.NVME),
            mode=(m.AttachedDisk.ModeValueValuesEnum.READ_WRITE),
            type=(m.AttachedDisk.TypeValueValuesEnum.SCRATCH)),
    ])

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates,
          'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testLocalSSDRequestWithBadSize(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Unexpected local SSD size: \[536870912000\]. '
        r'Legal values are positive multiples of 375GB.'):
      self.Run("""
          compute instance-templates create template-1
            --local-ssd size=500
          """)


if __name__ == '__main__':
  test_case.main()
