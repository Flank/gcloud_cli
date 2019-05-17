# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the resource_topics module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_topics
from googlecloudsdk.core.resource import resource_transform
from tests.lib import test_case


class ResourceTopicsTest(test_case.Base):

  def SetUp(self):
    self.maxDiff = None  # Show assertMutiLineEqual() diffs.

  def testResourceDescriptionFormat(self):
    expected = """\
Most *gcloud* commands return a list of resources on success. By default they
are pretty-printed on the standard output. The
*--format=*_NAME_[_ATTRIBUTES_]*(*_PROJECTION_*)* and
*--filter=*_EXPRESSION_ flags along with projections can be used to format and
change the default output to a more meaningful result.

Use the `--format` flag to change the default output format of a command.   Resource formats are described in detail below.

Use the `--filter` flag to select resources to be listed. For details run $ gcloud topic filters.

Use resource-keys to reach resource items through a unique path of names from the root. For details run $ gcloud topic resource-keys.

Use projections to list a subset of resource keys in a resource.   For details run $ gcloud topic projections.

Note: To refer to a list of fields you can sort, filter, and format by for
each resource, you can run a list command with the format set to `text` or
`json`. For
example, $ gcloud compute instances list --limit=1 --format=text.

To work through an interactive tutorial about using the filter and format
flags instead, see: https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/cloud-shell-tutorials&page=editor&tutorial=cloudsdk/tutorial.md
"""
    actual = resource_topics.ResourceDescription('format')
    self.assertEqual(expected, actual)

  def testResourceDescriptionKey(self):
    expected = """\
Most *gcloud* commands return a list of resources on success. By default they
are pretty-printed on the standard output. The
*--format=*_NAME_[_ATTRIBUTES_]*(*_PROJECTION_*)* and
*--filter=*_EXPRESSION_ flags along with projections can be used to format and
change the default output to a more meaningful result.

Use the `--format` flag to change the default output format of a command.   For details run $ gcloud topic formats.

Use the `--filter` flag to select resources to be listed. For details run $ gcloud topic filters.

Use resource-keys to reach resource items through a unique path of names from the root. Resource keys are described in detail below.

Use projections to list a subset of resource keys in a resource.   For details run $ gcloud topic projections.

Note: To refer to a list of fields you can sort, filter, and format by for
each resource, you can run a list command with the format set to `text` or
`json`. For
example, $ gcloud compute instances list --limit=1 --format=text.

To work through an interactive tutorial about using the filter and format
flags instead, see: https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/cloud-shell-tutorials&page=editor&tutorial=cloudsdk/tutorial.md
"""
    actual = resource_topics.ResourceDescription('key')
    self.assertEqual(expected, actual)

  def testResourceDescriptionProjection(self):
    expected = """\
Most *gcloud* commands return a list of resources on success. By default they
are pretty-printed on the standard output. The
*--format=*_NAME_[_ATTRIBUTES_]*(*_PROJECTION_*)* and
*--filter=*_EXPRESSION_ flags along with projections can be used to format and
change the default output to a more meaningful result.

Use the `--format` flag to change the default output format of a command.   For details run $ gcloud topic formats.

Use the `--filter` flag to select resources to be listed. For details run $ gcloud topic filters.

Use resource-keys to reach resource items through a unique path of names from the root. For details run $ gcloud topic resource-keys.

Use projections to list a subset of resource keys in a resource.   Resource projections are described in detail below.

Note: To refer to a list of fields you can sort, filter, and format by for
each resource, you can run a list command with the format set to `text` or
`json`. For
example, $ gcloud compute instances list --limit=1 --format=text.

To work through an interactive tutorial about using the filter and format
flags instead, see: https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/cloud-shell-tutorials&page=editor&tutorial=cloudsdk/tutorial.md
"""
    actual = resource_topics.ResourceDescription('projection')
    self.assertEqual(expected, actual)

  def testResourceDescriptionUnknown(self):
    with self.assertRaisesRegex(ValueError, r'Expected one of \[filter,format,'
                                r'key,projection\], got \[unknown\].'):
      resource_topics.ResourceDescription('unknown')

  def testFormatRegistryDescriptions(self):

    class ComplexPrinter(object):
      """This line should be skipped.

      This line describes the complex format.
      It needs a few lines of details.

      Printer attributes:
        ellipse: Draws an ellipse around the output.
        no-bar: Eliminates bar from the foo.

      Attributes:
        _rows: This line should not be seen.
      """

    class DefaultPrinter(ComplexPrinter):
      """An alias for YamlPrinter.

      An alias for the yaml format.
      """

    class NonePrinter(object):
      """Disables formatted output.

      Disables formatted output.
      """

      def __new__(cls, **unused_kwargs):
        return None

    class SimplePrinter(object):
      """This line should be skipped.

      This line describes the simple format.
      """

    registry = {
        'complex': ComplexPrinter,
        'default': DefaultPrinter,
        'none': NonePrinter,
        'simple': SimplePrinter,
        }

    self.StartObjectPatch(
        resource_printer, 'GetFormatRegistry').side_effect = [registry]
    expected = """\
The formats and format specific attributes are:

*complex*::
This line describes the complex format. It needs a few lines of details.
+
The format attributes are:

*ellipse*:::
Draws an ellipse around the output.
*no-bar*:::
Eliminates bar from the foo.

*default*::
An alias for the yaml format.

*none*::
Disables formatted output.

*simple*::
This line describes the simple format.

All formats have these attributes:
+
*disable*::
Disables formatted output and does not consume the resources.
*json-decode*::
Decodes string values that are JSON compact encodings of list and dictionary objects. This may become the default.
*pager*::
If True, sends output to a pager.
*private*::
Disables log file output. Use this for sensitive resource data that should not be displayed in log files. Explicit command line IO redirection overrides this attribute.
*transforms*::
Apply projection transforms to the resource values. The default is format specific. Use *no-transforms* to disable.

"""
    actual = resource_topics.FormatRegistryDescriptions()
    self.assertMultiLineEqual(expected, actual)

  def testTransformRegistryDescriptions(self):

    def TransformBar(r, projection, *args):
      """Returns the first non-empty .name attribute value for name in args.

      Args:
        r: A JSON-serializable object.
        projection: Another arg like **kwargs that should not be documented.
        *args: Names to check for resource attribute values,

      Returns:
        The first non-empty r.name value for name in args, '' otherwise.

      Example:
        x.firstof(bar_foo, barFoo, BarFoo, BAR_FOO):::
        Checks x.bar_foo, x.barFoo, x.BarFoo, and x.BAR_FOO in order for the
        first non-empty value.
      """
      return '{0}{1}{2}'.format(r, projection, args)

    def TransformFoo(r, encoding, undefined='T', unused_unit=1, **kwargs):
      """Formats to a numeric ISO time format.

      Args:
        r: A JSON-serializable object.
        encoding: An old bug would document this formal with a default value.
        undefined: Returns this if the resource does not have an isoformat()
          attribute.
        unused_unit: Some well-documented parameter.
        **kwargs: Extra junk that should not be in the docs.

      Returns:
        The numeric ISO time format for r or undefined if r is not a time.
      """
      return '{0}{1}{2}{3}{4}'.format(
          r, encoding, undefined, unused_unit, kwargs)

    def TransformBool(r, affirmative=True, negatory=False):
      """Boolean valued kwarg test.

      Args:
        r: A JSON-serializable object.
        affirmative: Absolutely yes.
        negatory: Unequivocally no. Disabled by default.

      Returns:
        The Boolean kwarg values.
      """
      return '{0}{1}{2}'.format(r, affirmative, negatory)

    transforms = {
        'bar': TransformBar,
        'foo': TransformFoo,
        'bool': TransformBool,
        }

    def MockGetTransforms(component=None):
      # This hijacks the builtin transforms.
      return None if component else transforms

    self.StartObjectPatch(
        resource_transform, 'GetTransforms').side_effect = MockGetTransforms
    expected = """\

The builtin transform functions are:


*bar*(args)::
Returns the first non-empty .name attribute value for name in args.
+
The arguments are:
+
*```args```*:::
Names to check for resource attribute values,
:::
+
For example:
+
x.firstof(bar_foo, barFoo, BarFoo, BAR_FOO):::
Checks x.bar_foo, x.barFoo, x.BarFoo, and x.BAR_FOO in order for the first non-empty value.


*bool*(affirmative=true, negatory=false)::
Boolean valued kwarg test.
+
The arguments are:
+
*```affirmative```*:::
Absolutely yes.
:::
*```negatory```*:::
Unequivocally no. Disabled by default.
:::


*foo*(encoding, undefined="T", unit=1)::
Formats to a numeric ISO time format.
+
The arguments are:
+
*```encoding```*:::
An old bug would document this formal with a default value.
:::
*```undefined```*:::
Returns this if the resource does not have an isoformat()       attribute.
:::
*```unit```*:::
Some well-documented parameter.
:::

"""
    def _MockGetApiTransforms(api):
      if api == 'builtin':
        return resource_transform.GetTransforms()
      return None

    self.StartObjectPatch(resource_topics, '_GetApiTransforms',
                          side_effect=_MockGetApiTransforms)
    actual = resource_topics.TransformRegistryDescriptions()
    self.assertMultiLineEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
