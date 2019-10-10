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

"""Unit tests for the googlecloudsdk.core.util.importing module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.core.util import importing
from tests.lib import test_case

TEST_PACKAGE_NAME = (
    'tests.unit.core.util.testdata.importing_test_package')
TEST_MODULE_NAME = TEST_PACKAGE_NAME + '.test_module'


class ImportingTest(test_case.Base):

  def SetUp(self):
    if TEST_PACKAGE_NAME in sys.modules:
      del sys.modules[TEST_PACKAGE_NAME]
    if TEST_MODULE_NAME in sys.modules:
      del sys.modules[TEST_MODULE_NAME]

  def AssertNotLoaded(self, module):
    self.assertTrue(getattr(module, 'IS_UNLOADED_LAZY_MODULE', False))

  def AssertLoaded(self, module):
    self.assertFalse(getattr(module, 'IS_UNLOADED_LAZY_MODULE', False))

  def testLazyLoadModule(self):
    module = importing.lazy_load_module(TEST_MODULE_NAME)
    self.assertIsInstance(module, importing.LazyImporter)
    self.AssertNotLoaded(module)

  def testLazyLoadModuleNonexistentModule(self):
    with self.assertRaises(ImportError):
      importing.lazy_load_module('nonexistent.module')

  def testLazyLoadModuleParent(self):
    importing.lazy_load_module(TEST_MODULE_NAME)
    parent = sys.modules[TEST_PACKAGE_NAME]
    self.assertIsInstance(parent, importing.LazyImporter)
    self.AssertNotLoaded(parent)

  def testImportLazyModule(self):
    # pylint: disable=g-import-not-at-top
    # pylint: disable=reimported
    module = importing.lazy_load_module(TEST_MODULE_NAME)
    from tests.unit.core.util.testdata.importing_test_package import test_module
    self.assertIsInstance(module, importing.LazyImporter)
    self.assertEqual(module, test_module)

  def testImportChildDoesNotLoadLazyParent(self):
    # pylint: disable=g-import-not-at-top
    # pylint: disable=redefined-outer-name
    # pylint: disable=reimported
    # pylint: disable=unused-variable
    importing.lazy_load_module(TEST_MODULE_NAME)
    import tests.unit.core.util.testdata.importing_test_package.test_module
    parent = sys.modules[TEST_PACKAGE_NAME]
    self.AssertNotLoaded(parent)

  def testImportChildFromDoesNotLoadLazyParent(self):
    # pylint: disable=g-import-not-at-top
    # pylint: disable=reimported
    # pylint: disable=unused-variable
    importing.lazy_load_module(TEST_MODULE_NAME)
    from tests.unit.core.util.testdata.importing_test_package import test_module
    parent = sys.modules[TEST_PACKAGE_NAME]
    self.AssertNotLoaded(parent)

  def testLoadModule(self):
    module = importing.lazy_load_module(TEST_MODULE_NAME)
    self.AssertNotLoaded(module)
    importing._load_module(module)
    self.AssertLoaded(module)

  def testLoadLazyModuleAttribute(self):
    module = importing.lazy_load_module(TEST_MODULE_NAME)
    self.AssertNotLoaded(module)
    self.assertEqual('test_attribute', module.TEST_ATTRIBUTE)
    self.AssertLoaded(module)
    parent = sys.modules[TEST_PACKAGE_NAME]
    self.AssertLoaded(parent)
