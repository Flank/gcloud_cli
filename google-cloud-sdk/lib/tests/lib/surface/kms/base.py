# Copyright 2017 Google Inc. All Rights Reserved.
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

import copy

from apitools.base.py.testing import mock

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
        real_client=core_apis.GetClientInstance(
            'cloudkms', 'v1', no_http=True))
    self.kms.Mock()
    self.addCleanup(self.kms.Unmock)
    self.messages = core_apis.GetMessagesModule('cloudkms', 'v1')
    self.project_name = ResourceName(project_id=self.Project())


class ResourceName(object):
  """Helper representing the name of a KMS object."""

  def __init__(self,
               project_id=None,
               location_id=None,
               key_ring_id=None,
               crypto_key_id=None,
               version_id=None):
    """Create a ResourceName with whichever path components you want."""
    self.project_id = project_id
    self.location_id = location_id
    self.key_ring_id = key_ring_id
    self.crypto_key_id = crypto_key_id
    self.version_id = version_id

  def Parent(self):
    """Returns a ResourceName identifying the parent of this resource."""
    p = copy.copy(self)
    if p.version_id:
      p.version_id = None
    elif p.crypto_key_id:
      p.crypto_key_id = None
    elif p.key_ring_id:
      p.key_ring_id = None
    elif p.location_id:
      p.location_id = None
    elif p.project_id:
      p.project_id = None
    else:
      raise ValueError('Empty resource has no parent')
    return p

  def Child(self, resource_id):
    """Returns a ResourceName identifying a child of this resource.

    For example, a location is a child of a project; a KeyRing is a child of a
    location, etc.

    Args:
      resource_id: The ID (i.e., the last path component) of the child resource.

    Returns:
      A ResourceName identifying a child of this resource.

    Raises:
      ValueError: If this ResourceName is a CryptoKeyVersion.
    """
    c = copy.copy(self)
    if not c.project_id:
      c.project_id = resource_id
    elif not c.location_id:
      c.location_id = resource_id
    elif not c.key_ring_id:
      c.key_ring_id = resource_id
    elif not c.crypto_key_id:
      c.crypto_key_id = resource_id
    elif not c.version_id:
      c.version_id = resource_id
    else:
      raise ValueError('CryptoKeyVersion has no child resource')
    return c

  def Descendant(self, path):
    """A shortcut for repeatedly calling Child.

    r.Descendant('a/b') = r.Child('a').Child('b').

    Args:
      path: slash-separated list of IDs to pass to Child().

    Returns:
      The named descendant of this resource.
    """
    res = self
    for resource_id in path.split('/'):
      res = res.Child(resource_id)
    return res

  def RelativeName(self):
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
    if self.version_id:
      name = '/'.join([name, 'cryptoKeyVersions', self.version_id])
    return name


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
  def RunKmsBeta(self, *command):
    return self.Run(['beta', 'kms'] + list(command))

  def RunKms(self, *command):
    return self.Run(['kms'] + list(command))
