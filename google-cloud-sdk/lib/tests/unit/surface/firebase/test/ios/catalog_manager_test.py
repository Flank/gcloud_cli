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

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from tests.lib import test_case
from tests.lib.surface.firebase.test.ios import fake_catalogs
from tests.lib.surface.firebase.test.ios import unit_base


class IosCatalogManagerTests(unit_base.IosMockClientTest):
  """Unit tests for api_lib/test/ios/catalog_manager.py."""

  def testDimensionDefaults(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    self.assertEqual(mgr.GetDefaultModel(), 'iPen2')
    self.assertEqual(mgr.GetDefaultVersion(), '6.0')
    self.assertEqual(mgr.GetDefaultLocale(), 'en')
    self.assertEqual(mgr.GetDefaultOrientation(), 'portrait')

  def testModelDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyIosCatalog()
    mgr = catalog_manager.IosCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultModel()
    self.assertIn('model', ex_ctx.exception.message)

  def testVersionDefaultIsMissing(self):
    empty_catalog = fake_catalogs.EmptyIosCatalog()
    mgr = catalog_manager.IosCatalogManager(empty_catalog)
    with self.assertRaises(exceptions.DefaultDimensionNotFoundError) as ex_ctx:
      mgr.GetDefaultVersion()
    self.assertIn('version', ex_ctx.exception.message)

  def testLocaleDefaultIsEnglish(self):
    empty_catalog = fake_catalogs.EmptyIosCatalog()
    mgr = catalog_manager.IosCatalogManager(empty_catalog)
    locale = mgr.GetDefaultLocale()
    self.assertEqual(locale, 'en')

  def testValidateModels(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    model1 = mgr.ValidateDimensionAndValue('model', 'iPencil1')
    model2 = mgr.ValidateDimensionAndValue('model', 'iPen3')
    self.assertEqual(model1, 'iPencil1')
    self.assertEqual(model2, 'iPen3')

  def testValidateVersionIds(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    ver1 = mgr.ValidateDimensionAndValue('version', '5.1')
    ver2 = mgr.ValidateDimensionAndValue('version', '7.2')
    self.assertEqual(ver1, '5.1')
    self.assertEqual(ver2, '7.2')

  # TODO(b/78015882): add more locales/orientations when supported for iOS.

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testValidateLocales(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    l1 = mgr.ValidateDimensionAndValue('locale', 'en')
    self.assertEqual(l1, 'en')

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testValidateOrientation(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    o1 = mgr.ValidateDimensionAndValue('orientation', 'portrait')
    self.assertEqual(o1, 'portrait')

  def testValidateModel_InvalidValue(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    with self.assertRaises(exceptions.ModelNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('model', 'iPear')
    self.assertIn("'iPear' is not a valid model", ex_ctx.exception.message)

  def testValidateVersion_InvalidValue(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    with self.assertRaises(exceptions.VersionNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('version', '99')
    self.assertIn("'99' is not a valid OS version", ex_ctx.exception.message)

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testValidateLocale_InvalidValuel(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    with self.assertRaises(exceptions.LocaleNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('locale', 'mtv')
    self.assertIn("'mtv' is not a valid locale", ex_ctx.exception.message)

  @test_case.Filters.skip('Need ios locale/orientation support.', 'b/78015882')
  def testValidateOrientation_InvalidValue(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    with self.assertRaises(exceptions.OrientationNotFoundError) as ex_ctx:
      mgr.ValidateDimensionAndValue('orientation', 'diagonal')
    self.assertIn("'diagonal' is not a valid device orientation",
                  ex_ctx.exception.message)

  def testValidateDimension_InvalidDimensionName(self):
    catalog = fake_catalogs.FakeIosCatalog()
    mgr = catalog_manager.IosCatalogManager(catalog)
    with self.assertRaises(exceptions.InvalidIosDimensionNameError) as ex_ctx:
      mgr.ValidateDimensionAndValue('clone', 'iPear')
    self.assertIn("'clone' is not a valid dimension", ex_ctx.exception.message)


if __name__ == '__main__':
  test_case.main()
