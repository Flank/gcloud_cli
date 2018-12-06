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
"""Tests for core/util/walker_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import walker_util
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_printer
from tests.lib import calliope_test_base
from tests.lib import test_case
import six


class WalkerUtilTest(calliope_test_base.CalliopeTestBase,
                     test_case.WithOutputCapture):

  def SetUp(self):
    # CheckContainsRegression() subtest info.
    self.subtests = 0
    self.failures = []

    # Load the mock CLI.
    self.cli = self.LoadTestCli('sdk4')

  def TearDown(self):
    console_attr.ResetConsoleAttr()
    if self.failures:
      self.fail('%d/%d subtests failed:\n%s\n' % (len(self.failures),
                                                  self.subtests,
                                                  '\n'.join(self.failures)))

  def CheckRegression(self, label, actual, expected, contains=False):
    """Checks if actual== expected.

    Appends a regression message to self.failures if actual != expected.
    The unit test fails if len(self.failures) != 0 in self.TearDown().

    Args:
      label: The regression label string.
      actual: The actual result string.
      expected: The expected result string.
      contains: Check for containment if True, exact match otherwise.
    """
    self.subtests += 1
    if expected not in actual if contains else expected != actual:
      self.failures.append('<<<EXPECTED {label}>>>\n{expected}\n'
                           '<<<ACTUAL>>>\n{actual}\n<<<END>>>'.format(
                               label=label, expected=expected, actual=actual))

  def testDevSiteGenerator(self):
    """Tests the DevSite generated directory file names and sizes."""
    devsite_directory = os.path.join(self.temp_path, 'devsite')
    walker_util.DevSiteGenerator(self.cli, devsite_directory).Walk()
    self.AssertDirectoryIsGolden(
        devsite_directory, __file__, 'walker_util', 'devsite.dir')

  def testDevSiteGeneratorFileContents(self):
    """Tests the DevSite _toc.yaml files and one group and command HTML file."""
    devsite_directory = os.path.join(self.temp_path, 'devsite')
    walker_util.DevSiteGenerator(self.cli, devsite_directory).Walk()

    files = {
        'beta/sdk/subgroup/subgroup-command-2.html': (True, """\
<html devsite="">
<head>
<title>gcloud beta sdk subgroup subgroup-command-2</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
"""),
        'alpha/_toc.yaml': (False, """\
toc:
- title: "gcloud alpha"
  path: /sdk/gcloud/reference/alpha
  section:
  - title: "internal"
    path: /sdk/gcloud/reference/alpha/internal
    section:
    - title: "internal-command"
      path: /sdk/gcloud/reference/alpha/internal/internal-command
  - title: "sdk"
    path: /sdk/gcloud/reference/alpha/sdk
    section:
    - title: "alphagroup"
      path: /sdk/gcloud/reference/alpha/sdk/alphagroup
    - title: "ordered-choices"
      path: /sdk/gcloud/reference/alpha/sdk/ordered-choices
    - title: "second-level-command-1"
      path: /sdk/gcloud/reference/alpha/sdk/second-level-command-1
    - title: "second-level-command-b"
      path: /sdk/gcloud/reference/alpha/sdk/second-level-command-b
    - title: "subgroup"
      path: /sdk/gcloud/reference/alpha/sdk/subgroup
      section:
      - title: "subgroup-command-2"
        path: /sdk/gcloud/reference/alpha/sdk/subgroup/subgroup-command-2
      - title: "subgroup-command-a"
        path: /sdk/gcloud/reference/alpha/sdk/subgroup/subgroup-command-a
    - title: "xyzzy"
      path: /sdk/gcloud/reference/alpha/sdk/xyzzy
  - title: "version"
    path: /sdk/gcloud/reference/alpha/version
"""),
        'beta/_toc.yaml': (False, """\
toc:
- title: "gcloud beta"
  path: /sdk/gcloud/reference/beta
  section:
  - title: "internal"
    path: /sdk/gcloud/reference/beta/internal
    section:
    - title: "internal-command"
      path: /sdk/gcloud/reference/beta/internal/internal-command
  - title: "sdk"
    path: /sdk/gcloud/reference/beta/sdk
    section:
    - title: "betagroup"
      path: /sdk/gcloud/reference/beta/sdk/betagroup
      section:
      - title: "beta-command"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/beta-command
      - title: "sub-command-2"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/sub-command-2
      - title: "sub-command-a"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/sub-command-a
    - title: "ordered-choices"
      path: /sdk/gcloud/reference/beta/sdk/ordered-choices
    - title: "second-level-command-1"
      path: /sdk/gcloud/reference/beta/sdk/second-level-command-1
    - title: "second-level-command-b"
      path: /sdk/gcloud/reference/beta/sdk/second-level-command-b
    - title: "subgroup"
      path: /sdk/gcloud/reference/beta/sdk/subgroup
      section:
      - title: "subgroup-command-2"
        path: /sdk/gcloud/reference/beta/sdk/subgroup/subgroup-command-2
      - title: "subgroup-command-a"
        path: /sdk/gcloud/reference/beta/sdk/subgroup/subgroup-command-a
    - title: "xyzzy"
      path: /sdk/gcloud/reference/beta/sdk/xyzzy
  - title: "version"
    path: /sdk/gcloud/reference/beta/version
"""),
        'internal/_toc.yaml': (False, """\
toc:
- title: "gcloud internal"
  path: /sdk/gcloud/reference/internal
  section:
  - title: "internal-command"
    path: /sdk/gcloud/reference/internal/internal-command
"""),
        'sdk/_toc.yaml': (False, """\
toc:
- title: "gcloud sdk"
  path: /sdk/gcloud/reference/sdk
  section:
  - title: "ordered-choices"
    path: /sdk/gcloud/reference/sdk/ordered-choices
  - title: "second-level-command-1"
    path: /sdk/gcloud/reference/sdk/second-level-command-1
  - title: "second-level-command-b"
    path: /sdk/gcloud/reference/sdk/second-level-command-b
  - title: "subgroup"
    path: /sdk/gcloud/reference/sdk/subgroup
    section:
    - title: "subgroup-command-2"
      path: /sdk/gcloud/reference/sdk/subgroup/subgroup-command-2
    - title: "subgroup-command-a"
      path: /sdk/gcloud/reference/sdk/subgroup/subgroup-command-a
  - title: "xyzzy"
    path: /sdk/gcloud/reference/sdk/xyzzy
"""),
        '_toc.yaml': (False, """\
toc:
- title: "gcloud Reference"
  path: /sdk/gcloud/reference
  section:
  - include: /sdk/gcloud/reference/alpha/_toc.yaml
  - include: /sdk/gcloud/reference/beta/_toc.yaml
  - include: /sdk/gcloud/reference/internal/_toc.yaml
  - include: /sdk/gcloud/reference/sdk/_toc.yaml
  - title: "gcloud version"
    path: /sdk/gcloud/reference/version
""")}
    for name, (contains, expected) in six.iteritems(files):
      path = os.path.join(devsite_directory, name)
      with open(path, 'r') as f:
        actual = f.read()
        self.CheckRegression(name, actual, expected, contains=contains)

  def testHtmlGenerator(self):
    """Tests the generated directory file names and sizes."""
    html_directory = os.path.join(self.temp_path, 'html')
    walker_util.HtmlGenerator(self.cli, html_directory).Walk()
    self.AssertDirectoryIsGolden(
        html_directory, __file__, 'walker_util', 'html.dir')

  def testManPageGenerator(self):
    """Tests the generated directory file names and sizes."""
    manpage_directory = os.path.join(self.temp_path, 'manpage')
    walker_util.ManPageGenerator(self.cli, manpage_directory).Walk()
    self.AssertDirectoryIsGolden(
        manpage_directory, __file__, 'walker_util', 'manpage.dir')

  def testCommandTreeGeneratorAll(self):
    """Test the list of all groups and commands."""
    result = walker_util.CommandTreeGenerator(self.cli).Walk()
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_name_": "gcloud",
  "commands": [
    {
      "_name_": "version"
    }
  ],
  "groups": [
    {
      "_name_": "alpha",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "alphagroup"
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "beta",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "betagroup",
              "commands": [
                {
                  "_name_": "beta-command"
                },
                {
                  "_name_": "sub-command-2"
                },
                {
                  "_name_": "sub-command-a"
                }
              ]
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "internal",
      "commands": [
        {
          "_name_": "internal-command"
        }
      ]
    },
    {
      "_name_": "sdk",
      "commands": [
        {
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testCommandTreeGeneratorAllFlags(self):
    """Test the list of all groups and commands with flags."""
    result = walker_util.CommandTreeGenerator(self.cli, with_flags=True).Walk()
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_flags_": [
    "---flag-file-line-",
    "--authority-selector",
    "--authorization-token-file",
    "--configuration",
    "--credential-file-override",
    "--document",
    "--flags-file",
    "--flatten",
    "--format",
    "--help",
    "--http-timeout",
    "--log-http",
    "--user-output-enabled",
    "--verbosity",
    "-h"
  ],
  "_name_": "gcloud",
  "commands": [
    {
      "_name_": "version"
    }
  ],
  "groups": [
    {
      "_name_": "alpha",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_flags_": [
                "--ordered-choices"
              ],
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_flags_": [
                "--exactly-one",
                "--exactly-three",
                "--hidden",
                "--one-or-more",
                "--zero-or-more",
                "--zero-or-one"
              ],
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "alphagroup"
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_flags_": [
                    "--delete-in",
                    "--delete-on",
                    "--obsolete-in",
                    "--obsolete-on"
                  ],
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "beta",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_flags_": [
                "--ordered-choices"
              ],
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_flags_": [
                "--exactly-one",
                "--exactly-three",
                "--hidden",
                "--one-or-more",
                "--zero-or-more",
                "--zero-or-one"
              ],
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_flags_": [
                "--location"
              ],
              "_name_": "betagroup",
              "commands": [
                {
                  "_flags_": [
                    "--location"
                  ],
                  "_name_": "beta-command"
                },
                {
                  "_flags_": [
                    "--location"
                  ],
                  "_name_": "sub-command-2"
                },
                {
                  "_flags_": [
                    "--location",
                    "--one-two-three",
                    "--resourceful"
                  ],
                  "_name_": "sub-command-a"
                }
              ]
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_flags_": [
                    "--delete-in",
                    "--delete-on",
                    "--obsolete-in",
                    "--obsolete-on"
                  ],
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "internal",
      "commands": [
        {
          "_name_": "internal-command"
        }
      ]
    },
    {
      "_name_": "sdk",
      "commands": [
        {
          "_flags_": [
            "--ordered-choices"
          ],
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_flags_": [
            "--exactly-one",
            "--exactly-three",
            "--hidden",
            "--one-or-more",
            "--zero-or-more",
            "--zero-or-one"
          ],
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_flags_": [
                "--delete-in",
                "--delete-on",
                "--obsolete-in",
                "--obsolete-on"
              ],
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testCommandTreeGeneratorNoFlags(self):
    """Test the resource of all groups and commands with flags."""
    result = walker_util.CommandTreeGenerator(self.cli).Walk()
    self.assertNotIn('_flags_', result)

  def testCommandTreeGeneratorWithFlags(self):
    """Test the resource of all groups and commands with flags."""
    result = walker_util.CommandTreeGenerator(self.cli, with_flags=True).Walk()
    global_flags = result['_flags_']
    self.assertIn('--document', global_flags)
    self.assertIn('--help', global_flags)
    self.assertIn('--verbosity', global_flags)

  def testCommandTreeGeneratorWithFlagValues(self):
    """Test the resource of all groups and commands with flags/flag values."""
    result = walker_util.CommandTreeGenerator(self.cli,
                                              with_flag_values=True).Walk()
    global_flags = result['_flags_']
    self.assertIn('--document=:dict:', global_flags)
    self.assertIn('--help', global_flags)
    self.assertIn('--verbosity=critical,debug,error,info,none,warning',
                  global_flags)

  def testCommandTreeGeneratorAllFlagsValues(self):
    """Test the list of all groups and commands with flags and flag values."""
    result = walker_util.CommandTreeGenerator(self.cli,
                                              with_flag_values=True).Walk()
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_flags_": [
    "---flag-file-line-=:FLAG_FILE_LINE_:",
    "--authority-selector=:AUTHORITY_SELECTOR:",
    "--authorization-token-file=:AUTHORIZATION_TOKEN_FILE:",
    "--configuration=:CONFIGURATION:",
    "--credential-file-override=:CREDENTIAL_FILE_OVERRIDE:",
    "--document=:dict:",
    "--flags-file=:YAML_FILE:",
    "--flatten=:list:",
    "--format=:FORMAT:",
    "--help",
    "--http-timeout=:HTTP_TIMEOUT:",
    "--log-http",
    "--user-output-enabled",
    "--verbosity=critical,debug,error,info,none,warning",
    "-h"
  ],
  "_name_": "gcloud",
  "commands": [
    {
      "_name_": "version"
    }
  ],
  "groups": [
    {
      "_name_": "alpha",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_flags_": [
                "--ordered-choices=a-100g,a-10g,a-1g"
              ],
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_flags_": [
                "--exactly-one=:STOOGE:",
                "--exactly-three=:STOOGE:",
                "--hidden",
                "--one-or-more=:ATTRIBUTE:",
                "--zero-or-more=:ZERO_OR_MORE:",
                "--zero-or-one=:ZERO_OR_ONE:"
              ],
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "alphagroup"
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_flags_": [
                    "--delete-in=:DELETE_IN:",
                    "--delete-on=:DELETE_ON:",
                    "--obsolete-in=:OBSOLETE_IN:",
                    "--obsolete-on=:OBSOLETE_ON:"
                  ],
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "beta",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_flags_": [
                "--ordered-choices=a-100g,a-10g,a-1g"
              ],
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_flags_": [
                "--exactly-one=:STOOGE:",
                "--exactly-three=:STOOGE:",
                "--hidden",
                "--one-or-more=:ATTRIBUTE:",
                "--zero-or-more=:ZERO_OR_MORE:",
                "--zero-or-one=:ZERO_OR_ONE:"
              ],
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_flags_": [
                "--location=:LOCATION:"
              ],
              "_name_": "betagroup",
              "commands": [
                {
                  "_flags_": [
                    "--location=:LOCATION:"
                  ],
                  "_name_": "beta-command"
                },
                {
                  "_flags_": [
                    "--location=:LOCATION:"
                  ],
                  "_name_": "sub-command-2"
                },
                {
                  "_flags_": [
                    "--location=:LOCATION:",
                    "--one-two-three=1,2,3",
                    "--resourceful=:RESOURCEFUL:"
                  ],
                  "_name_": "sub-command-a"
                }
              ]
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_flags_": [
                    "--delete-in=:DELETE_IN:",
                    "--delete-on=:DELETE_ON:",
                    "--obsolete-in=:OBSOLETE_IN:",
                    "--obsolete-on=:OBSOLETE_ON:"
                  ],
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "internal",
      "commands": [
        {
          "_name_": "internal-command"
        }
      ]
    },
    {
      "_name_": "sdk",
      "commands": [
        {
          "_flags_": [
            "--ordered-choices=a-100g,a-10g,a-1g"
          ],
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_flags_": [
            "--exactly-one=:STOOGE:",
            "--exactly-three=:STOOGE:",
            "--hidden",
            "--one-or-more=:ATTRIBUTE:",
            "--zero-or-more=:ZERO_OR_MORE:",
            "--zero-or-one=:ZERO_OR_ONE:"
          ],
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_flags_": [
                "--delete-in=:DELETE_IN:",
                "--delete-on=:DELETE_ON:",
                "--obsolete-in=:OBSOLETE_IN:",
                "--obsolete-on=:OBSOLETE_ON:"
              ],
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testCommandTreeGeneratorRestrict(self):
    """Test the list of the sdk groups and commands."""
    result = walker_util.CommandTreeGenerator(self.cli).Walk(
        restrict=['gcloud.sdk'])
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_name_": "gcloud",
  "groups": [
    {
      "_name_": "sdk",
      "commands": [
        {
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testGCloudTreeGenerator(self):
    """Test the gcloud command and group tree list."""
    result = walker_util.GCloudTreeGenerator(self.cli).Walk()
    resource_printer.Print(resources=result, print_format='json')
    self.AssertOutputIsGolden(__file__, 'walker_util', 'gcloud.tree')

  def testDevSiteGeneratorHidden(self):
    """Tests the hidden DevSite generated directory file names and sizes."""
    devsite_directory = os.path.join(self.temp_path, 'devsite')
    walker_util.DevSiteGenerator(self.cli, devsite_directory).Walk(hidden=True)
    self.AssertDirectoryIsGolden(
        devsite_directory, __file__, 'walker_util', 'devsite-hidden.dir')

  def testDevSiteGeneratorHiddenFileContents(self):
    """Tests the hidden DevSite _toc.yaml files, and two HTML files."""
    devsite_directory = os.path.join(self.temp_path, 'devsite')
    walker_util.DevSiteGenerator(self.cli, devsite_directory).Walk(hidden=True)

    files = {
        'alpha/sdk/hiddengroup/index.html': (True, """\
<html devsite="">
<head>
<title>gcloud alpha sdk hiddengroup</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
"""),
        'beta/sdk/subgroup/subgroup-command-2.html': (True, """\
<html devsite="">
<head>
<title>gcloud beta sdk subgroup subgroup-command-2</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
"""),
        'alpha/_toc.yaml': (False, """\
toc:
- title: "gcloud alpha"
  path: /sdk/gcloud/reference/alpha
  section:
  - title: "internal"
    path: /sdk/gcloud/reference/alpha/internal
    section:
    - title: "internal-command"
      path: /sdk/gcloud/reference/alpha/internal/internal-command
  - title: "sdk"
    path: /sdk/gcloud/reference/alpha/sdk
    section:
    - title: "alphagroup"
      path: /sdk/gcloud/reference/alpha/sdk/alphagroup
    - title: "hidden-command"
      path: /sdk/gcloud/reference/alpha/sdk/hidden-command
    - title: "hiddengroup"
      path: /sdk/gcloud/reference/alpha/sdk/hiddengroup
      section:
      - title: "hidden-command-2"
        path: /sdk/gcloud/reference/alpha/sdk/hiddengroup/hidden-command-2
      - title: "hidden-command-a"
        path: /sdk/gcloud/reference/alpha/sdk/hiddengroup/hidden-command-a
    - title: "ordered-choices"
      path: /sdk/gcloud/reference/alpha/sdk/ordered-choices
    - title: "second-level-command-1"
      path: /sdk/gcloud/reference/alpha/sdk/second-level-command-1
    - title: "second-level-command-b"
      path: /sdk/gcloud/reference/alpha/sdk/second-level-command-b
    - title: "subgroup"
      path: /sdk/gcloud/reference/alpha/sdk/subgroup
      section:
      - title: "subgroup-command-2"
        path: /sdk/gcloud/reference/alpha/sdk/subgroup/subgroup-command-2
      - title: "subgroup-command-a"
        path: /sdk/gcloud/reference/alpha/sdk/subgroup/subgroup-command-a
    - title: "xyzzy"
      path: /sdk/gcloud/reference/alpha/sdk/xyzzy
  - title: "version"
    path: /sdk/gcloud/reference/alpha/version
"""),
        'beta/_toc.yaml': (False, """\
toc:
- title: "gcloud beta"
  path: /sdk/gcloud/reference/beta
  section:
  - title: "internal"
    path: /sdk/gcloud/reference/beta/internal
    section:
    - title: "internal-command"
      path: /sdk/gcloud/reference/beta/internal/internal-command
  - title: "sdk"
    path: /sdk/gcloud/reference/beta/sdk
    section:
    - title: "betagroup"
      path: /sdk/gcloud/reference/beta/sdk/betagroup
      section:
      - title: "beta-command"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/beta-command
      - title: "sub-command-2"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/sub-command-2
      - title: "sub-command-a"
        path: /sdk/gcloud/reference/beta/sdk/betagroup/sub-command-a
    - title: "hidden-command"
      path: /sdk/gcloud/reference/beta/sdk/hidden-command
    - title: "hiddengroup"
      path: /sdk/gcloud/reference/beta/sdk/hiddengroup
      section:
      - title: "hidden-command-2"
        path: /sdk/gcloud/reference/beta/sdk/hiddengroup/hidden-command-2
      - title: "hidden-command-a"
        path: /sdk/gcloud/reference/beta/sdk/hiddengroup/hidden-command-a
    - title: "ordered-choices"
      path: /sdk/gcloud/reference/beta/sdk/ordered-choices
    - title: "second-level-command-1"
      path: /sdk/gcloud/reference/beta/sdk/second-level-command-1
    - title: "second-level-command-b"
      path: /sdk/gcloud/reference/beta/sdk/second-level-command-b
    - title: "subgroup"
      path: /sdk/gcloud/reference/beta/sdk/subgroup
      section:
      - title: "subgroup-command-2"
        path: /sdk/gcloud/reference/beta/sdk/subgroup/subgroup-command-2
      - title: "subgroup-command-a"
        path: /sdk/gcloud/reference/beta/sdk/subgroup/subgroup-command-a
    - title: "xyzzy"
      path: /sdk/gcloud/reference/beta/sdk/xyzzy
  - title: "version"
    path: /sdk/gcloud/reference/beta/version
"""),
        'internal/_toc.yaml': (False, """\
toc:
- title: "gcloud internal"
  path: /sdk/gcloud/reference/internal
  section:
  - title: "internal-command"
    path: /sdk/gcloud/reference/internal/internal-command
"""),
        'sdk/_toc.yaml': (False, """\
toc:
- title: "gcloud sdk"
  path: /sdk/gcloud/reference/sdk
  section:
  - title: "hidden-command"
    path: /sdk/gcloud/reference/sdk/hidden-command
  - title: "hiddengroup"
    path: /sdk/gcloud/reference/sdk/hiddengroup
    section:
    - title: "hidden-command-2"
      path: /sdk/gcloud/reference/sdk/hiddengroup/hidden-command-2
    - title: "hidden-command-a"
      path: /sdk/gcloud/reference/sdk/hiddengroup/hidden-command-a
  - title: "ordered-choices"
    path: /sdk/gcloud/reference/sdk/ordered-choices
  - title: "second-level-command-1"
    path: /sdk/gcloud/reference/sdk/second-level-command-1
  - title: "second-level-command-b"
    path: /sdk/gcloud/reference/sdk/second-level-command-b
  - title: "subgroup"
    path: /sdk/gcloud/reference/sdk/subgroup
    section:
    - title: "subgroup-command-2"
      path: /sdk/gcloud/reference/sdk/subgroup/subgroup-command-2
    - title: "subgroup-command-a"
      path: /sdk/gcloud/reference/sdk/subgroup/subgroup-command-a
  - title: "xyzzy"
    path: /sdk/gcloud/reference/sdk/xyzzy
"""),
        '_toc.yaml': (False, """\
toc:
- title: "gcloud Reference"
  path: /sdk/gcloud/reference
  section:
  - include: /sdk/gcloud/reference/alpha/_toc.yaml
  - include: /sdk/gcloud/reference/beta/_toc.yaml
  - include: /sdk/gcloud/reference/internal/_toc.yaml
  - include: /sdk/gcloud/reference/sdk/_toc.yaml
  - title: "gcloud version"
    path: /sdk/gcloud/reference/version
""")}
    for name, (contains, expected) in six.iteritems(files):
      path = os.path.join(devsite_directory, name)
      with open(path, 'r') as f:
        actual = f.read()
        self.CheckRegression(name, actual, expected, contains=contains)

  def testHelpTextGenerator(self):
    """Tests the help text generated directory file names and sizes."""
    help_directory = os.path.join(self.temp_path, 'help')
    walker_util.HelpTextGenerator(self.cli, help_directory).Walk()
    self.AssertDirectoryIsGolden(
        help_directory, __file__, 'walker_util', 'help.dir')

  def testHelpTextGeneratorHidden(self):
    """Tests the hidden help text generated directory file names and sizes."""
    help_directory = os.path.join(self.temp_path, 'help')
    walker_util.HelpTextGenerator(self.cli, help_directory).Walk(hidden=True)
    self.AssertDirectoryIsGolden(
        help_directory, __file__, 'walker_util', 'help-hidden.dir')

  def testManPageGeneratorHidden(self):
    """Tests the hidden man page generated directory file names and sizes."""
    manpage_directory = os.path.join(self.temp_path, 'manpage')
    walker_util.ManPageGenerator(self.cli, manpage_directory).Walk(hidden=True)
    self.AssertDirectoryIsGolden(
        manpage_directory, __file__, 'walker_util', 'manpage-hidden.dir')

  def testCommandTreeGeneratorHiddenAll(self):
    """Test the list of all hidden groups and commands."""
    result = walker_util.CommandTreeGenerator(self.cli).Walk(hidden=True)
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_name_": "gcloud",
  "commands": [
    {
      "_name_": "version"
    }
  ],
  "groups": [
    {
      "_name_": "alpha",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_name_": "hidden-command"
            },
            {
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "alphagroup"
            },
            {
              "_name_": "hiddengroup",
              "commands": [
                {
                  "_name_": "hidden-command-2"
                },
                {
                  "_name_": "hidden-command-a"
                }
              ]
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "beta",
      "commands": [
        {
          "_name_": "version"
        }
      ],
      "groups": [
        {
          "_name_": "internal",
          "commands": [
            {
              "_name_": "internal-command"
            }
          ]
        },
        {
          "_name_": "sdk",
          "commands": [
            {
              "_name_": "hidden-command"
            },
            {
              "_name_": "ordered-choices"
            },
            {
              "_name_": "second-level-command-1"
            },
            {
              "_name_": "second-level-command-b"
            },
            {
              "_name_": "xyzzy"
            }
          ],
          "groups": [
            {
              "_name_": "betagroup",
              "commands": [
                {
                  "_name_": "beta-command"
                },
                {
                  "_name_": "sub-command-2"
                },
                {
                  "_name_": "sub-command-a"
                }
              ]
            },
            {
              "_name_": "hiddengroup",
              "commands": [
                {
                  "_name_": "hidden-command-2"
                },
                {
                  "_name_": "hidden-command-a"
                }
              ]
            },
            {
              "_name_": "subgroup",
              "commands": [
                {
                  "_name_": "subgroup-command-2"
                },
                {
                  "_name_": "subgroup-command-a"
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "_name_": "internal",
      "commands": [
        {
          "_name_": "internal-command"
        }
      ]
    },
    {
      "_name_": "sdk",
      "commands": [
        {
          "_name_": "hidden-command"
        },
        {
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "hiddengroup",
          "commands": [
            {
              "_name_": "hidden-command-2"
            },
            {
              "_name_": "hidden-command-a"
            }
          ]
        },
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testCommandTreeGeneratorHiddenRestrict(self):
    """Test the list of the restricted hidden sdk groups and commands."""
    result = walker_util.CommandTreeGenerator(self.cli).Walk(
        hidden=True, restrict=['gcloud.sdk'])
    resource_printer.Print(result, print_format='json')
    self.AssertOutputContains("""\
{
  "_name_": "gcloud",
  "groups": [
    {
      "_name_": "sdk",
      "commands": [
        {
          "_name_": "hidden-command"
        },
        {
          "_name_": "ordered-choices"
        },
        {
          "_name_": "second-level-command-1"
        },
        {
          "_name_": "second-level-command-b"
        },
        {
          "_name_": "xyzzy"
        }
      ],
      "groups": [
        {
          "_name_": "hiddengroup",
          "commands": [
            {
              "_name_": "hidden-command-2"
            },
            {
              "_name_": "hidden-command-a"
            }
          ]
        },
        {
          "_name_": "subgroup",
          "commands": [
            {
              "_name_": "subgroup-command-2"
            },
            {
              "_name_": "subgroup-command-a"
            }
          ]
        }
      ]
    }
  ]
}
""")

  def testGCloudTreeGeneratorHidden(self):
    """Test the hidden gcloud command and group tree list."""
    result = walker_util.GCloudTreeGenerator(self.cli).Walk(hidden=True)
    resource_printer.Print(resources=result, print_format='json')
    self.AssertOutputIsGolden(__file__, 'walker_util', 'hidden.tree')


if __name__ == '__main__':
  test_case.main()
