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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.android import catalog_manager
from tests.lib import test_case
from tests.lib.surface.firebase.test.android import fake_catalogs
from tests.lib.surface.firebase.test.android import unit_base

import six


class AndroidCatalogManagerTests(unit_base.AndroidMockClientTest):
  """Unit tests for api_lib/test/android/catalog_manager.py."""

  def testDimensionDefaults(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    self.assertEqual(mgr.GetDefaultModel(), 'Universe3')
    self.assertEqual(mgr.GetDefaultVersion(), 'F')
    self.assertEqual(mgr.GetDefaultLocale(), 'ro')
    self.assertEqual(mgr.GetDefaultOrientation(), 'askew')

  def testModelDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultModel()
    self.assertIn('model', six.text_type(ex_ctx.exception))

  def testVersionDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultVersion()
    self.assertIn('version', six.text_type(ex_ctx.exception))

  def testLocaleDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultLocale()
    self.assertIn('locale', six.text_type(ex_ctx.exception))

  def testOrientationDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultOrientation()
    self.assertIn('orientation', six.text_type(ex_ctx.exception))

  def testValidateModels(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    model1 = mgr.ValidateDimensionAndValue('model', 'Nexus2099')
    model2 = mgr.ValidateDimensionAndValue('model', 'Universe3')
    self.assertEqual(model1, 'Nexus2099')
    self.assertEqual(model2, 'Universe3')

  def testValidateVersionIds(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    ver1 = mgr.ValidateDimensionAndValue('version', 'C')
    ver2 = mgr.ValidateDimensionAndValue('version', 'F')
    self.assertEqual(ver1, 'C')
    self.assertEqual(ver2, 'F')

  def testValidateVersionNamesConvertedToVersionIds(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    ver1 = mgr.ValidateDimensionAndValue('version', '1.5')
    ver2 = mgr.ValidateDimensionAndValue('version', '2.2.x')
    self.assertEqual(ver1, 'C')
    self.assertEqual(ver2, 'F')

  def testValidateLocales(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    l1 = mgr.ValidateDimensionAndValue('locale', 'ro')
    l2 = mgr.ValidateDimensionAndValue('locale', 'kl')
    self.assertEqual(l1, 'ro')
    self.assertEqual(l2, 'kl')

  def testValidateOrientation(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    o1 = mgr.ValidateDimensionAndValue('orientation', 'askew')
    self.assertEqual(o1, 'askew')

  def testValidateModel_InvalidValue(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    with self.assertRaises(exceptions.ModelNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('model', 'Sungsam')
    self.assertIn("'Sungsam' is not a valid model",
                  six.text_type(ex_ctx.exception))

  def testValidateVersion_InvalidValue(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('version', '9.9')
    self.assertIn("'9.9' is not a valid OS version",
                  six.text_type(ex_ctx.exception))

  def testValidateLocale_InvalidValuel(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    with self.assertRaises(exceptions.LocaleNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('locale', 'vulcan')
    self.assertIn("'vulcan' is not a valid locale",
                  six.text_type(ex_ctx.exception))

  def testValidateOrientation_InvalidValue(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    with self.assertRaises(exceptions.OrientationNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('orientation', 'diagonal')
    self.assertIn("'diagonal' is not a valid device orientation",
                  six.text_type(ex_ctx.exception))

  def testValidateDimension_InvalidDimensionName(self):
    catalog = fake_catalogs.FakeAndroidCatalog()
    mgr = catalog_manager.AndroidCatalogManager(catalog)
    with self.assertRaises(exceptions.InvalidDimensionNameError) as ex_ctx:
      mgr.ValidateDimensionAndValue('brand', 'Sungsam')
    self.assertIn("'brand' is not a valid dimension",
                  six.text_type(ex_ctx.exception))


if __name__ == '__main__':
  test_case.main()
