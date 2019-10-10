# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Unit tests for the yaml_printer module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import yaml_printer
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base


class YamlPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer('yaml')

  def testEmptyCase(self):
    self._printer.Finish()
    self.AssertOutputEquals('')

  def testSingleStreamedResourceCase(self):
    for resource in self.CreateResourceList(1):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        size: 0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))

  def testSingleResourceCase(self):
    resource = list(self.CreateResourceList(1))[0]
    self._printer.PrintSingleRecord(resource)
    self.AssertOutputEquals(
        textwrap.dedent("""\
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        size: 0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))

  def testMultipleResourceCase(self):
    generator = self.CreateResourceList(3)

    self.AssertOutputEquals('')

    self._printer.AddRecord(next(generator))
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        size: 0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))

    self._printer.AddRecord(next(generator))

    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        size: 0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        ---
        SelfLink: http://g/selfie/az-1
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.1
        name: my-instance-az-1
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.1
        size: 11
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))

    self._printer.AddRecord(next(generator))
    self.AssertOutputEquals(
        textwrap.dedent("""\
        ---
        SelfLink: http://g/selfie/a-0
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.2
        name: my-instance-a-0
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.0
        size: 0
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        ---
        SelfLink: http://g/selfie/az-1
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.1
        name: my-instance-az-1
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.1
        size: 11
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        ---
        SelfLink: http://g/selfie/azz-2
        kind: compute#instance
        labels:
          empty: ''
          full: value
          "\\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F": "\\xAE\\u01D6\\u026C\\u0258\\u03C2"
        metadata:
          items:
          - key: a
            value: b
          - key: c
            value: d
          - key: e
            value: f
          - key: g
            value: h
          kind: compute#metadata.0
        name: my-instance-azz-2
        networkInterfaces:
        - accessConfigs:
          - kind: compute#accessConfig
            name: External NAT
            natIP: 74.125.239.110
            type: ONE_TO_ONE_NAT
          name: nic0
          network: default
          networkIP: 10.240.150.2
        size: 2
        unicode: "python 2 \\u1E72\\u1F94\\u1E2F\\xA2\\u25CE\\u217E\\u212F \\u1E67\\u028A\\xA2\\u043A\\
          \\u1E67"
        """))


class YamlPrintTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._resources = [{'a': 1, 'b': 2, 'c': 3}]

  def testSinglePrint(self):
    resource_printer.Print(self._resources[0], 'yaml',
                           single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        a: 1
        b: 2
        c: 3
        """))

  def testPrint(self):
    resource_printer.Print(self._resources, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        a: 1
        b: 2
        c: 3
        """))

  def testPrintProjection(self):
    resource_printer.Print(self._resources, 'yaml(a,c)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        a: 1
        c: 3
        """))

  def testPrintEmptyDict(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: {}
        full:
          FAIL: 0
          PASS: 1
        """))

  def testPrintEmptyDictProjection(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'yaml(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: {}
        full:
          FAIL: 0
          PASS: 1
        """))

  def testPrintListEmpty(self):
    resource = [{'empty': []}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: []
        """))

  def testPrintListEmptyFully(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: []
        full:
        - PASS
        - FAIL
        """))

  def testPrintListProjectionEmpty(self):
    resource = [{'empty': []}]
    resource_printer.Print(resource, 'yaml(empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: []
        """))

  def testPrintListProjectionDictFail(self):

    class TestDict(dict):

      def __getattr__(self, unused_attr):
        raise AttributeError()

    resource = [TestDict()]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        --- {}
        """))

  def testPrintListProjectionListFail(self):

    class TestList(list):

      def __getattr__(self, unused_attr):
        raise AttributeError()

    resource = [TestList()]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        --- []
        """))

  def testPrintListProjectionEmptyFull(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: []
        full:
        - PASS
        - FAIL
        """))

  def testPrintUnicodeLines(self):
    self.SetEncoding('utf-8')
    resource = [{'prose': 'python\n2\nṲᾔḯ¢◎ⅾℯ\nṧʊ¢кṧ\n'}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        prose: |
          python
          2
          Ṳᾔḯ¢◎ⅾℯ
          ṧʊ¢кṧ
        """))

  def testPrintIterEmpty(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        """))

  def testPrintIterEmptyFull(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        full:
        - PASS
        - FAIL
        """))

  def testPrintIterProjectionEmpty(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml(empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        """))

  def testPrintIterProjectionEmptyFull(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        full:
        - PASS
        - FAIL
        """))

  def testPrintIterEmptyNoUndefined(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml[no-undefined]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
          null
        """))

  def testPrintIterEmptyFullNoUndefined(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml[no-undefined]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        full:
        - PASS
        - FAIL
        """))

  def testPrintIterProjectionEmptyNoUndefined(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml[no-undefined](empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        """))

  def testPrintIterProjectionEmptyFullNoUndefined(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml[no-undefined](empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: null
        full:
        - PASS
        - FAIL
        """))

  def testPrintIterEmptyNoUndefinedWithNullString(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml[no-undefined,null="(unset)"]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
          (unset)
        """))

  def testPrintIterEmptyWithNullString(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml[null="(unset)"]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: (unset)
        """))

  def testPrintIterEmptyFullWithNullString(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml[null="(unset)"]')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: (unset)
        full:
        - PASS
        - FAIL
        """))

  def testPrintIterProjectionEmptyWithNullString(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'yaml[null="(unset)"](empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: (unset)
        """))

  def testPrintIterProjectionEmptyFullWithNullString(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'yaml[null="(unset)"](empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        empty: (unset)
        full:
        - PASS
        - FAIL
        """))

  def testPrintBooleanVersion11(self):
    resource = [{'falsy': ['false', 'no', 'off', 'other'],
                 'truthy': ['true', 'yes', 'on', 'other']}]
    resource_printer.Print(resource, 'yaml[version=1.1]')
    self.AssertOutputEquals(textwrap.dedent("""\
        %YAML 1.1
        ---
        falsy:
        - 'false'
        - 'no'
        - 'off'
        - other
        truthy:
        - 'true'
        - 'yes'
        - 'on'
        - other
        """))

  def testPrintBooleanProjectionVersion11(self):
    resource = [{'truthy': ['true', 'yes', 'on', 'other']}]
    resource_printer.Print(resource, 'yaml[version=1.1](truthy)')
    self.AssertOutputEquals(textwrap.dedent("""\
        %YAML 1.1
        ---
        truthy:
        - 'true'
        - 'yes'
        - 'on'
        - other
        """))

  def testPrintBooleanVersion12(self):
    resource = [{'falsy': ['false', 'no', 'off', 'other'],
                 'truthy': ['true', 'yes', 'on', 'other']}]
    resource_printer.Print(resource, 'yaml[version=1.2]')
    self.AssertOutputEquals(textwrap.dedent("""\
        %YAML 1.2
        ---
        falsy:
        - 'false'
        - no
        - off
        - other
        truthy:
        - 'true'
        - yes
        - on
        - other
        """))

  def testPrintBooleanProjectionVersion12(self):
    resource = [{'truthy': ['true', 'yes', 'on', 'other']}]
    resource_printer.Print(resource, 'yaml[version=1.2](truthy)')
    self.AssertOutputEquals(textwrap.dedent("""\
        %YAML 1.2
        ---
        truthy:
        - 'true'
        - yes
        - on
        - other
        """))

  def testPrintOrderedDictSome(self):
    resource_printer.Print(self.ordered_dict_resource,
                           ':(allowed.list())'
                           'yaml(name,network,sourceRanges,allowed)')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        allowed:
        - IPProtocol: tcp
          ports:
          - '2376'
        name: allow-gae-builder
        network: default
        sourceRanges:
        - 0.0.0.0/0
        """))

  def testPrintOrderedDictAll(self):
    resource_printer.Print(self.ordered_dict_resource, 'yaml')
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        allowed:
        - IPProtocol: tcp
          ports:
          - '2376'
        creationTimestamp: '2015-05-20T08:14:24.654-07:00'
        description: ''
        id: '123456789'
        kind: compute#firewall
        name: allow-gae-builder
        network: default
        sourceRanges:
        - 0.0.0.0/0
        """))

  def testPrintOrderedDictPreserveOrder(self):
    yaml_printer.YamlPrinter(
        name='yaml',
        projector=resource_projector.IdentityProjector(),
    ).Print(self.ordered_dict_resource)
    self.AssertOutputEquals(textwrap.dedent("""\
        ---
        allowed:
        - IPProtocol: tcp
          ports:
          - '2376'
        description: ''
        name: allow-gae-builder
        id: '123456789'
        network: default
        sourceRanges:
        - 0.0.0.0/0
        kind: compute#firewall
        creationTimestamp: '2015-05-20T08:14:24.654-07:00'
        """))


class YamlPrintTextTest(resource_printer_test_base.Base):

  def testText(self):
    resource_printer.Print(self.text_resource, 'yaml', single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        a: no leading or trailing space
        b: '  leading space'
        c: 'trailing space  '
        d: '  surrounded by space  '
        e: |2-
           Leading space.
          Trailing space.  \

            Leading and Trailing.  \

        f: |-
          This is the first line.
          And the middle line.
          Finally at last.
        """))


class YamlPrintFloatTest(resource_printer_test_base.Base):

  def testFloat(self):
    resource_printer.Print(self.float_resource, 'yaml', single=True)
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


class YamlPrivateAttributeTest(sdk_test_base.WithLogCapture,
                               resource_printer_test_base.Base):

  _SECRET = 'too-many-secrets'  # yaml write tokens on separate lines
  _RESOURCE = [{'message': _SECRET}]

  def testYamlNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'yaml(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testYamlNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'yaml(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testYamlPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testYamlPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testYamlNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'yaml(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testYamlPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testYamlPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testYamlPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testYamlPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]yaml(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


if __name__ == '__main__':
  resource_printer_test_base.main()
