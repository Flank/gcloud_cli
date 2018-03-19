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

"""Command strings shared by 'gcloud firebase test' unit and end-2-end tests."""


ANDROID_PREFIX = 'firebase test android '
ANDROID_TEST_RUN = ANDROID_PREFIX + 'run '
ANDROID_BETA_TEST_RUN = 'beta ' + ANDROID_PREFIX + 'run '
ANDROID_MODELS_LIST = ANDROID_PREFIX + 'models list '
ANDROID_VERSIONS_LIST = ANDROID_PREFIX + 'versions list '
ANDROID_LOCALES_LIST = ANDROID_PREFIX + 'locales list '
ANDROID_MODELS_DESCRIBE = ANDROID_PREFIX + 'models describe '
ANDROID_VERSIONS_DESCRIBE = ANDROID_PREFIX + 'versions describe '
ANDROID_LOCALES_DESCRIBE = ANDROID_PREFIX + 'locales describe '
NETWORK_PROFILES_LIST = 'firebase test network-profiles list '
NETWORK_PROFILES_DESCRIBE = 'firebase test network-profiles describe '

ANDROID_DEVICES_LIST = 'beta test android devices list '  # Deprecated
