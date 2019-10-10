# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the disks create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import disks_test_base
from tests.lib.surface.compute import test_base


def SetUp(test_obj, api_version):
  test_obj.SelectApi(api_version)

  test_obj.make_requests.side_effect = iter(
      [[], [
          test_obj.messages.Zone(name='central2-a'),
      ]])

  test_obj._image_uri_prefix = (
      test_obj.compute_uri +
      '/projects/debian-cloud/global/images/')
  test_obj._default_image = (test_obj._image_uri_prefix +
                             'debian-8-jessie-v20151130')


class DisksCreateTestGA(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self.message_version = self.compute_v1
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.SelectApi('v1')

  def testDefaultOptionsWithSingleDisk(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=500),
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains("""\
        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting""",
                           normalize_space=True)

  def testNoWarningWithPerformantDiskSize(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a --size 200GB
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=200),
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains("""\
        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting""",
                           normalize_space=True)

  def testPerformanceWarningWithStandardPd(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a --size 199GB
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=199),
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [200GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')

  def testPerformanceWarningWithSSD(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a --size 9GB --type pd-ssd
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=9,
                  type=(self.compute_uri + '/projects/'
                        'my-project/zones/central2-a/diskTypes/pd-ssd')),
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains(
        'WARNING: You have selected a disk size of under [10GB]. This may '
        'result in poor I/O performance. For more information, see: '
        'https://developers.google.com/compute/docs/disks#performance.')

  def testDefaultOptionsWithMultipleDisks(self):
    self.Run("""
        compute disks create disk-1 disk-2 disk-3 --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=500),
              project='my-project',
              zone='central2-a')),
         (self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-2', sizeGb=500),
              project='my-project',
              zone='central2-a')),
         (self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-3', sizeGb=500),
              project='my-project',
              zone='central2-a'))],
    )

  def testSizeOptionWithGbUnits(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a --size 10GB
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=10),
              project='my-project',
              zone='central2-a'))],
    )

  def testSizeOptionWithByteUnits(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --size 21474836480B
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=20),
              project='my-project',
              zone='central2-a'))],
    )

  def testSizeOptionWithNonGbMultipleValue(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Disk size must be a multiple of 1 GB. Did you mean \[2GB\]?'):
      self.Run("""
          compute disks create disk-1 --zone central2-a
            --size 1073741825B
        """)
    self.CheckRequests()

  def testDescriptionOption(self):

    self.Run("""
        compute disks create disk-1 --zone central2-a
          --description "My Very Excellent Mother Just Served Us Nine Pizzas"
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  description=(
                      'My Very Excellent Mother Just Served Us Nine Pizzas'),
                  sizeGb=500),
              project='my-project',
              zone='central2-a'))],
    )

  def testTypeOption(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --type pd-ssd
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=100,
                  type=(self.compute_uri + '/projects/'
                        'my-project/zones/central2-a/diskTypes/pd-ssd')),
              project='my-project',
              zone='central2-a'))],
    )

  def testImageOptionWithoutAlias(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image my-image
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=(self.compute_uri + '/projects/'
                           'my-project/global/images/my-image'),
              project='my-project',
              zone='central2-a'))],
    )

  def testImageOptionWithImageProjectOption(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image other-image
          --image-project some-other-project
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=(self.compute_uri + '/projects/'
                           'some-other-project/global/images/other-image'),
              project='my-project',
              zone='central2-a'))],
    )

    self.AssertErrEquals('')

  def testImageAndSizeTogether(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image my-image --size 100GB
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=100),
              sourceImage=(self.compute_uri + '/projects/'
                           'my-project/global/images/my-image'),
              project='my-project',
              zone='central2-a'))],
    )

  def testImageAliasExpansionWithSingleImageMatch(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=self._default_image),
        ],

        [],
    ])

    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image debian-8
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=self._default_image,
              project='my-project',
              zone='central2-a'))],
    )

  def testImageAliasExpansionWithMultipleMatches(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            # This image is missing the "v" before the version number,
            # so it should be ignored.
            self.messages.Image(
                name='backports-debian-7-sp1-20160101',
                selfLink=(self._image_uri_prefix +
                          'backports-debian-7-sp1-20160101')),

            self.messages.Image(
                name='backports-debian-v7-sp1-v20110101',
                selfLink=(
                    self._image_uri_prefix +
                    'backports-debian-v7-sp1-v20110101')),
            self.messages.Image(
                name='backports-debian-v7-sp0-v20150101',
                selfLink=(
                    self._image_uri_prefix +
                    'backports-debian-v7-sp0-v20150101')),
            self.messages.Image(
                name='backports-debian-v7-sp2-v20120101',
                selfLink=(
                    self._image_uri_prefix +
                    'backports-debian-v7-sp2-v20120101')),
            self.messages.Image(
                name='backports-debian-v7-sp3-v20130101',
                selfLink=(
                    self._image_uri_prefix +
                    'backports-debian-v7-sp3-v20130101')),
            self.messages.Image(
                name='backports-debian-v7-sp3-a-v20130101a',
                selfLink=(
                    self._image_uri_prefix +
                    'backports-debian-v7-sp3-a-v20130101a')),
        ],

        [],
    ])

    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image debian-8
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=(
                  self._image_uri_prefix + 'backports-debian-v7-sp0-v20150101'),
              project='my-project',
              zone='central2-a'))],
    )

  def testImageAliasExpansionWithDeprecatedImages(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=self._default_image),

            self.messages.Image(
                name='debian-8-jessie-v20150101',
                selfLink=(self._image_uri_prefix +
                          'debian-8-jessie-v20150101'),
                deprecated=self.messages.DeprecationStatus(
                    state=(self.messages.DeprecationStatus.StateValueValuesEnum
                           .DEPRECATED))),

            self.messages.Image(
                name='debian-8-jessie-v20120101',
                selfLink=(self._image_uri_prefix +
                          'debian-8-jessie-v20120101'),
                deprecated=self.messages.DeprecationStatus(
                    state=(self.messages.DeprecationStatus.StateValueValuesEnum
                           .DEPRECATED))),
        ],
        []
    ])

    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image debian-8
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=self._default_image,
              project='my-project',
              zone='central2-a'))],
    )

  def testImageAliasExpansionWithAliasConflict(self):
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        [
            self.messages.Image(
                name='debian-8-jessie-v20151130',
                selfLink=self._default_image),

            self.messages.Image(
                name='debian-8',
                selfLink=(self.compute_uri + '/projects/'
                          'my-project/global/images/debian-8')),
        ],

        [],
    ])

    self.Run("""
        compute disks create disk-1 --zone central2-a
          --image debian-8
        """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1'),
              sourceImage=self._default_image,
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["{compute_uri}/projects/my-project/global/images/debian-8"'
        ', "{compute_uri}/projects/debian-cloud/global/images/debian-8-jessie-'
        'v20151130"]'.format(compute_uri=self.compute_uri))

  def testImageAliasExpansionWithNoMatches(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],

        [],

        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        r'Failed to find image for alias \[debian-8\] in public '
        r'image project \[debian-cloud\].'):
      self.Run("""
          compute disks create disk-1 --zone central2-a
            --image debian-8
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
    )

  def testImageAliasExpansionWithErrors(self):
    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        yield self.messages.Zone(name='central2-a')
      else:
        yield self.messages.Image(
            name='debian-8-jessie-v20151130',
            selfLink=self._default_image)
        kwargs['errors'].append((500, 'Server Error'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        r'Failed to find image for alias \[debian-8\] in public '
        r'image project \[debian-cloud\].'):
      self.Run("""
          compute disks create disk-1 --zone central2-a
            --image debian-8
          """)

    self.CheckRequests(
        self.zone_get_request,
        self.image_alias_expansion_requests,
    )
    self.AssertErrContains('Server Error')

  def testSnapshotOption(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --source-snapshot my-snapshot
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sourceSnapshot=(self.compute_uri +
                                  '/projects/my-project/global/snapshots/'
                                  'my-snapshot')),
              project='my-project',
              zone='central2-a'))],
    )

    self.AssertErrEquals('')

  def testSnapshotAndSize(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --source-snapshot my-snapshot --size 10GB
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sourceSnapshot=(self.compute_uri +
                                  '/projects/my-project/global/snapshots/'
                                  'my-snapshot'),
                  sizeGb=10),
              project='my-project',
              zone='central2-a'))],
    )

  def testZoneDeprecationWarningWithPromptYes(self):
    self.WriteInput('Y\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(
                name='central2-b',
                deprecated=self.messages.DeprecationStatus(
                    state=self.messages.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
                ),
        ],
        [],
    ])
    self.Run("""
        compute disks create disk-1 --zone central2-b
        """)

    self.CheckRequests(
        [(self.message_version.zones, 'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project', zone='central2-b'))],
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(name='disk-1', sizeGb=500),
              project='my-project',
              zone='central2-b'))],
    )

    # pylint: disable=line-too-long
    self.AssertErrContains(
        r'WARNING: The following selected zone is deprecated. All resources in '
        r'this zone will be deleted after the turndown date.\n'
        r' - [central2-b] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testUriSupport(self):
    self.Run("""
        compute disks create {compute_uri}/projects/my-project/zones/central2-a/disks/disk-1
          --source-snapshot {compute_uri}/projects/my-project/global/snapshots/my-snapshot
          --type {compute_uri}/projects/my-project/zones/central2-a/diskTypes/pd-ssd
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sourceSnapshot=(self.compute_uri +
                                  '/projects/my-project/global/snapshots/'
                                  'my-snapshot'),
                  type=(self.compute_uri + '/projects/'
                        'my-project/zones/central2-a/diskTypes/pd-ssd')),
              project='my-project',
              zone='central2-a'))],
    )

  def testImageFamilyFlag(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet --zone central2-a \
             --image-family yorik
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(name='hamlet',),
              sourceImage=(self.compute_uri +
                           '/projects/my-project/global/images/family/yorik'),
              project='my-project',
              zone='central2-a'))])

    self.AssertErrEquals('')

  def testImageFamilyURI(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet --zone central2-a \
             --image-family '{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(name='hamlet',),
              sourceImage=(self.compute_uri +
                           '/projects/my-project/global/images/family/yorik'),
              project='my-project',
              zone='central2-a'))])

  def testImageFamilyURIImageFlag(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet --zone central2-a \
             --image '{0}/projects/my-project/global/images/family/yorik'
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(name='hamlet',),
              sourceImage=(self.compute_uri +
                           '/projects/my-project/global/images/family/yorik'),
              project='my-project',
              zone='central2-a'))])


class DisksCreateTestBeta(DisksCreateTestGA):

  def SetUp(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

  def testCreateZonalDiskWithPhysicalBlockSize(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
          --physical-block-size 4096
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.message_version.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1', physicalBlockSizeBytes=4096, sizeGb=500),
              project='my-project',
              zone='central2-a'))],
    )


class DisksCreateTestAlpha(DisksCreateTestBeta):

  def SetUp(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

  def testCreateDiskEraseVss(self):
    self.Run("""
        compute disks create hamlet --zone central2-a \
        --erase-windows-vss-signature
    """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='hamlet',
                  sizeGb=500,
                  eraseWindowsVssSignature=True
              ),
              project='my-project',
              zone='central2-a'))])

  def testCreateDiskSourceDisk(self):
    self.Run("""
        compute disks create testdisk --zone central2-a
         --source-disk source --source-disk-zone central2-b
    """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='testdisk',
                  sourceDisk=self.compute_uri +
                  '/projects/my-project/zones/'
                  'central2-b/disks/source'
              ),
              project='my-project',
              zone='central2-a'))])


class DisksCreateTestWithCsekKeys(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'v1')
    self.private_key_fname = self.WriteKeyFile()

  def testCsekKeyOkRaw(self):
    self.Run("""
        compute disks create hamlet --zone central2-a \
             --csek-key-file {0}
        """.format(self.private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='hamlet',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testCsekKeyOkStdin(self):
    self.WriteInput(self.GetKeyFileContent())
    self.Run("""
        compute disks create hamlet --zone central2-a \
             --csek-key-file -
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='hamlet',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testEncryptionKeyWithSnapshotKeyOk(self):
    msgs = self.messages
    self.Run("""
        compute disks create hamlet --zone central2-a \
             --csek-key-file {0} --source-snapshot laertes \
        """.format(self.private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='hamlet',
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA='),
                  sourceSnapshot=(self.compute_uri +
                                  '/projects/my-project/global/snapshots/'
                                  'laertes'),
                  sourceSnapshotEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='AsAWoodcockToMineOwnSpringet00000000000000X=')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testEncryptionKeyWithImageKeyOk(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet --zone central2-a \
             --csek-key-file {0} --image yorik \
        """.format(self.private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='hamlet',
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA='),
                  sourceImageEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='aFellowOfInfiniteJestOfMostExcellentFancy00=')
                  ),
              sourceImage=(self.compute_uri +
                           '/projects/my-project/global/images/yorik'),
              project='my-project',
              zone='central2-a'))])

  def testCsekKeyRepeatedOk(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet ophelia --zone central2-a \
             --csek-key-file {0}
        """.format(self.private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='hamlet',
                  sizeGb=500,
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
                  ),
              project='my-project',
              zone='central2-a')),
         (self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='ophelia',
                  sizeGb=500,
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='OpheliaOphelia0000000000000000000000000000X=')
                  ),
              project='my-project',
              zone='central2-a'))
        ])

  def testCsekKeyRepeatedMissingOneNoRequireOk(self):
    msgs = self.messages

    self.Run("""
        compute disks create hamlet disk-1 --zone central2-a
             --csek-key-file {0}
             --no-require-csek-key-create
        """.format(self.private_key_fname))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='hamlet',
                  sizeGb=500,
                  diskEncryptionKey=msgs.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
                  ),
              project='my-project',
              zone='central2-a')),
         (self.compute.disks,
          'Insert',
          msgs.ComputeDisksInsertRequest(
              disk=msgs.Disk(
                  name='disk-1',
                  sizeGb=500,
                  ),
              project='my-project',
              zone='central2-a'))
        ])

  def testCsekKeyMissingRequired(self):
    with self.AssertRaisesExceptionMatches(
        csek_utils.MissingCsekException, 'Key required for resource'):
      self.Run("""
          compute disks create disk-1 --zone central2-a \
               --csek-key-file {0}
          """.format(self.private_key_fname))

  def testCsekKeyWrappedInvalid(self):
    # Explicitly include the RSA-wrapped key for this one
    self.private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)
    with self.assertRaisesRegex(csek_utils.BadKeyTypeException, re.escape(
        'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
        'alpha and beta versions of this command.')):
      self.Run("""
          compute disks create wrappedkeydisk --zone central2-a \
               --csek-key-file {0}
          """.format(self.private_key_fname))


class DisksCreateTestWithCsekKeysBeta(test_base.BaseTest):

  def SetUp(self):
    SetUp(self, 'beta')
    self.private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)
    self.track = calliope_base.ReleaseTrack.BETA

  def testCsekKeyOkWrapped(self):
    self.checkCreateDiskWithRsaIngressKey(
        self.WriteKeyFile(include_rsa_encrypted=True))

  def testCsekKeyOkWrappedV1DiskUrls(self):
    self.checkCreateDiskWithRsaIngressKey(
        self.WriteKeyFile(include_rsa_encrypted=True, api='v1'))

  def testCsekKeyOkWrappedAlphaDiskUrls(self):
    self.checkCreateDiskWithRsaIngressKey(
        self.WriteKeyFile(include_rsa_encrypted=True, api='alpha'))

  def checkCreateDiskWithRsaIngressKey(self, private_key_fname):
    self.Run("""
        compute disks create wrappedkeydisk --zone central2-a \
             --csek-key-file {0}
        """.format(private_key_fname))
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='wrappedkeydisk',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rsaEncryptedKey=test_base.SAMPLE_WRAPPED_CSEK_KEY)
                  ),
              project='my-project',
              zone='central2-a'))])


class DisksCreateTestWithKmsKeysGa(test_base.BaseTest):

  def SetupApiAndTrack(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testKmsKeyWithKeyNameArgsOk(self):
    self.SetupApiAndTrack()
    self.Run("""
        compute disks create wrappedkeydisk --zone central2-a \
            --kms-key=projects/key-project/locations/global/keyRings/disk-ring/cryptoKeys/disk-key
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='wrappedkeydisk',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/key-project/locations/global/'
                                 'keyRings/disk-ring/cryptoKeys/disk-key')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testKmsKeyWithKeyPartArgsOk(self):
    self.SetupApiAndTrack()
    self.Run("""
        compute disks create wrappedkeydisk --zone central2-a \
            --kms-project=key-project --kms-location=global \
            --kms-keyring=disk-ring --kms-key=disk-key
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='wrappedkeydisk',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/key-project/locations/global/'
                                 'keyRings/disk-ring/cryptoKeys/disk-key')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testKmsKeyWithoutProjectOk(self):
    self.SetupApiAndTrack()
    self.Run("""
        compute disks create wrappedkeydisk --zone central2-a \
            --kms-location=global \
            --kms-keyring=disk-ring --kms-key=disk-key
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='wrappedkeydisk',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/my-project/locations/global/'
                                 'keyRings/disk-ring/cryptoKeys/disk-key')
                  ),
              project='my-project',
              zone='central2-a'))])

  def testMissingKeyRing(self):
    self.SetupApiAndTrack()
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute disks create wrappedkeydisk --zone central2-a \
              --kms-location=global \
              --kms-key=disk-key
          """)

  def testMissingKey(self):
    self.SetupApiAndTrack()
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute disks create wrappedkeydisk --zone central2-a \
              --kms-location=global \
              --kms-keyring=disk-ring
          """)

  def testConflictKmsKeyNameWithCsekKeyFile(self):
    self.SetupApiAndTrack()
    self.WriteInput(self.GetKeyFileContent())
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run("""
          compute disks create hamlet --zone central2-a \
              --kms-key=projects/key-project/locations/global/keyRings/disk-ring/cryptoKeys/disk-key \
              --csek-key-file -
          """)


class DisksCreateTestWithKmsKeysBeta(DisksCreateTestWithKmsKeysGa):

  def SetupApiAndTrack(self):
    SetUp(self, 'beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testKmsKeyRegionFallthrough(self):
    self.SetupApiAndTrack()
    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',
            ),
        ],
        [],
    ])
    self.Run("""
        compute disks create wrappedkeydisk --region central2
            --replica-zones central2-b,central2-c
            --kms-keyring=disk-ring --kms-key=disk-key
        """)
    self.CheckRequests(
        [],
        [(self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='my-project',
              region='central2'
          ))],
        [(self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='wrappedkeydisk',
                  sizeGb=500,
                  diskEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/my-project/locations/central2/'
                                 'keyRings/disk-ring/cryptoKeys/disk-key'),
                  replicaZones=[
                      self.compute_uri+'/projects/my-project/zones/central2-b',
                      self.compute_uri+'/projects/my-project/zones/central2-c']
              ),
              project='my-project',
              region='central2'))],
    )


class DisksCreateTestWithKmsKeysAlpha(DisksCreateTestWithKmsKeysBeta):

  def SetupApiAndTrack(self):
    SetUp(self, 'alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA


class RegionalDisksCreateTestGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    SetUp(self, self.api_version)

  def testDefaultOptionsWithSingleDisk(self):
    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',
            ),
        ],
        [],
    ])
    self.Run("""
        compute disks create disk-1 --region central2 --replica-zones central2-b,central2-c
        """)

    self.CheckRequests(
        [],
        [(self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='my-project',
              region='central2'
          ))],
        [(self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/my-project/zones/central2-b',
                      self.compute_uri+'/projects/my-project/zones/central2-c']
              ),
              project='my-project',
              region='central2'))],
    )
    self.AssertErrContains("""\
        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting""",
                           normalize_space=True)

  def testRegionalDiskType(self):

    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',
            ),
        ],
        [],
    ])
    self.Run("""
        compute disks create disk-1
        --region central2
        --replica-zones central2-b,central2-c
        --type pd-standard
        """)

    self.CheckRequests(
        [],
        [(self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='my-project',
              region='central2'
          ))],
        [(self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  type=(self.compute_uri+'/projects/'
                        'my-project/regions/central2/diskTypes/pd-standard'),
                  replicaZones=[
                      self.compute_uri+'/projects/my-project/zones/central2-b',
                      self.compute_uri+'/projects/my-project/zones/central2-c']
              ),
              project='my-project',
              region='central2'))],
    )
    self.AssertErrContains("""\
        New disks are unformatted. You must format and mount a disk before it
        can be used. You can find instructions on how to do this at:

        https://cloud.google.com/compute/docs/disks/add-persistent-disk#formatting""",
                           normalize_space=True)

  def testRegionDeprecated(self):

    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',
                deprecated=self.messages.DeprecationStatus(
                    state=self.messages.DeprecationStatus
                    .StateValueValuesEnum
                    .DEPRECATED,
                    deleted='2015-03-29T00:00.000-07:00'),
            ),
        ],
        [],
    ])
    self.Run("""
        compute disks create disk-1 --region central2 --replica-zones central2-b,central2-c
        """)

    self.CheckRequests(
        [],
        [(self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='my-project',
              region='central2'
          ))],
        [(self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/my-project/zones/central2-b',
                      self.compute_uri+'/projects/my-project/zones/central2-c']
              ),
              project='my-project',
              region='central2'))],
    )

    # pylint: disable=line-too-long
    self.AssertErrContains(
        r'WARNING: The following selected region is deprecated. All resources '
        r'in this region will be deleted after the turndown date.\n'
        r' - [central2] 2015-03-29T00:00.000-07:00')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testRegionButNoReplicaZones(self):

    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('compute disks create disk-1 --region central2')

  def testReplicaZonesButNoRegion(self):

    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',),
        ],
        [],
    ])
    self.Run(
        'compute disks create disk-1 --replica-zones central2-b,central2-c')
    self.CheckRequests(
        [],
        [(self.compute.regions, 'Get', self.messages.ComputeRegionsGetRequest(
            project='my-project', region='central2'))],
        [(self.compute.regionDisks, 'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/my-project/zones/central2-b',
                      self.compute_uri+'/projects/my-project/zones/central2-c'
                  ]),
              project='my-project',
              region='central2'))],)

  def testWrongNumberOfReplicaZones(self):

    with self.AssertRaisesArgumentError():
      self.Run(
          'compute disks create disk-1 '
          '--region central2 '
          '--replica-zones central2-b')

  def testCreateInDifferentProjects(self):

    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',
            ),
        ],
        [
            self.messages.Region(
                name='central2',
            ),
        ],
        [],
    ])
    self.Run("""
        compute disks create
        https://compute.googleapis.com/compute/{version}/projects/project-1/regions/central2/disks/disk-1
        https://compute.googleapis.com/compute/{version}/projects/project-2/regions/central2/disks/disk-1
        --region central2
        --replica-zones central2-b,central2-c
        """.format(version=self.api_version))

    self.CheckRequests(
        [],
        [(self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='project-1',
              region='central2'
          )),
         (self.compute.regions,
          'Get',
          self.messages.ComputeRegionsGetRequest(
              project='project-2',
              region='central2'
          ))],
        [(self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/project-1/zones/central2-b',
                      self.compute_uri+'/projects/project-1/zones/central2-c']),
              project='project-1',
              region='central2')),
         (self.compute.regionDisks,
          'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/project-2/zones/central2-b',
                      self.compute_uri+'/projects/project-2/zones/central2-c']),
              project='project-2',
              region='central2'))],
    )


class RegionalDisksCreateTestBeta(RegionalDisksCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testCreateWithPhysicalBlockSize(self):
    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(name='central2',),
        ],
        [],
    ])
    self.Run('compute disks create disk-1 '
             '--replica-zones central2-b,central2-c '
             '--physical-block-size 16384')
    self.CheckRequests(
        [],
        [(self.compute.regions, 'Get',
          self.messages.ComputeRegionsGetRequest(
              project='my-project', region='central2'))],
        [(self.compute.regionDisks, 'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  physicalBlockSizeBytes=16384,
                  replicaZones=[
                      self.compute_uri +
                      '/projects/my-project/zones/central2-b',
                      self.compute_uri + '/projects/my-project/zones/central2-c'
                  ]),
              project='my-project',
              region='central2'))],
    )


class RegionalDisksCreateTestAlpha(RegionalDisksCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


class RegionalDisksCreateTestStandardTemplateGA(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    SetUp(self, self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',),
        ],
        [],
    ])

  def testZonalDiskCreate(self):
    self.Run("""
        compute disks create disk-1 --zone central2-a
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert', self.messages.ComputeDisksInsertRequest(
            disk=self.messages.Disk(name='disk-1', sizeGb=500),
            project='my-project',
            zone='central2-a'))],)

  def testProjectFromRegion(self):
    self.Run('compute disks create disk-1 '
             '--replica-zones central2-b,central2-c '
             '--region {}'.format(
                 self.resources.Create(
                     'compute.regions', project='project-1', region='central2')
                 .SelfLink()))
    self.CheckRequests(
        [],
        [(self.compute.regions, 'Get', self.messages.ComputeRegionsGetRequest(
            project='project-1', region='central2'))],
        [(self.compute.regionDisks, 'Insert',
          self.messages.ComputeRegionDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-1',
                  sizeGb=500,
                  replicaZones=[
                      self.compute_uri+'/projects/project-1/zones/central2-b',
                      self.compute_uri+'/projects/project-1/zones/central2-c'
                  ]),
              project='project-1',
              region='central2'))],)

  def testProjectsCache(self):
    self.Run('compute disks create disk-1 disk-2 '
             '--replica-zones central2-b,central2-c '
             '--region {}'.format(
                 self.resources.Create(
                     'compute.regions', project='project-1', region='central2')
                 .SelfLink()))
    self.CheckRequests([], [
        (self.compute.regions, 'Get', self.messages.ComputeRegionsGetRequest(
            project='project-1', region='central2'))
    ], [(self.compute.regionDisks, 'Insert',
         self.messages.ComputeRegionDisksInsertRequest(
             disk=self.messages.Disk(
                 name='disk-1',
                 sizeGb=500,
                 replicaZones=[
                     self.compute_uri+'/projects/project-1/zones/central2-b',
                     self.compute_uri+'/projects/project-1/zones/central2-c'
                 ]),
             project='project-1',
             region='central2')),
        (self.compute.regionDisks, 'Insert',
         self.messages.ComputeRegionDisksInsertRequest(
             disk=self.messages.Disk(
                 name='disk-2',
                 sizeGb=500,
                 replicaZones=[
                     self.compute_uri+'/projects/project-1/zones/central2-b',
                     self.compute_uri+'/projects/project-1/zones/central2-c'
                 ]),
             project='project-1',
             region='central2'))])

  def testZoneInDifferentProjectThanDisk(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--zone]: Zone [{compute_uri}/'
         'projects/project-2/zones/central2-b] lives in different '
         'project than disk [{compute_uri}/'
         'projects/project-1/regions/central2/disks/disk-1].'
         .format(compute_uri=self.compute_uri))):
      self.Run('compute disks create {} '
               '--replica-zones {},{}'.format(
                   self.resources.Create(
                       'compute.regionDisks',
                       project='project-1',
                       region='central2',
                       disk='disk-1').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-2',
                       zone='central2-b').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-2', zone='central2-c')
                   .SelfLink()))

  def testReplicaZonesInDifferentRegions(self):

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Zones [central1-b, central2-c] '
         'live in different regions [central1, central2], but should live in '
         'the same.')):
      self.Run('compute disks create {} '
               '--replica-zones {},{}'.format(
                   self.resources.Create(
                       'compute.regionDisks',
                       project='project-1',
                       region='central2',
                       disk='disk-1').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central1-b').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central2-c').SelfLink()))

  def testReplicaZonesInconsistentWithExplicitRegion(self):

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Region from [--replica-zones] '
         '(central2) is different from [--region] (central1).')):
      self.Run('compute disks create {} '
               '--replica-zones {},{} '
               '--region central1'.format(
                   self.resources.Create(
                       'compute.regionDisks',
                       project='project-1',
                       region='central2',
                       disk='disk-1').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central2-b').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central2-c').SelfLink()))

  def testRegionFromDiskDifferentFromReplicaZones(self):

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Region from [DISK_NAME] '
         '({compute_uri}/projects/project-1/'
         'regions/central1/disks/disk-1) is different from [--replica-zones] '
         '(central2).'.format(compute_uri=self.compute_uri))):
      self.Run('compute disks create {} '
               '--replica-zones {},{} '.format(
                   self.resources.Create(
                       'compute.regionDisks',
                       project='project-1',
                       region='central1',
                       disk='disk-1').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central2-b').SelfLink(),
                   self.resources.Create(
                       'compute.zones', project='project-1',
                       zone='central2-c').SelfLink()))

  def testRegionPromptingMissingReplicaZones(self):

    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.WriteInput('1\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='central2'),
        ],
        [
            self.messages.Zone(name='central2-a'),
        ],
        [],
    ])
    with self.assertRaises(exceptions.RequiredArgumentException):
      self.Run('compute disks create disk-1')


class RegionalDisksCreateTestStandardTemplateBeta(
    RegionalDisksCreateTestStandardTemplateGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class RegionalDisksCreateTestStandardTemplateAlpha(
    RegionalDisksCreateTestStandardTemplateBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


class DisksCreateWithLabelsTest(test_base.BaseTest):
  """Test creation of disk with labels."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateWithLabels(self):
    m = self.messages

    self.Run("""
       compute disks create disk-with-labels
       --zone=central2-a
       --labels=k0=v0,k-1=v-1
       --labels=foo=bar
       """)

    labels_in_request = (('foo', 'bar'), ('k-1', 'v-1'), ('k0', 'v0'))
    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks,
          'Insert',
          m.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  labels=m.Disk.LabelsValue(
                      additionalProperties=[
                          m.Disk.LabelsValue.AdditionalProperty(
                              key=pair[0], value=pair[1])
                          for pair in labels_in_request]),
                  name='disk-with-labels',
                  sizeGb=500),
              project='my-project',
              zone='central2-a',
          ))],
    )

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute disks create disk-with-labels
            --zone=central2-a
            --labels=inv@lid-key=inv@l!d-value
          """)


class DisksCreateWithGuestOsFeaturesTest(test_base.BaseTest):
  """Tests for GuestOsFeatures being added during disk creation."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateDisksWithOsFeatures(self):
    self.Run("""
        compute disks create my-disk --zone central2-a
          --guest-os-features WINDOWS,VIRTIO_SCSI_MULTIQUEUE
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='my-disk',
                  sizeGb=500,
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ]),
              project='my-project',
              zone='central2-a'))],
    )

  def testCreateGuestImageWithLowerCaseOsFeatures(self):
    self.Run("""
        compute disks create my-disk --zone central2-a
          --guest-os-features windows,virtio_scsi_multiqueue
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='my-disk',
                  sizeGb=500,
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ]),
              project='my-project',
              zone='central2-a'))],
    )

  def testCreateWithUnknownOsFeature(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --guest-os-features: BAD_FEATURE must be one of \['):
      self.Run("""
          compute disks create my-disk --zone central2-a
            --guest-os-features BAD_FEATURE
          """)

    self.CheckRequests()


class DisksCreateWithLicensesTest(test_base.BaseTest):
  """Tests for licenses being added during disk creation."""

  def SetUp(self):
    SetUp(self, 'v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testSingleLicense(self):
    licenses = [
        'https://compute.googleapis.com/compute/v1/projects/rhel-cloud/'
        'global/licenses/rhel-6-server'
    ]
    self.Run("""
        compute disks create my-disk --zone central2-a
          --licenses {0}
        """.format(licenses[0]))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='my-disk', sizeGb=500, licenses=licenses),
              project='my-project',
              zone='central2-a'))],
    )

  def testMultipleLicenses(self):
    licenses = [
        'https://compute.googleapis.com/compute/v1/projects/rhel-cloud/'
        'global/licenses/rhel-6-server',
        'https://compute.googleapis.com/compute/v1/projects/rhel-cloud/'
        'global/licenses/rhel-7-server',
        'https://compute.googleapis.com/compute/v1/projects/rhel-cloud/'
        'global/licenses/rhel-8-server',
    ]
    self.Run("""
        compute disks create my-disk --zone central2-a
          --licenses {0}
        """.format(','.join(licenses)))

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='my-disk', sizeGb=500, licenses=licenses),
              project='my-project',
              zone='central2-a'))],
    )


class DisksCreateTestWithResourcePoliciesBeta(disks_test_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.make_requests.side_effect = iter(
        [[], [
            self.messages.Zone(name='central2-a'),
        ]])

  def testCreate_ZonalWithResourcePolicy(self):
    self.Run("""
        compute disks create disk-with-backup --zone central2-a \
            --resource-policies my-policy
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-with-backup',
                  sizeGb=500,
                  resourcePolicies=[
                      'https://compute.googleapis.com/compute/{0}/projects/'
                      '{1}/regions/central2/resourcePolicies/my-policy'.format(
                          self.api_version, self.Project())
                  ]),
              project='my-project',
              zone='central2-a'))])

  def testCreate_ZonalWithMultipleResourcePolicies(self):
    self.Run("""
        compute disks create disk-with-backup --zone central2-a \
            --resource-policies pol1,pol2
        """)

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='disk-with-backup',
                  sizeGb=500,
                  resourcePolicies=[
                      'https://compute.googleapis.com/compute/{0}/projects/'
                      '{1}/regions/central2/resourcePolicies/pol1'.format(
                          self.api_version, self.Project()),
                      'https://compute.googleapis.com/compute/{0}/projects/'
                      '{1}/regions/central2/resourcePolicies/pol2'.format(
                          self.api_version, self.Project())
                  ]),
              project='my-project',
              zone='central2-a'))])

  def testCreate_RegionalWithResourcePolicy(self):
    self.make_requests.side_effect = iter([
        [],
        [
            self.messages.Region(
                name='central2',),
        ],
        [],
    ])
    self.Run('compute disks create disk-1 --region central2 '
             '--replica-zones central2-b,central2-c '
             '--resource-policies pol1')
    self.CheckRequests([], [
        (self.compute.regions, 'Get',
         self.messages.ComputeRegionsGetRequest(
             project='my-project', region='central2'))
    ], [(self.compute.regionDisks, 'Insert',
         self.messages.ComputeRegionDisksInsertRequest(
             disk=self.messages.Disk(
                 name='disk-1',
                 sizeGb=500,
                 resourcePolicies=[
                     'https://compute.googleapis.com/compute/{}/projects/'
                     'my-project/regions/central2/resourcePolicies/pol1'.format(
                         self.api_version)
                 ],
                 replicaZones=[
                     self.compute_uri + '/projects/my-project/zones/central2-b',
                     self.compute_uri + '/projects/my-project/zones/central2-c'
                 ]),
             project='my-project',
             region='central2'))])


class DisksCreateTestWithResourcePoliciesAlpha(
    DisksCreateTestWithResourcePoliciesBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateSharedZonalPD(self):
    self.Run('compute disks create sharedZonalDisk --zone central2-a '
             '--multi-writer ')

    self.CheckRequests(
        self.zone_get_request,
        [(self.compute.disks, 'Insert',
          self.messages.ComputeDisksInsertRequest(
              disk=self.messages.Disk(
                  name='sharedZonalDisk', sizeGb=500, multiWriter=True),
              project='my-project',
              zone='central2-a'))],
    )

if __name__ == '__main__':
  test_case.main()
