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

"""Unit tests for resource_printer.MultiPrinter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer
from tests.lib.core.resource import resource_printer_test_base


class MultiPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer(
        'multi(metadata:format=json, networkInterfaces:format="table(name, '
        'network, networkIP)")')

  def testEmpty(self):
    self._printer.Finish()
    self.AssertOutputEquals('')

  def testSingleResource(self):
    resource = list(self.CreateResourceList(1))[0]
    self._printer.PrintSingleRecord(resource)
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
""")

  def testIntermingledMultipleAndSingleResource(self):
    for i, resource in enumerate(self.CreateResourceList(5)):
      if i == 2:
        self._printer.PrintSingleRecord(resource)
      else:
        self._printer.AddRecord(resource)
    self._printer.Finish()

    self.maxDiff = None
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.1"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.1
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.0"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.2
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.3
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.1"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.4
""")

  def testSingleStreamedResource(self):
    for resource in self.CreateResourceList(1):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
""")

  def testMultipleResource(self):
    for resource in self.CreateResourceList(3):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.1"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.1
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.0"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.2
""")


class MultiPrintTest(resource_printer_test_base.Base):

  def testPrintWithBadFormat(self):
    with self.assertRaises(resource_printer.UnknownFormatError):
      resource_printer.Print(
          [{'a': 1, 'b': 2, 'c': 3}],
          'multi(metadata:format=BadFormat)')

  def testPrintWithMissingFormat(self):
    with self.assertRaises(resource_printer.ProjectionFormatRequiredError):
      resource_printer.Print(
          [{'a': 1, 'b': 2, 'c': 3}],
          'multi(metadata:format=json, networkInterfaces)')

  def testPrintWithMultiFormat(self):
    resource_printer.Print(
        self.CreateResourceList(2),
        'multi(metadata:format=json, networkInterfaces:format="table(name, '
        'network, networkIP)")')
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.1"
}
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.1
""")

  def testPrintWithSeparatorSingleResource(self):
    resource_printer.Print(
        list(self.CreateResourceList(1))[0],
        'multi[separator="---\n"](metadata:format=json, networkInterfaces:format="table(name, '
        'network, networkIP)")')
    self.AssertOutputEquals("""\
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
---
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
""")

  def testPrintWithSeparatorMultipleResources(self):
    resource_printer.Print(
        self.CreateResourceList(2),
        'multi[separator="---\n"](metadata:format=json, networkInterfaces:format="table(name, '
        'network, networkIP)")')
    self.AssertOutputEquals("""\
---
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.2"
}
---
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.0
---
{
  "items": [
    {
      "key": "a",
      "value": "b"
    },
    {
      "key": "c",
      "value": "d"
    },
    {
      "key": "e",
      "value": "f"
    },
    {
      "key": "g",
      "value": "h"
    }
  ],
  "kind": "compute#metadata.1"
}
---
NAME  NETWORK  NETWORK_IP
nic0  default  10.240.150.1
""")


if __name__ == '__main__':
  resource_printer_test_base.main()
