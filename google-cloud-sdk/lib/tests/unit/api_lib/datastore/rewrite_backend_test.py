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
"""Tests for Cloud Datastore rewrite backends."""

from googlecloudsdk.api_lib.datastore import rewrite_backend
from googlecloudsdk.core.resource import resource_exceptions
from tests.lib import test_case


class OperationsRewriteBackendTest(test_case.Base):
  """Tests for the OperationsRewriteBackend."""

  def SetUp(self):
    self.backend = rewrite_backend.OperationsRewriteBackend()

  def assertTransform(self, input_expr, expected_output):
    frontend_expr, backend_expr = self.backend.Rewrite(input_expr)
    # No support for partial rewrite
    self.assertIsNone(frontend_expr)
    self.assertEqual(expected_output, backend_expr)

  def AssertInvalidTransform(self, input_expr):
    with self.assertRaises(resource_exceptions.ExpressionSyntaxError):
      self.backend.Rewrite(input_expr)

  def testLabels(self):
    self.assertTransform('label.foo:bar', 'metadata.common.labels.foo=bar')
    self.assertTransform('label.foo:"bar with space"',
                         'metadata.common.labels.foo="bar with space"')
    self.assertTransform('label."quoted.label."=baz',
                         'metadata.common.labels."quoted.label."=baz')
    self.assertTransform('label."quoted.label."="also quoted"',
                         'metadata.common.labels."quoted.label."="also quoted"')
    self.assertTransform('label."url.com/1/2_3.4"=bar',
                         'metadata.common.labels."url.com/1/2_3.4"=bar')
    # Backend supported, but not by parser.
    self.AssertInvalidTransform('label.url.com/1/2_3.4 = bar')

  def testAutoQuote(self):
    self.assertTransform('label.foo = foo\\bar',
                         'metadata.common.labels.foo="foo\\\\\\bar"')

  def testType(self):
    self.assertTransform('type:IMPORT_ENTITIES',
                         'metadata.common.operation_type=IMPORT_ENTITIES')
    self.assertTransform('type:export_entities',
                         'metadata.common.operation_type=export_entities')

  def testKind(self):
    self.assertTransform('kind:foo', 'metadata.entity_filter.kind=foo')
    self.assertTransform('kind:*', 'metadata.entity_filter.kind=*')

  def testNamespace(self):
    self.assertTransform('namespace:foo',
                         'metadata.entity_filter.namespace_id=foo')
    self.assertTransform('namespace:*', 'metadata.entity_filter.namespace_id=*')
    self.assertTransform('namespace:"(default)"',
                         'metadata.entity_filter.namespace_id=""')
    self.assertTransform('namespace:""',
                         'metadata.entity_filter.namespace_id=""')
    self.assertTransform('namespace:\'\'',
                         'metadata.entity_filter.namespace_id=""')

  def testConjunction(self):
    self.assertTransform('label.foo:bar kind:baz',
                         'metadata.common.labels.foo=bar '
                         'AND metadata.entity_filter.kind=baz')
    self.assertTransform('label.foo:bar AND kind:baz AND namespace:ns',
                         'metadata.common.labels.foo=bar '
                         'AND (metadata.entity_filter.kind=baz '
                         'AND metadata.entity_filter.namespace_id=ns)')

  def testNoTranslation(self):
    frontend_expr, backend_expr = self.backend.Rewrite('filter_without_op')
    self.assertEqual('filter_without_op', frontend_expr)
    self.assertIsNone(backend_expr)


if __name__ == '__main__':
  test_case.main()
