# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Fake Android device catalogs for testing."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis

TESTING_MESSAGES = apis.GetMessagesModule('testing', 'v1')


def EmptyAndroidCatalog():
  """Returns a fake Android device catalog containing no resources."""
  return TESTING_MESSAGES.AndroidDeviceCatalog(
      models=[],
      versions=[],
      runtimeConfiguration=TESTING_MESSAGES.AndroidRuntimeConfiguration(
          locales=[], orientations=[]))


def FakeAndroidCatalog():
  """Returns a fake Android device catalog containing three models."""
  android_virtual_model = TESTING_MESSAGES.AndroidModel(
      brand='Google',
      form=TESTING_MESSAGES.AndroidModel.FormValueValuesEnum.VIRTUAL,
      id='Nexus2099',
      manufacturer='MegaCorp',
      name='Nexus 2099',
      screenX=600,
      screenY=800,
      supportedVersionIds=['v98', 'v99'])
  android_physical_model = TESTING_MESSAGES.AndroidModel(
      brand='Sungsam',
      form=TESTING_MESSAGES.AndroidModel.FormValueValuesEnum.PHYSICAL,
      id='Universe3',
      manufacturer='Sungsam',
      name='Universe T3',
      screenX=1000,
      screenY=2000,
      supportedVersionIds=['C', 'F'],
      tags=['youreit', 'default'])
  android_deprecated_model = TESTING_MESSAGES.AndroidModel(
      brand='Sorny',
      form=TESTING_MESSAGES.AndroidModel.FormValueValuesEnum.PHYSICAL,
      id='EsperiaXYZ',
      manufacturer='Genuine Panaphonics',
      name='Esperia XYZ',
      screenX=10,
      screenY=7,
      supportedVersionIds=['0', '1', '2'],
      tags=['deprecated=1,2'])

  android_version_3 = TESTING_MESSAGES.AndroidVersion(
      apiLevel=3,
      codeName='Cupcake',
      distribution=TESTING_MESSAGES.Distribution(
          marketShare=12.3, measurementTime='nigh'),
      id='C',
      releaseDate=TESTING_MESSAGES.Date(month=4, day=27, year=2009),
      tags=['unsupported', 'deprecated'],
      versionString='1.5')
  android_version_8 = TESTING_MESSAGES.AndroidVersion(
      apiLevel=8,
      codeName='Froyo',
      id='F',
      releaseDate=TESTING_MESSAGES.Date(month=5, day=10, year=2010),
      tags=['default'],
      versionString='2.2.x')

  locale_ro = TESTING_MESSAGES.Locale(
      id='ro', name='Romulan', region='Romulus', tags=['cunning', 'default'])
  locale_kl = TESTING_MESSAGES.Locale(
      id='kl', name='Klingon', region='Empire', tags=['feisty'])

  orientation = TESTING_MESSAGES.Orientation(
      id='askew', name='off-kilter', tags=['default', 'graffiti'])

  return TESTING_MESSAGES.AndroidDeviceCatalog(
      models=[
          android_virtual_model, android_physical_model,
          android_deprecated_model
      ],
      versions=[android_version_3, android_version_8],
      runtimeConfiguration=TESTING_MESSAGES.AndroidRuntimeConfiguration(
          locales=[locale_ro, locale_kl], orientations=[orientation]))
