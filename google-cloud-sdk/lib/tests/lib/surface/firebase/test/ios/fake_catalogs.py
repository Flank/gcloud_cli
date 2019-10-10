# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Fake iOS device catalogs for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

TESTING_MESSAGES = apis.GetMessagesModule('testing', 'v1')


def EmptyIosCatalog():
  """Returns a fake iOS device catalog containing no resources."""
  return TESTING_MESSAGES.IosDeviceCatalog(
      models=[],
      versions=[],
      runtimeConfiguration=TESTING_MESSAGES.IosRuntimeConfiguration(
          locales=[], orientations=[]))


def FakeIosCatalog():
  """Returns a fake but realistic iOS device catalog."""
  testing_messages = apis.GetMessagesModule('testing', 'v1')
  ios_model_1 = testing_messages.IosModel(
      id='iPencil1',
      name='iPencil 1',
      supportedVersionIds=['5.1', '6.0'],
      tags=['deprecated=5.1'])
  ios_model_2 = testing_messages.IosModel(
      id='iPen2',
      name='iPen 2',
      supportedVersionIds=['5.1', '6.0', '7.2'],
      tags=['default'])
  ios_model_3 = testing_messages.IosModel(
      id='iPen3',
      name='iPen 3',
      supportedVersionIds=['6.0', '7.2'],
      tags=['unstable'])
  ios_version_5 = testing_messages.IosVersion(
      id='5.1',
      majorVersion=5,
      minorVersion=1,
      supportedXcodeVersionIds=['9.2.0'],
      tags=['old'])
  ios_version_6 = testing_messages.IosVersion(
      id='6.0',
      majorVersion=6,
      minorVersion=0,
      supportedXcodeVersionIds=['9.2.0', '10.0.1'],
      tags=['default'])
  ios_version_7 = testing_messages.IosVersion(
      id='7.2',
      majorVersion=7,
      minorVersion=2,
      supportedXcodeVersionIds=['9.2.0', '10.0.1'])

  locale_ro = TESTING_MESSAGES.Locale(
      id='ro', name='Romulan', region='Romulus', tags=['cunning', 'default'])
  locale_kl = TESTING_MESSAGES.Locale(
      id='kl', name='Klingon', region='Empire', tags=['feisty'])

  orientation_askew = TESTING_MESSAGES.Orientation(
      id='askew', name='off-kilter', tags=['default', 'graffiti'])
  orientation_diagonal = TESTING_MESSAGES.Orientation(
      id='diagonal', name='diag', tags=['popcorn'])

  xcode_version_9 = TESTING_MESSAGES.XcodeVersion(
      version='9.2.0', tags=['default'])
  xcode_version_10 = TESTING_MESSAGES.XcodeVersion(
      version='10.0.1', tags=['beta'])

  return testing_messages.IosDeviceCatalog(
      models=[ios_model_1, ios_model_2, ios_model_3],
      versions=[ios_version_5, ios_version_6, ios_version_7],
      xcodeVersions=[xcode_version_9, xcode_version_10],
      runtimeConfiguration=TESTING_MESSAGES.IosRuntimeConfiguration(
          locales=[locale_ro, locale_kl],
          orientations=[orientation_askew, orientation_diagonal]))
