# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Unit tests for the flattened_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base

from six.moves import range  # pylint: disable=redefined-builtin


class FlattenedPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf-8')
    self._printer = resource_printer.Printer('flattened')

  def testEmptyCase(self):
    self._printer.Finish()
    self.AssertOutputEquals('')

  def testSingleResourceCase(self):
    [resource] = self.CreateResourceList(1)
    self._printer.PrintSingleRecord(resource)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        SelfLink:                                    http://g/selfie/a-0
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.2
        name:                                        my-instance-a-0
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.0
        size:                                        0
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

  def testSingleStreamedResourceCase(self):
    for resource in self.CreateResourceList(1):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink:                                    http://g/selfie/a-0
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.2
        name:                                        my-instance-a-0
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.0
        size:                                        0
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

  def testMultipleResourceCase(self):
    generator = self.CreateResourceList(3)

    self.AssertOutputEquals('')

    self._printer.AddRecord(next(generator))
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink:                                    http://g/selfie/a-0
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.2
        name:                                        my-instance-a-0
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.0
        size:                                        0
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

    self._printer.AddRecord(next(generator))
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink:                                    http://g/selfie/a-0
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.2
        name:                                        my-instance-a-0
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.0
        size:                                        0
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        ---
        SelfLink:                                    http://g/selfie/az-1
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.1
        name:                                        my-instance-az-1
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.1
        size:                                        11
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

    self._printer.AddRecord(next(generator))
    self._printer.Finish()
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink:                                    http://g/selfie/a-0
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.2
        name:                                        my-instance-a-0
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.0
        size:                                        0
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        ---
        SelfLink:                                    http://g/selfie/az-1
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.1
        name:                                        my-instance-az-1
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.1
        size:                                        11
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        ---
        SelfLink:                                    http://g/selfie/azz-2
        kind:                                        compute#instance
        labels.empty:                                \

        labels.full:                                 value
        labels.Ṳᾔḯ¢◎ⅾℯ:                              ®ǖɬɘς
        metadata.items[0].key:                       a
        metadata.items[0].value:                     b
        metadata.items[1].key:                       c
        metadata.items[1].value:                     d
        metadata.items[2].key:                       e
        metadata.items[2].value:                     f
        metadata.items[3].key:                       g
        metadata.items[3].value:                     h
        metadata.kind:                               compute#metadata.0
        name:                                        my-instance-azz-2
        networkInterfaces[0].accessConfigs[0].kind:  compute#accessConfig
        networkInterfaces[0].accessConfigs[0].name:  External NAT
        networkInterfaces[0].accessConfigs[0].natIP: 74.125.239.110
        networkInterfaces[0].accessConfigs[0].type:  ONE_TO_ONE_NAT
        networkInterfaces[0].name:                   nic0
        networkInterfaces[0].network:                default
        networkInterfaces[0].networkIP:              10.240.150.2
        size:                                        2
        unicode:                                     python 2 Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
        """))

  def testListHandling(self):
    """Ensures that indices are ordered numerically."""
    self._printer.AddRecord(range(20))
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        [0]:  0
        [1]:  1
        [2]:  2
        [3]:  3
        [4]:  4
        [5]:  5
        [6]:  6
        [7]:  7
        [8]:  8
        [9]:  9
        [10]: 10
        [11]: 11
        [12]: 12
        [13]: 13
        [14]: 14
        [15]: 15
        [16]: 16
        [17]: 17
        [18]: 18
        [19]: 19
        """))


class FlattenedPrinterAttributeTest(resource_printer_test_base.Base):

  def SetUp(self):
    self.SetEncoding('utf-8')

  def testDefaultPad(self):
    self.Print(style='flattened')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        id:    1267
        name:  Ṁöë
        quote: .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
        ---
        id:    1245
        name:  Larry
        quote: ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
        ---
        id:    lrlrlrl
        name:  Shemp
        quote: Hey, Ṁöë! Hey, Larry!
        ---
        id:    1234
        name:  Curly
        quote: Søɨŧɇnłɏ!
        """))

  def testNoPad(self):
    self.Print(style='flattened', count=6, attributes='[no-pad]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        id: 1267
        name: Ṁöë
        quote: .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
        ---
        id: 1245
        name: Larry
        quote: ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
        ---
        id: lrlrlrl
        name: Shemp
        quote: Hey, Ṁöë! Hey, Larry!
        ---
        id: 1234
        name: Curly
        quote: Søɨŧɇnłɏ!
        ---
        id[0]: new
        id[1]: 6789
        name: Joe
        quote: Oh, cut it ouuuuuut!
        ---
        id.new: 890
        name: Curly Joe
        quote: One of these days, you're gonna poke my eyes out.
        """))

  def testNoPadSeparator(self):
    self.Print(style='flattened', count=6, attributes='[no-pad,separator=" "]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        id 1267
        name Ṁöë
        quote .TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW
        ---
        id 1245
        name Larry
        quote ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.
        ---
        id lrlrlrl
        name Shemp
        quote Hey, Ṁöë! Hey, Larry!
        ---
        id 1234
        name Curly
        quote Søɨŧɇnłɏ!
        ---
        id[0] new
        id[1] 6789
        name Joe
        quote Oh, cut it ouuuuuut!
        ---
        id.new 890
        name Curly Joe
        quote One of these days, you're gonna poke my eyes out.
        """))


class FlattenedPrintTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._resources = [{'a': 1, 'b': 2, 'c': 3}]

  def testSinglePrintWithKeys(self):
    self._resources[0]['d'] = [1, 2, 3]
    resource_printer.Print(self._resources[0], 'flattened',
                           single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        a:    1
        b:    2
        c:    3
        d[0]: 1
        d[1]: 2
        d[2]: 3
        """))

  def testPrintWithKeys(self):
    self._resources[0]['d'] = [1, 2, 3]
    resource_printer.Print(self._resources, 'flattened')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        a:    1
        b:    2
        c:    3
        d[0]: 1
        d[1]: 2
        d[2]: 3
        """))

  def testPrintProjectionWithKeys(self):
    self._resources[0]['d'] = [1, 2, 3]
    resource_printer.Print(self._resources, 'flattened(a,d)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        a:    1
        d[0]: 1
        d[1]: 2
        d[2]: 3
        """))

  def testPrintEmptyDict(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'flattened')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty:     {}
        full.FAIL: 0
        full.PASS: 1
        """))

  def testPrintEmptyDictProjection(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'flattened(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty:     {}
        full.FAIL: 0
        full.PASS: 1
        """))

  def testPrintEmptyList(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'flattened')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty:   []
        full[0]: PASS
        full[1]: FAIL
        """))

  def testPrintEmptyListProjection(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'flattened(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty:   []
        full[0]: PASS
        full[1]: FAIL
        """))


class FlattenedResourceNoneTest(resource_printer_test_base.Base):

  def testFlattenedResourceNone(self):
    resource_printer.Print(None, 'flattened')
    self.AssertOutputEquals('')


class FlattenedPrintTextTest(resource_printer_test_base.Base):

  def testFlattenedPrintText(self):
    resource_printer.Print(self.text_resource, 'flattened', single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        a: no leading or trailing space
        b: "  leading space"
        c: "trailing space  "
        d: "  surrounded by space  "
        e: " Leading space.\\nTrailing space.  \\n  Leading and Trailing.  "
        f: "This is the first line.\\nAnd the middle line.\\nFinally at last."
        """))


class FlattenedPrivateAttributeTest(sdk_test_base.WithLogCapture,
                                    resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testFlattenedNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'flattened(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testFlattenedNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'flattened(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testFlattenedPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testFlattenedPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testFlattenedNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'flattened(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testFlattenedPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testFlattenedPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testFlattenedPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testFlattenedPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]flattened(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


class FlattenedPrintFloatTest(resource_printer_test_base.Base):

  def testFloat(self):
    resource_printer.Print(self.float_resource, 'flattened', single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        a: 1.0
        b: -1.0
        c: 1.00001
        d: -1.00009
        e: 1.0009
        f: -1.009
        g: 1.009
        h: -1.09
        i: 1.9
        j: -1.33333
        k: 1.66667
        l: -12.3457
        m: 123.457
        n: -1234.57
        o: 12345.7
        p: -123456.8
        q: 1234567.9
        r: -12345678.9
        s: 123456789.0
        t: -1.23457e+09
        """))


if __name__ == '__main__':
  resource_printer_test_base.main()
