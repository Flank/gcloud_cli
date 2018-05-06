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

"""Unit tests for the json_printer module."""

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import sys
import textwrap

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from tests.lib import sdk_test_base
from tests.lib.core.resource import resource_printer_test_base

import six


class JsonPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = resource_printer.Printer('json')

  def testEmpty(self):
    self._printer.Finish()
    self.AssertOutputEquals('[]\n')

  def testSingleResource(self):
    [resource] = self.CreateResourceList(1)
    self._printer.PrintSingleRecord(resource)
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "SelfLink": "http://g/selfie/a-0",
          "kind": "compute#instance",
          "labels": {
            "empty": "",
            "full": "value",
            "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
          },
          "metadata": {
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
          },
          "name": "my-instance-a-0",
          "networkInterfaces": [
            {
              "accessConfigs": [
                {
                  "kind": "compute#accessConfig",
                  "name": "External NAT",
                  "natIP": "74.125.239.110",
                  "type": "ONE_TO_ONE_NAT"
                }
              ],
              "name": "nic0",
              "network": "default",
              "networkIP": "10.240.150.0"
            }
          ],
          "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
        }
        """))

  def testIntermingledMultipleAndSingleResource(self):
    for i, resource in enumerate(self.CreateResourceList(5)):
      if i == 2:
        self._printer.PrintSingleRecord(resource)
      else:
        self._printer.AddRecord(resource)
    self._printer.Finish()

    self.maxDiff = None
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/az-1",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-az-1",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.1"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }
        ]
        {
          "SelfLink": "http://g/selfie/azz-2",
          "kind": "compute#instance",
          "labels": {
            "empty": "",
            "full": "value",
            "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
          },
          "metadata": {
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
          },
          "name": "my-instance-azz-2",
          "networkInterfaces": [
            {
              "accessConfigs": [
                {
                  "kind": "compute#accessConfig",
                  "name": "External NAT",
                  "natIP": "74.125.239.110",
                  "type": "ONE_TO_ONE_NAT"
                }
              ],
              "name": "nic0",
              "network": "default",
              "networkIP": "10.240.150.2"
            }
          ],
          "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
        }
        [
          {
            "SelfLink": "http://g/selfie/azzz-3",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-azzz-3",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.3"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/azzzz-4",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-azzzz-4",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.4"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }
        ]
        """))

  def testSingleStreamedResource(self):
    for resource in self.CreateResourceList(1):
      self._printer.AddRecord(resource)
    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }
        ]
        """))

  def testMultipleResource(self):
    resource = list(self.CreateResourceList(3))

    self._printer.AddRecord(resource[0])
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }"""))

    self._printer.AddRecord(resource[1])
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/az-1",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-az-1",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.1"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }"""))

    self._printer.AddRecord(resource[2])
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/az-1",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-az-1",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.1"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/azz-2",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-azz-2",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.2"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }"""))

    self._printer.Finish()
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "SelfLink": "http://g/selfie/a-0",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-a-0",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.0"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/az-1",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-az-1",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.1"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          },
          {
            "SelfLink": "http://g/selfie/azz-2",
            "kind": "compute#instance",
            "labels": {
              "empty": "",
              "full": "value",
              "\\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f": "\\u00ae\\u01d6\\u026c\\u0258\\u03c2"
            },
            "metadata": {
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
            },
            "name": "my-instance-azz-2",
            "networkInterfaces": [
              {
                "accessConfigs": [
                  {
                    "kind": "compute#accessConfig",
                    "name": "External NAT",
                    "natIP": "74.125.239.110",
                    "type": "ONE_TO_ONE_NAT"
                  }
                ],
                "name": "nic0",
                "network": "default",
                "networkIP": "10.240.150.2"
              }
            ],
            "unicode": "python 2 \\u1e72\\u1f94\\u1e2f\\u00a2\\u25ce\\u217e\\u212f \\u1e67\\u028a\\u00a2\\u043a\\u1e67"
          }
        ]
        """))


class JsonPrintTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._resources = [{'a': 1, 'b': 2, 'c': 3}]

  def testSinglePrint(self):
    resource_printer.Print(self._resources[0], 'json',
                           single=True)
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "a": 1,
          "b": 2,
          "c": 3
        }
        """))

  def testPrint(self):
    resource_printer.Print(self._resources, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "a": 1,
            "b": 2,
            "c": 3
          }
        ]
        """))

  def testPrintProjection(self):
    resource_printer.Print(self._resources, 'json(a,c)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "a": 1,
            "c": 3
          }
        ]
        """))

  def testPrintWithKeys(self):
    self._resources[0]['d'] = [1, 2, 3]
    resource_printer.Print(self._resources, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "a": 1,
            "b": 2,
            "c": 3,
            "d": [
              1,
              2,
              3
            ]
          }
        ]
        """))

  def testPrintProjectionWithKeys(self):
    self._resources[0]['d'] = [1, 2, 3]
    resource_printer.Print(self._resources, 'json(a,d)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "a": 1,
            "d": [
              1,
              2,
              3
            ]
          }
        ]
        """))

  def testPrintEmptyDict(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": {},
            "full": {
              "FAIL": 0,
              "PASS": 1
            }
          }
        ]
        """))

  def testPrintEmptyDictProjection(self):
    resource = [{'empty': {},
                 'full': {'PASS': 1, 'FAIL': 0}}]
    resource_printer.Print(resource, 'json(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": {},
            "full": {
              "FAIL": 0,
              "PASS": 1
            }
          }
        ]
        """))

  def testPrintEmptyList(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": [],
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))

  def testPrintEmptyListProjection(self):
    resource = [{'empty': [],
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": [],
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))

  def testPrintWithBadFormat(self):
    with self.assertRaises(resource_printer.UnknownFormatError):
      resource_printer.Print(self._resources, 'BadFormat')

  def testPrintDateTime(self):
    resource = [
        {
            'start': datetime.datetime(2015, 10, 21, 10, 11, 12, 0),
        }
    ]
    resource_printer.Print(resource, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {{
            "start": {{
              "datetime": "2015-10-21 10:11:12",
              "day": 21,{fold}
              "hour": 10,
              "microsecond": 0,
              "minute": 11,
              "month": 10,
              "second": 12,
              "year": 2015
            }}
          }}
        ]
        """.format(fold='\n              "fold": 0,' if six.PY3 else '')))

  def testPrintIterEmpty(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null
          }
        ]
        """))

  def testPrintIterEmptyFull(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null,
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))

  def testPrintIterProjectionEmpty(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'json(empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null
          }
        ]
        """))

  def testPrintIterProjectionEmptyFull(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json(empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null,
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))

  def testPrintIterEmptyNoUndefined(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'json[no-undefined]')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          null
        ]
        """))

  def testPrintIterEmptyFullNoUndefined(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json[no-undefined]')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))

  def testPrintIterProjectionEmptyNoUndefined(self):
    resource = [{'empty': iter([])}]
    resource_printer.Print(resource, 'json[no-undefined](empty)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null
          }
        ]
        """))

  def testPrintIterProjectionEmptyFullNoUndefined(self):
    resource = [{'empty': iter([]),
                 'full': ['PASS', 'FAIL']}]
    resource_printer.Print(resource, 'json[no-undefined](empty, full)')
    self.AssertOutputEquals(textwrap.dedent("""\
        [
          {
            "empty": null,
            "full": [
              "PASS",
              "FAIL"
            ]
          }
        ]
        """))


class JsonPrivateAttributeTest(sdk_test_base.WithLogCapture,
                               resource_printer_test_base.Base):

  _SECRET = 'too many secrets'
  _RESOURCE = [{'message': _SECRET}]

  def testJsonNoPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, 'json(message)', out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testJsonNoPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, 'json(message)', out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testJsonPrivateAttributeDefaultOut(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=None)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testJsonPrivateAttributeLogOut(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=log.out)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testJsonNoPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, 'json(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogContains(self._SECRET)

  def testJsonPrivateAttributeLogErr(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=log.err)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testJsonPrivateAttributeLogStatus(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=log.status)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testJsonPrivateAttributeStdout(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=sys.stdout)
    self.AssertOutputContains(self._SECRET)
    self.AssertErrNotContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)

  def testJsonPrivateAttributeStderr(self):
    resource_printer.Print(self._RESOURCE, '[private]json(message)',
                           out=sys.stderr)
    self.AssertOutputNotContains(self._SECRET)
    self.AssertErrContains(self._SECRET)
    self.AssertLogNotContains(self._SECRET)


if __name__ == '__main__':
  resource_printer_test_base.main()
