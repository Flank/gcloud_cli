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

"""Base class for all 'gcloud test android' integration tests."""

import os

from tests.lib import e2e_base
from tests.lib import sdk_test_base


E2E_TEST_DATA_PATH = sdk_test_base.SdkBase.Resource(
    'tests', 'e2e', 'surface', 'firebase', 'test', 'testdata')
INTEGRATION_ARGS = os.path.join(E2E_TEST_DATA_PATH, 'integration_args')
NOTEPAD_APP = os.path.join(E2E_TEST_DATA_PATH, 'notepad.apk')
NOTEPAD_TEST = os.path.join(E2E_TEST_DATA_PATH, 'notepad-test.apk')
WALKSHARE_APP = os.path.join(E2E_TEST_DATA_PATH, 'walkshare.apk')
WALKSHARE_TEST = os.path.join(E2E_TEST_DATA_PATH, 'walkshare-test.apk')
FTLGAME_APP = os.path.join(E2E_TEST_DATA_PATH, 'ftlgame.apk')


class TestIntegrationTestBase(e2e_base.WithServiceAuth):
  """Base class for all 'gcloud test android' integration tests."""
