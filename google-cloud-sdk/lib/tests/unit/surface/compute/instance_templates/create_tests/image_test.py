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

import textwrap

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateTest(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testWithImageInSameProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='my-image',
                selfLink=('{compute}/projects/'
                          'my-project/global/images/my-image'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image my-image
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=('{compute}/projects/'
                             'my-project/global/images/my-image'.format(
                                 compute=self.compute_uri)),),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(image='my-image', project='my-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageInDifferentProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global/images'
                          '/other-image'.format(compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image other-image
          --image-project some-other-project
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=(
                    '{compute}/projects/some-other-project/global/images'
                    '/other-image'.format(compute=self.compute_uri)),),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(
              image='other-image', project='some-other-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageInDifferentProjectWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global'
                          '/images/other-image'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image other-image
          --image-project {compute}/projects/some-other-project
          """.format(compute=self.compute_uri))

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=(
                    '{compute}/projects/some-other-project/global/images'
                    '/other-image'.format(compute=self.compute_uri)),),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(
              image='other-image', project='some-other-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithNoImageAndBootDiskDeviceNameOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-device-name\] can only be used when creating a new '
        r'boot disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-device-name x
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskSizeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-size\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-size 10GB
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskTypeOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--boot-disk-type\] can only be used when creating a new boot '
        r'disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --boot-disk-type pd-ssd
          """)

    self.CheckRequests()

  def testWithNoImageAndBootDiskAutoDeleteOverride(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--no-boot-disk-auto-delete\] can only be used when creating a new '
        'boot disk.'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk
            --no-boot-disk-auto-delete
          """)

    self.CheckRequests()

  def testIllegalAutoDeleteValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Value for \[auto-delete\] in \[--disk\] must be \[yes\] or \[no\], '
        r'not \[true\].'):
      self.Run("""
          compute instance-templates create template-1
            --disk boot=yes,name=my-disk,auto-delete=true
          """)

    self.CheckRequests()

  def testCreateWithConfigureDiskBadCustomImageArg(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Value for `instaniate-from` must be \'custom-image\' if the key '
        '`custom-image` is specified.'):
      self.Run('compute instance-templates create template-1 '
               '--source-instance tkul-konnn-test '
               '--source-instance-zone asia-east1-a '
               '--configure-disk auto-delete=true,device-name=foo,'
               'instantiate-from=source-image,'
               'custom-image=projects/image-project/global/images/my-image')

  def testWithNonExistentImage(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      yield None
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesExceptionMatches(
        utils.ImageNotFoundError,
        textwrap.dedent("""\
        Could not fetch image resource:
         - Not Found
        """)):
      self.Run("""
          compute instance-templates create template-1
            --image non-existent-image --image-project non-existent-project
          """)

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(
              image='non-existent-image', project='non-existent-project'))],)

  def testWithNonExistentImageNoImageProject(self):
    m = self.messages

    def MakeRequests(*_, **kwargs):
      if False:  # pylint: disable=using-constant-test
        yield
      kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.assertRaisesRegex(
        utils.ImageNotFoundError,
        (r'The resource \[(.*)projects/my-project/global/images/non-existent-'
         r'image\] was not found. Is the image located in another project\? '
         r'Use the --image-project flag to specify the project where the image '
         r'is located.')):
      self.Run("""
          compute instance-templates create template-1
            --image non-existent-image
          """)

    self.CheckRequests(
        [(self.compute.images, 'Get',
          m.ComputeImagesGetRequest(
              image='non-existent-image', project='my-project'))],)


class InstanceTemplatesCreateTestBeta(InstanceTemplatesCreateTest,
                                      parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateTestAlpha(InstanceTemplatesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testWithImageFamilyInSameProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='family/my-family',
                selfLink=('{compute}/projects/'
                          'my-project/global/images/family/my-family'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family my-family
        """)

    template = self._MakeInstanceTemplate(
        disks=[
            m.AttachedDisk(
                autoDelete=True,
                boot=True,
                initializeParams=m.AttachedDiskInitializeParams(
                    sourceImage=(
                        '{compute}/projects/'
                        'my-project/global/images/family/my-family'.format(
                            compute=self.compute_uri)),),
                mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
                type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
        ],)

    self.CheckRequests(
        [(self.compute.images, 'GetFromFamily',
          m.ComputeImagesGetFromFamilyRequest(
              family='my-family', project='my-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageFamilyInDifferentProject(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='other-image',
                selfLink=('{compute}/projects/some-other-project/global/images'
                          '/family/other-family'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family other-family
          --image-project some-other-project
        """)

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=(
                    '{compute}/projects/some-other-project/global/images'
                    '/family/other-family'.format(compute=self.compute_uri)),),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        [(self.compute.images, 'GetFromFamily',
          self.messages.ComputeImagesGetFromFamilyRequest(
              family='other-family', project='some-other-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testWithImageFamilyInDifferentProjectWithUri(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.Image(
                name='family/other-family',
                selfLink=('{compute}/projects/some-other-project/global'
                          '/images/family/other-family'.format(
                              compute=self.compute_uri))),
        ],
        [],
    ])

    self.Run("""
        compute instance-templates create template-1
          --image-family other-family
          --image-project {compute}/projects/some-other-project
          """.format(compute=self.compute_uri))

    template = self._MakeInstanceTemplate(disks=[
        m.AttachedDisk(
            autoDelete=True,
            boot=True,
            initializeParams=m.AttachedDiskInitializeParams(
                sourceImage=(
                    '{compute}/projects/some-other-project/global/images'
                    '/family/other-family'.format(compute=self.compute_uri)),),
            mode=m.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
            type=m.AttachedDisk.TypeValueValuesEnum.PERSISTENT)
    ])

    self.CheckRequests(
        [(self.compute.images, 'GetFromFamily',
          m.ComputeImagesGetFromFamilyRequest(
              family='other-family', project='some-other-project'))],
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )


if __name__ == '__main__':
  test_case.main()
