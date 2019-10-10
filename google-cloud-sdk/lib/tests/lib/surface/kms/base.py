# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Base classes and helpers for all gcloud kms tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy  # import: before=mock
from apitools.base.py.testing import mock
import enum

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base


class KmsMockTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth,
                  sdk_test_base.WithTempCWD):
  """A base class for gcloud kms tests that need to use a mocked KMS client."""

  def SetUp(self):
    self.kms = mock.Client(
        core_apis.GetClientClass('cloudkms', 'v1'),
        real_client=core_apis.GetClientInstance('cloudkms', 'v1', no_http=True))
    self.kms.Mock()
    self.addCleanup(self.kms.Unmock)
    self.messages = core_apis.GetMessagesModule('cloudkms', 'v1')
    self.project_name = ResourceName(project_id=self.Project())


class ResourceType(enum.Enum):
  """Represents the KMS resource types."""
  PROJECT = 'Project'
  LOCATION = 'Location'
  KEY_RING = 'KeyRing'
  IMPORT_JOB = 'ImportJob'
  CRYPTO_KEY = 'CryptoKey'
  CRYPTO_KEY_VERSION = 'CryptoKeyVersion'


class ResourceName(object):
  """Helper representing the name of a KMS object."""

  def __init__(self,
               project_id=None,
               location_id=None,
               key_ring_id=None,
               crypto_key_id=None,
               import_job_id=None,
               version_id=None):
    # type: (Optional[Text], Optional[Text], Optional[Text], Optional[Text], Optional[Text], Optional[Text])  # pylint: disable=line-too-long
    """Create a ResourceName with whichever path components you want."""
    self.project_id = project_id
    self.location_id = location_id
    self.key_ring_id = key_ring_id
    self.crypto_key_id = crypto_key_id
    self.import_job_id = import_job_id
    self.version_id = version_id

  def Parent(self):
    # type: () -> ResourceName
    """Returns a ResourceName identifying the parent of this resource."""
    p = copy.copy(self)
    if p.version_id:
      p.version_id = None
    elif p.crypto_key_id:
      p.crypto_key_id = None
    elif p.import_job_id:
      p.import_job_id = None
    elif p.key_ring_id:
      p.key_ring_id = None
    elif p.location_id:
      p.location_id = None
    elif p.project_id:
      p.project_id = None
    else:
      raise ValueError('Empty resource has no parent')
    return p

  def Location(self, location_id):
    # type: (Text) -> ResourceName
    """Returns a ResourceName for a Location child of this resource."""
    if self.GetType() != ResourceType.PROJECT:
      raise ValueError('The parent of a location must be a project')
    resource_name = copy.copy(self)
    resource_name.location_id = location_id
    return resource_name

  def KeyRing(self, key_ring_id):
    # type: (Text) -> ResourceName
    """Returns a ResourceName for a KeyRing child of this resource."""
    if self.GetType() != ResourceType.LOCATION:
      return self.ParsePath(key_ring_id, ResourceType.KEY_RING)
    resource_name = copy.copy(self)
    resource_name.key_ring_id = key_ring_id
    return resource_name

  def ImportJob(self, import_job_id):
    # type: (Text) -> ResourceName
    """Returns a ResourceName for an ImportJob child of this resource."""
    if self.GetType() != ResourceType.KEY_RING:
      return self.ParsePath(import_job_id, ResourceType.IMPORT_JOB)
    resource_name = copy.copy(self)
    resource_name.import_job_id = import_job_id
    return resource_name

  def CryptoKey(self, crypto_key_id):
    # type: (Text) -> ResourceName
    """Returns a ResourceName for a CryptoKey child of this resource."""
    if self.GetType() != ResourceType.KEY_RING:
      return self.ParsePath(crypto_key_id, ResourceType.CRYPTO_KEY)
    resource_name = copy.copy(self)
    resource_name.crypto_key_id = crypto_key_id
    return resource_name

  def Version(self, version_id):
    # type: (Text) -> ResourceName
    """Returns a ResourceName for a CryptoKeyVersion child."""
    if self.GetType() != ResourceType.CRYPTO_KEY:
      return self.ParsePath(version_id, ResourceType.CRYPTO_KEY_VERSION)
    resource_name = copy.copy(self)
    resource_name.version_id = version_id
    return resource_name

  def ParsePath(self, path, resource_type):
    # type: (Text, ResourceType) -> ResourceName
    """Parses the given path to produce a resource of the request type.

    Args:
      path: slash-separated list of IDs to pass to Child().
      resource_type: the ResourceType represented by the path.  This allows us
        to distinguish between CryptoKeys and ImportJobs.

    Returns:
      The named descendant of this resource.

    """
    res = self
    for resource_id in path.split('/'):
      if res.GetType() == ResourceType.PROJECT:
        res = res.Location(resource_id)
      elif res.GetType() == ResourceType.LOCATION:
        res = res.KeyRing(resource_id)
      elif res.GetType() == ResourceType.KEY_RING:
        if resource_type == ResourceType.IMPORT_JOB:
          res = res.ImportJob(resource_id)
        else:
          res = res.CryptoKey(resource_id)
      elif res.GetType() == ResourceType.CRYPTO_KEY:
        res = res.Version(resource_id)
    return res

  def RelativeName(self):
    # type: () -> Text
    """Renders this ResourceName as an atomic string.

    Returns:
      A string like 'projects/{project_id}/locations/{location_id}'
    """
    name = ''
    if self.project_id:
      name = '/'.join(['projects', self.project_id])
    if self.location_id:
      name = '/'.join([name, 'locations', self.location_id])
    if self.key_ring_id:
      name = '/'.join([name, 'keyRings', self.key_ring_id])
    if self.crypto_key_id:
      name = '/'.join([name, 'cryptoKeys', self.crypto_key_id])
    if self.import_job_id:
      name = '/'.join([name, 'importJobs', self.import_job_id])
    if self.version_id:
      name = '/'.join([name, 'cryptoKeyVersions', self.version_id])
    return name

  def GetType(self):
    # type: () -> ResourceType
    """Returns the ResourceType of this resource."""
    if self.version_id:
      return ResourceType.CRYPTO_KEY_VERSION
    elif self.crypto_key_id:
      return ResourceType.CRYPTO_KEY
    elif self.import_job_id:
      return ResourceType.IMPORT_JOB
    elif self.key_ring_id:
      return ResourceType.KEY_RING
    elif self.location_id:
      return ResourceType.LOCATION
    elif self.project_id:
      return ResourceType.PROJECT
    else:
      raise ValueError('Empty resource has no type')


class KmsE2ETestBase(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):
  """Base class for Kms integration tests."""

  def SetUp(self):
    self.keyring_namer = e2e_utils.GetResourceNameGenerator(prefix='keyring')
    self.cryptokey_namer = e2e_utils.GetResourceNameGenerator(
        prefix='cryptokey')

  # Helpers for commands to pass to Run,
  # output should not be passed to RunKms functions
  def FormatCmdKmsBeta(self, *command):
    return ['beta', 'kms'] + list(command)

  def FormatCmdKms(self, *command):
    return ['kms'] + list(command)

  # Helpers for running commands
  def RunKmsAlpha(self, *command):
    return self.Run(['alpha', 'kms'] + list(command))

  def RunKmsBeta(self, *command):
    return self.Run(['beta', 'kms'] + list(command))

  def RunKms(self, *command):
    return self.Run(['kms'] + list(command))
