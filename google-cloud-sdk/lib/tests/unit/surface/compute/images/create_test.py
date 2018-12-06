# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the images create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
import six


class ImagesCreateTest(test_base.BaseTest):

  def testAllFlags(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testWithSourceUri(self):
    self.Run("""
        compute images create my-image
          --source-uri https://www.googleapis.com/storage/v1/b/31dd/o/source-image
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testSourceUriWithGsProtocol(self):
    self.Run("""
        compute images create my-image
          --source-uri gs://31dd/source-image
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImageFromDisk(self):
    self.Run("""
        compute images create my-image
          --source-disk my-disk --source-disk-zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImage_NoDiskNoSourceURI(self):
    """Ensure an error is raised if --source-disk and --source-uri not given.
    """
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) must be'
        ' specified'
    ):
      self.Run("""compute images create my-image""")

  def testCreateImageFromUriWithZone(self):
    """Specifying a zone within the disk uri is no longer supported."""
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--source-disk-zone\] unless you are specifying '
        r'\[--source-disk\].'):
      self.Run("""
          compute images create my-image
            --source-disk-zone us-central1-a
            --source-uri gs://31dd/source-image
          """)

    self.CheckRequests()

  def testCreateParametersAreMutuallyExclusive(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-disk: Exactly one of (--source-disk | --source-image'
        ' | --source-image-family | --source-snapshot | --source-uri) must be'
        ' specified.'):
      self.Run("""
          compute images create my-image
            --source-disk my-disk --source-disk-zone us-central1-a
            --source-image my-image
            --source-image-family my-family
            --source-uri gs://31dd/source-image
          """)

  def testZonePrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
            self.messages.Zone(name='central2-b'),
        ],

        [],
    ])
    self.Run("""
        compute images create my-image
          --source-disk my-disk
        """)

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/central2-b/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )
    self.AssertErrContains('my-disk')
    self.AssertErrContains('central2-a')
    self.AssertErrContains('central2-b')

  def testUriSupport(self):
    self.Run("""
        compute images create my-image
          --source-disk https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-b/disks/my-disk
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/central2-b/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testDefaultUsedForSourceDiskZone(self):
    properties.VALUES.compute.zone.Set('us-central1-a')
    self.Run("""
        compute images create my-image
          --source-disk my-disk
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testFamily(self):
    self.Run("""
        compute images create my-image --family my-family
          --source-disk my-disk --source-disk-zone us-central1-a
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  family='my-family',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testSingleLicense(self):
    licenses = ['https://www.googleapis.com/compute/v1/projects/rhel-cloud/'
                'global/licenses/rhel-6-server']
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --licenses {0}
        """.format(licenses[0]))

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  licenses=licenses,
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testMultipleLicenses(self):
    licenses = ['https://www.googleapis.com/compute/v1/projects/rhel-cloud/'
                'global/licenses/rhel-6-server',
                'https://www.googleapis.com/compute/v1/projects/rhel-cloud/'
                'global/licenses/rhel-7-server',
                'https://www.googleapis.com/compute/v1/projects/rhel-cloud/'
                'global/licenses/rhel-8-server',
               ]
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --licenses {0}
        """.format(','.join(licenses)))

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  licenses=licenses,
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImageRequireCsekCreate_NoSourceDiskKeyProvided(self):
    """Tests that with --require-csek-create flag no image key causes an error.

    That is, if --require-csek-create is true (default), there *must* be a
    matching key for the image to create.

    This test verifies that this is true when no a matching key is found for the
    source disk.
    """
    private_key_fname = self.WriteKeyFile()

    image_uri = self.compute_uri + '/projects/my-project/global/images/my-image'
    with self.assertRaisesRegex(
        csek_utils.MissingCsekException,
        r'Key required for resource \[{0}\], but none found.'.format(
            image_uri)):
      # --require-csek-create is default
      self.Run("""
          compute images create my-image
            --source-disk my-disk --source-disk-zone us-central1-a
            --csek-key-file={0}
          """.format(private_key_fname))

  def testCreateImageRequireCsekCreate_SourceDiskKeyProvided(self):
    """Tests that with --require-csek-create flag no image key causes an error.

    That is, if --require-csek-create is true (default), there *must* be a
    matching key for the image to create.

    This test verifies that this is true even if a matching key is found for the
    source disk.
    """
    private_key_fname = self.WriteKeyFile()

    image_uri = self.compute_uri + '/projects/my-project/global/images/my-image'
    with self.assertRaisesRegex(
        csek_utils.MissingCsekException,
        r'Key required for resource \[{0}\], but none found.'.format(
            image_uri)):
      # --require-csek-create is default
      self.Run("""
          compute images create my-image
            --source-disk hamlet --source-disk-zone central2-a
            --csek-key-file={0}
          """.format(private_key_fname))

  def testCreateImageFromDiskCsekEncrypted(self):
    private_key_fname = self.WriteKeyFile()

    self.Run("""
        compute images create my-image
          --source-disk hamlet --source-disk-zone central2-a
          --csek-key-file={0} --no-require-csek-key-create
        """.format(private_key_fname))
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/central2-a/disks/hamlet'),
                  sourceDiskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA='),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImageFromDiskCsekEncryptedFromStdin(self):
    self.WriteInput(self.GetKeyFileContent())

    self.Run("""
        compute images create my-image
          --source-disk hamlet --source-disk-zone central2-a
          --csek-key-file - --no-require-csek-key-create
        """)
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/central2-a/disks/hamlet'),
                  sourceDiskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA='),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImageFromDiskCsekEncryptedRsaWrapped(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)

    with self.assertRaisesRegex(csek_utils.BadKeyTypeException,
                                r'Invalid key type \[rsa-encrypted\]'):
      self.Run("""
          compute images create my-image
            --source-disk wrappedkeydisk --source-disk-zone central2-a
            --csek-key-file={0} --no-require-csek-key-create
          """.format(private_key_fname))

  def testCreateImageEncrypted(self):
    private_key_fname = self.WriteKeyFile()

    self.Run("""
        compute images create yorik
          --source-disk my-disk --source-disk-zone us-central1-a
          --csek-key-file={0}
        """.format(private_key_fname))
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='yorik',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='aFellowOfInfiniteJestOfMostExcellentFancy00='),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImageFromDiskBothEncrypted(self):
    private_key_fname = self.WriteKeyFile()

    self.Run("""
        compute images create yorik
          --source-disk hamlet --source-disk-zone central2-a
          --csek-key-file={0}
        """.format(private_key_fname))
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='yorik',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/central2-a/disks/hamlet'),
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='aFellowOfInfiniteJestOfMostExcellentFancy00='),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW,
                  sourceDiskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')),
              project='my-project'))],
    )

  def testCreateImageCsekProvidedNeitherEncrypted(self):
    private_key_fname = self.WriteKeyFile()

    self.Run("""
        compute images create yorik
          --source-disk my-disk --source-disk-zone us-central1-a
          --csek-key-file={0}
        """.format(private_key_fname))
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='yorik',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      rawKey='aFellowOfInfiniteJestOfMostExcellentFancy00='),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )


class ImagesCreateCsekBetaTest(test_base.BaseTest):
  """Tests for CSEK features only available in beta."""

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateImageFromDiskCsekEncryptedRsaWrapped(self):
    private_key_fname = self.WriteKeyFile(include_rsa_encrypted=True)

    self.Run("""
        compute images create my-image
          --source-disk wrappedkeydisk --source-disk-zone central2-a
          --csek-key-file={0} --no-require-csek-key-create
        """.format(private_key_fname))
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/my-project'
                              + '/zones/central2-a/disks/wrappedkeydisk'),
                  sourceDiskEncryptionKey=self.messages.CustomerEncryptionKey(
                      rsaEncryptedKey=test_base.SAMPLE_WRAPPED_CSEK_KEY),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )


class ImagesCreateGuestOsFeaturesTest(test_base.BaseTest):
  """Tests for GuestOsFeatures available in the v1 API."""

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateGuestImageWithOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features WINDOWS,VIRTIO_SCSI_MULTIQUEUE
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateGuestImageWithLowerCaseOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features windows,virtio_scsi_multiqueue
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithUnknownOsFeature(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --guest-os-features: BAD_FEATURE must be one of \['):
      self.Run("""
          compute images create my-image
            --source-uri gs://31dd/source-image
            --guest-os-features BAD_FEATURE
          """)

    self.CheckRequests()

  def testCheckGuestOsFeaturesEnum(self):
    enums = list(
        self.messages.GuestOsFeature.TypeValueValuesEnum.to_dict().keys())
    enums.remove('FEATURE_TYPE_UNSPECIFIED')
    enums.sort()

    # Update the list in the image_utils module if this test fails because of an
    # API regen update mismatch. See b/72110252 for example.
    choices = list(image_utils.GUEST_OS_FEATURES)
    choices.sort()

    self.assertEqual(enums, choices)


class ImagesCreateGuestOsFeaturesBetaTest(test_base.BaseTest):
  """Tests for GuestOsFeatures available in beta."""

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateGuestImageWithOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features WINDOWS,VIRTIO_SCSI_MULTIQUEUE
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateGuestImageWithLowerCaseOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features windows,virtio_scsi_multiqueue
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithUnknownOsFeature(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --guest-os-features: BAD_FEATURE must be one of \['):
      self.Run("""
          compute images create my-image
            --source-uri gs://31dd/source-image
            --guest-os-features BAD_FEATURE
          """)

    self.CheckRequests()

  def testCheckGuestOsFeaturesEnum(self):
    enums = list(
        self.messages.GuestOsFeature.TypeValueValuesEnum.to_dict().keys())
    enums.remove('FEATURE_TYPE_UNSPECIFIED')
    enums.sort()

    choices = list(image_utils.GUEST_OS_FEATURES_BETA)
    choices.sort()

    self.assertEqual(enums, choices)


class ImagesCreateGuestOsFeaturesAlphaTest(test_base.BaseTest):
  """Tests for GuestOsFeatures currently available in alpha."""

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testCreateGuestImageWithOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features WINDOWS,VIRTIO_SCSI_MULTIQUEUE
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateGuestImageWithLowerCaseOsFeatures(self):
    self.Run("""
        compute images create my-image --description nifty
          --source-uri gs://31dd/source-image
          --guest-os-features windows,virtio_scsi_multiqueue
        """)

    windows_type = self.messages.GuestOsFeature.TypeValueValuesEnum('WINDOWS')
    vsm_type = self.messages.GuestOsFeature.TypeValueValuesEnum(
        'VIRTIO_SCSI_MULTIQUEUE')

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  description='nifty',
                  guestOsFeatures=[
                      self.messages.GuestOsFeature(type=windows_type),
                      self.messages.GuestOsFeature(type=vsm_type),
                  ],
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithUnknownOsFeature(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r'argument --guest-os-features: BAD_FEATURE must be one of \['):
      self.Run("""
          compute images create my-image
            --source-uri gs://31dd/source-image
            --guest-os-features BAD_FEATURE
          """)

    self.CheckRequests()

  def testCheckGuestOsFeaturesEnum(self):
    enums = list(
        self.messages.GuestOsFeature.TypeValueValuesEnum.to_dict().keys())
    enums.remove('FEATURE_TYPE_UNSPECIFIED')
    enums.sort()

    choices = list(image_utils.GUEST_OS_FEATURES_ALPHA)
    choices.sort()

    self.assertEqual(enums, choices)


class ImagesCreateWithForceCreateFlagTest(
    sdk_test_base.WithLogCapture, test_base.BaseTest):
  """Test the --force-create flag (deprecated) for image creation."""

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testForceImageCreationFromDisk(self):
    self.Run("""
        compute images create my-image
          --source-disk my-disk --source-disk-zone us-central1-a
          --force-create
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              forceCreate=True,
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )
    self.AssertLogContains(
        'Flag force-create is deprecated. Use --force instead.')


class ImagesCreateWithForceFlagTest(test_base.BaseTest):
  """Test the --force flag for image creation."""

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testForceImageCreationFromDisk(self):
    self.Run("""
        compute images create my-image
          --source-disk my-disk --source-disk-zone us-central1-a
          --force
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              forceCreate=True,
              image=self.messages.Image(
                  name='my-image',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )


class ImagesCreateWithLabelsTest(test_base.BaseTest):
  """Test creation of images with labels."""

  def SetUp(self):
    self.SelectApi('v1')
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateWithLabels(self):
    m = self.messages

    self.Run("""
       compute images create image-with-labels
         --source-disk my-disk
         --source-disk-zone us-central1-a
         --labels k0=v0,k-1=v-1
         --labels foo=bar
       """)

    labels_in_request = {'k0': 'v0', 'k-1': 'v-1', 'foo': 'bar'}
    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=m.Image(
                  labels=m.Image.LabelsValue(
                      additionalProperties=[
                          m.Image.LabelsValue.AdditionalProperty(
                              key=key, value=value)
                          for key, value in sorted(
                              six.iteritems(labels_in_request))]),
                  name='image-with-labels',
                  sourceDisk=(self.compute_uri + '/projects/'
                              'my-project/zones/us-central1-a/disks/my-disk'),
                  sourceType=m.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithInvalidLabels(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run("""
          compute images create image-with-labels
            --source-disk my-disk
            --source-disk-zone us-central1-a
            --labels inv@lid-key=inv@l!d-value
          """)


class ImagesCreateImageCloningTest(test_base.BaseTest):
  """Test cloning of images."""

  def testCreateWithSourceImage(self):
    m = self.messages
    source_image = m.Image(
        name='orig-image',
        selfLink=(self.compute_uri + '/projects/'
                  'my-project/global/images/orig-image'))
    self.make_requests.side_effect = iter([
        [source_image],
        [],
    ])

    self.Run("""
        compute images create clone-image
          --source-image orig-image
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          self.messages.ComputeImagesGetRequest(
              image='orig-image',
              project='my-project'))],
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=m.Image(
                  name='clone-image',
                  sourceImage=(self.compute_uri + '/projects/'
                               'my-project/global/images/orig-image'),
                  sourceType=m.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithImageFamily(self):
    m = self.messages
    source_image = m.Image(
        name='orig-image',
        selfLink=(self.compute_uri + '/projects/'
                  'my-project/global/images/orig-image'))
    self.make_requests.side_effect = iter([
        [source_image],
        [],
    ])

    self.Run("""
        compute images create clone-image
          --source-image-family image-family
        """)

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          self.messages.ComputeImagesGetFromFamilyRequest(
              family='image-family',
              project='my-project'))],
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=m.Image(
                  name='clone-image',
                  sourceImage=(self.compute_uri + '/projects/'
                               'my-project/global/images/orig-image'),
                  sourceType=m.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateWithSourceImageProject(self):
    m = self.messages
    source_image = m.Image(
        name='orig-image',
        selfLink=(self.compute_uri + '/projects/'
                  'cloud-project/global/images/orig-image'))
    self.make_requests.side_effect = iter([
        [source_image],
        [],
    ])

    self.Run("""
        compute images create clone-image
          --source-image orig-image
          --source-image-project cloud-project
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Get',
          self.messages.ComputeImagesGetRequest(
              image='orig-image',
              project='cloud-project'))],
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=m.Image(
                  name='clone-image',
                  sourceImage=(self.compute_uri + '/projects/'
                               'cloud-project/global/images/orig-image'),
                  sourceType=m.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testCreateImage_NoImageSource(self):
    """Ensure an error is raised if no source for image is given."""
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) must be'
        ' specified.'):
      self.Run("""compute images create my-image""")

  def testCreateParametersAreMutuallyExclusiveDiskImage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-disk: Exactly one of (--source-disk | '
        '--source-image | --source-image-family | --source-snapshot | '
        '--source-uri) must be specified.'):
      self.Run("""
          compute images create my-image
            --source-disk my-disk --source-disk-zone us-central1-a
            --source-image orig-image
          """)

  def testCreateParametersAreMutuallyExclusiveImageImageFamily(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-image: Exactly one of (--source-disk | '
        '--source-image | --source-image-family | --source-snapshot | '
        '--source-uri) must be specified.'):
      self.Run("""
          compute images create my-image
            --source-image orig-image
            --source-image-family image-family
          """)

  def testCreateParametersAreMutuallyExclusiveUriImage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-image: Exactly one of (--source-disk | '
        '--source-image | --source-image-family | --source-snapshot | '
        '--source-uri) must be specified.'):
      self.Run("""
          compute images create my-image
            --source-image orig-image
            --source-uri gs://31dd/source-image
          """)

  def testCreateImageFromProjectWithUri(self):
    """Test image creation through source image or source image family."""
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--source-image-project\] unless you are '
        r'specifying \[--source-image\] or \[--source-image-family\].'):
      self.Run("""
          compute images create my-image
            --source-image-project rhel-cloud
            --source-uri gs://31dd/source-image
          """)


class ImagesCreateImageFromSnapshotTest(test_base.BaseTest):
  """Test creating images from snapshots."""

  def testCreateWithSourceSnapshot(self):
    m = self.messages
    source_snapshot = m.Snapshot(
        name='orig-snapshot',
        selfLink=('https://www.googleapis.com/compute/alpha/projects/'
                  'my-project/global/snapshots/orig-snapshot'))
    self.make_requests.side_effect = iter([
        [source_snapshot],
        [],
    ])

    self.Run("""
        compute images create dest-image
          --source-snapshot orig-snapshot
        """)

    self.CheckRequests(
        [(self.compute.images, 'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=m.Image(
                  name='dest-image',
                  sourceSnapshot=(self.compute_uri + '/projects/'
                                  'my-project/global/snapshots/orig-snapshot'),
                  sourceType=m.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],)

  def testCreateImage_NoSnapshotSource(self):
    """Ensure an error is raised if no source for image is given."""
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) '
        'must be specified.'):
      self.Run("""compute images create my-image""")

  def testCreateParametersAreMutuallyExclusiveImageSnapshot(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) '
        'must be specified.'):
      self.Run("""
          compute images create my-image
            --source-snapshot orig-snapshot
            --source-image my-image
          """)

  def testCreateParametersAreMutuallyExclusiveDiskSnapshot(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) '
        'must be specified.'):
      self.Run("""
          compute images create my-image
            --source-snapshot orig-snapshot
            --source-disk my-disk --source-disk-zone us-central1-a
          """)

  def testCreateParametersAreMutuallyExclusiveSnapshotImageFamily(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) '
        'must be specified.'):
      self.Run("""
          compute images create my-image
            --source-snapshot orig-snapshot
            --source-image-family image-family
          """)

  def testCreateParametersAreMutuallyExclusiveUriSnapshot(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-disk | --source-image | '
        '--source-image-family | --source-snapshot | --source-uri) '
        'must be specified.'):
      self.Run("""
          compute images create my-image
            --source-snapshot orig-snapshot
            --source-uri gs://31dd/source-image
          """)


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA, 'alpha'),
                          (calliope_base.ReleaseTrack.BETA, 'beta'),
                          (calliope_base.ReleaseTrack.GA, 'v1'))
class ImageCreateTestWithKmsKeys(test_base.BaseTest, parameterized.TestCase):

  def testKmsKeyWithKeyNameArgsOk(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.Run("""
        compute images create my-image --source-uri gs://31dd/source-image \
            --kms-key=projects/key-project/locations/global/keyRings/ring/cryptoKeys/image-key
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/key-project/locations/global/'
                                 'keyRings/ring/cryptoKeys/image-key'
                  ),
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testKmsKeyWithKeyPartArgsOk(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.Run("""
        compute images create my-image --source-uri gs://31dd/source-image \
            --kms-project=key-project --kms-location=global \
            --kms-keyring=ring --kms-key=image-key
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/key-project/locations/global/'
                                 'keyRings/ring/cryptoKeys/image-key'
                  ),
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testKmsKeyWithoutProjectOk(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.Run("""
        compute images create my-image --source-uri gs://31dd/source-image \
            --kms-location=global \
            --kms-keyring=ring --kms-key=image-key
        """)

    self.CheckRequests(
        [(self.compute.images,
          'Insert',
          self.messages.ComputeImagesInsertRequest(
              image=self.messages.Image(
                  name='my-image',
                  imageEncryptionKey=self.messages.CustomerEncryptionKey(
                      kmsKeyName='projects/my-project/locations/global/'
                                 'keyRings/ring/cryptoKeys/image-key'
                  ),
                  rawDisk=self.messages.Image.RawDiskValue(
                      source='https://www.googleapis.com/storage/v1/b/31dd/o/'
                      'source-image'),
                  sourceType=self.messages.Image.SourceTypeValueValuesEnum.RAW),
              project='my-project'))],
    )

  def testMissingLocation(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute images create my-image --source-uri gs://31dd/source-image \
              --kms-keyring=ring --kms-key=key
          """)

  def testMissingKeyRing(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'KMS cryptokey resource was not fully specified.'):
      self.Run("""
          compute images create my-image --source-uri gs://31dd/source-image \
              --kms-location=global \
              --kms-key=key
          """)

  def testMissingKey(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    with self.AssertRaisesArgumentError():
      self.Run("""
          compute images create my-image --source-uri gs://31dd/source-image \
              --kms-location=global \
              --kms-keyring=ring
          """)

  def testConflictKmsKeyNameWithCsekKeyFile(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.WriteInput(self.GetKeyFileContent())
    with self.assertRaises(exceptions.ConflictingArgumentsException):
      self.Run("""
          compute images create yorik --source-uri gs://31dd/source-image \
              --kms-key=projects/key-project/locations/global/keyRings/ring/cryptoKeys/key \
              --csek-key-file -
          """)


if __name__ == '__main__':
  test_case.main()
