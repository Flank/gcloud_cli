# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base class for all ml platform tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base


class _MlPlatformTestBase(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase,
                          parameterized.TestCase):
  """Base class for ML Platform command unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        client_class=apis.GetClientClass('ml', self.API_VERSION))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    resources.REGISTRY.RegisterApiByName('ml', self.API_VERSION)
    self.msgs = self.client.MESSAGES_MODULE
    self.short_msgs = self.GetShortNameMessageObject()

  def GetShortNameMessageObject(self):
    """Gets an object like the typical message module, but with shorter names.

    This is an awful hack, but almost necessary since in some cases the names of
    message types are 60 chars long*. Any access of these types is unwieldy,
    especially since the module lives at `self.msgs` (9 chars) and any reference
    is going to have indent level at least 2 (4 chars).

    It also allows reuse of test code between different API versions that are
    almost identical, save message names.

    In any case, prefixing each message type name with the API name and version
    is atypical.

    *e.g. `GoogleCloudMlV1beta1HyperparameterOutputHyperparameterMetric`

    Returns:
      object that behaves like the messages module, but with shorter names.
    """
    msgs = self.msgs
    api_version = self.API_VERSION

    class ShortNameMessages(object):

      def __getattr__(self, value):
        return getattr(msgs,
                       'GoogleCloudMl' + api_version.capitalize() + value)

    return ShortNameMessages()


class MlAlphaPlatformTestBase(_MlPlatformTestBase):
  """Base class for ML Platform command unit tests, alpha track."""
  API_VERSION = 'v1'

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA


class MlBetaPlatformTestBase(_MlPlatformTestBase):
  """Base class for ML Platform command unit tests, beta track."""
  API_VERSION = 'v1'

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA

  def GetBetaModel(self, name):
    return self.msgs.GoogleCloudMlV1beta1Model(name=name)


class MlGaPlatformTestBase(_MlPlatformTestBase):
  """Base class for ML Platform command unit tests, GA track."""
  API_VERSION = 'v1'

  def SetUp(self):
    self.track = base.ReleaseTrack.GA

  def GetGaModel(self, name):
    return self.msgs.GoogleCloudMlV1Model(name=name)
