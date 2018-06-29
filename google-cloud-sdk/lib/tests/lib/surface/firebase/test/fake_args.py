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

"""Fake arguments for testing arg-file parsing and arg validation."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis


def TypedArgRules():
  return {
      'o-positive': {
          'required': ['blood'],
          'optional': ['today'],
          'defaults': {
              'blood': '1 pint',
          },
      },
      'ab-negative': {
          'required': ['platelets'],
          'optional': ['tomorrow'],
          'defaults': {
              'tomorrow': 'procrastinator',
          },
      },
  }


def SharedArgRules():
  return {
      'required': ['type', 'donate'],
      'optional': ['where'],
      'defaults': {
          'donate': 'feels-good',
      },
  }


def AllArgsSet():
  return set(
      ['blood', 'platelets', 'today', 'tomorrow', 'type', 'donate', 'where'])


def AndroidCatalog():
  """Returns a fake but realistic Android device catalog."""
  testing_messages = apis.GetMessagesModule('testing', 'v1')
  model_nexus1 = testing_messages.AndroidModel(
      form=testing_messages.AndroidModel.FormValueValuesEnum.VIRTUAL,
      id='Nexus1',
      manufacturer='MegaCorp',
      name='Nexus 1',
      screenX=1000,
      screenY=1600,
      supportedVersionIds=['k'])
  model_nexus2 = testing_messages.AndroidModel(
      form=testing_messages.AndroidModel.FormValueValuesEnum.VIRTUAL,
      id='Nexus2',
      manufacturer='Sungsam',
      name='Nexus 2',
      screenX=2000,
      screenY=3000,
      supportedVersionIds=['k', 'l'],
      tags=['default'])
  android_version_l = testing_messages.AndroidVersion(
      id='l',
      versionString='5.0',
      apiLevel=20,
      codeName='Lollipop',
      tags=['default'])
  android_version_k = testing_messages.AndroidVersion(
      id='k',
      versionString='4.4',
      apiLevel=19,
      codeName='KitKat')
  locale_de = testing_messages.Locale(id='de')
  locale_en = testing_messages.Locale(id='en', tags=['default'])
  locale_fr = testing_messages.Locale(id='fr')
  portrait = testing_messages.Orientation(id='portrait', tags=['default'])
  landscape = testing_messages.Orientation(id='landscape')

  return testing_messages.AndroidDeviceCatalog(
      models=[model_nexus1, model_nexus2],
      versions=[android_version_l, android_version_k],
      runtimeConfiguration=testing_messages.AndroidRuntimeConfiguration(
          locales=[locale_de, locale_en, locale_fr],
          orientations=[portrait, landscape]))
