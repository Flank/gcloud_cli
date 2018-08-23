# -*- coding: utf-8 -*- #
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

"""Tests for the gcloud interactive browser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import browser
from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.core.util import files
from tests.lib import subtests
from tests.unit.command_lib.interactive import testdata


class MockCli(object):

  def __init__(self, root):
    self.parser = parser.Parser(root)
    self.context = None
    self.root = root


class BrowserTests(subtests.Base):

  @classmethod
  def SetUpClass(cls):
    path = os.path.join(os.path.dirname(testdata.__file__), 'gcloud.json')
    cls.tree = cli_tree.Load(path=path)

  def SetUp(self):
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        side_effect=lambda command: '_' not in command)
    self.cli = MockCli(self.tree)

  def RunSubTest(self, line, pos=None):
    return [
        browser._GetReferenceURL(self.cli, line, pos),
        browser._GetReferenceURL(self.cli, line, pos, man_page=True),
    ]

  def testParse(self):

    def T(expected, line, pos=None):
      self.Run(expected, line, pos=pos, depth=2)

    T(['https://cloud.google.com/sdk/gcloud/reference',
       'gcloud --help'],
      'gcloud')
    T(['https://cloud.google.com/sdk/gcloud/reference/compute',
       'gcloud compute --help'],
      'gcloud compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/compute',
       'gcloud compute --help'],
      'gcloud compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/compute/instances',
       'gcloud compute instances --help'],
      'gcloud compute instances')
    T(['https://cloud.google.com/sdk/gcloud/reference',
       'gcloud --help'],
      'gcloud compute instances', pos=4)

    T(['https://cloud.google.com/sdk/gcloud/reference/alpha',
       'gcloud alpha --help'],
      'gcloud alpha')
    T(['https://cloud.google.com/sdk/gcloud/reference/alpha/compute',
       'gcloud alpha compute --help'],
      'gcloud alpha compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/alpha/compute',
       'gcloud alpha compute --help'],
      'gcloud alpha compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/alpha/compute/instances',
       'gcloud alpha compute instances --help'],
      'gcloud alpha compute instances')
    T(['https://cloud.google.com/sdk/gcloud/reference/alpha',
       'gcloud alpha --help'],
      'gcloud alpha compute instances', pos=8)

    T(['https://cloud.google.com/sdk/gcloud/reference/beta',
       'gcloud beta --help'],
      'gcloud beta')
    T(['https://cloud.google.com/sdk/gcloud/reference/beta/compute',
       'gcloud beta compute --help'],
      'gcloud beta compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/beta/compute',
       'gcloud beta compute --help'],
      'gcloud beta compute')
    T(['https://cloud.google.com/sdk/gcloud/reference/beta/compute/instances',
       'gcloud beta compute instances --help'],
      'gcloud beta compute instances')
    T(['https://cloud.google.com/sdk/gcloud/reference/beta',
       'gcloud beta --help'],
      'gcloud beta compute instances', pos=8)

    T(['https://cloud.google.com/bigquery/bq-command-line-tool',
       'bq help | less'],
      'bq')
    T(['https://cloud.google.com/bigquery/bq-command-line-tool',
       'bq help | less'],
      'bq cancel')

    T(['https://cloud.google.com/storage/docs/gsutil',
       'gsutil help | less'],
      'gsutil')
    T(['https://cloud.google.com/storage/docs/gsutil/commands/compose',
       'gsutil help compose | less'],
      'gsutil compose')
    T(['https://cloud.google.com/storage/docs/gsutil/commands/acl',
       'gsutil help acl | less'],
      'gsutil acl set')

    T(['https://kubernetes.io/docs/user-guide/kubectl/v1.8',
       'kubectl help | less'],
      'kubectl')
    T(['https://kubernetes.io/docs/user-guide/kubectl/v1.8/#attach',
       'kubectl help attach | less'],
      'kubectl attach')
    T(['https://kubernetes.io/docs/user-guide/kubectl/v1.8/#auth',
       'kubectl help auth | less'],
      'kubectl auth can-i')

    if 'darwin' in sys.platform:

      T(['https://developer.apple.com/legacy/library/documentation/'
         'Darwin/Reference/ManPages/man1/ls.1.html',
         'man ls'],
        'ls')
      T(['https://developer.apple.com/legacy/library/documentation/'
         'Darwin/Reference/ManPages/man1/ls.1.html',
         'man ls'],
        'ls -l')
      T(['https://developer.apple.com/legacy/library/documentation/'
         'Darwin/Reference/ManPages/man1/ls.1.html',
         'man ls'],
        'ls foo')

    else:

      T(['http://man7.org/linux/man-pages/man1/ls.1.html',
         'man ls'],
        'ls')
      T(['http://man7.org/linux/man-pages/man1/ls.1.html',
         'man ls'],
        'ls -l')
      T(['http://man7.org/linux/man-pages/man1/ls.1.html',
         'man ls'],
        'ls foo')

    T([None,
       None],
      '_No_SuCh_CoMmAnD_')
