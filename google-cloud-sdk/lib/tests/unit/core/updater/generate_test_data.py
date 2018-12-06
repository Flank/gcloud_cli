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
"""A script to generate .tar files and snapshots for testing the updater."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os
import shutil

from googlecloudsdk.core.util import files
from tests.lib.core.updater import util


def GenerateSnapshot(out_dir, revision, tuples):
  snapshot, _ = util.TestComponents.CreateSnapshotFromComponentsGenerateTars(
      revision, tuples)
  snapshot_path = util.TestComponents.CreateTempSnapshotFileFromSnapshot(
      snapshot)
  shutil.copy(snapshot_path, os.path.join(out_dir, str(revision) + '.json'))


def main():
  parser = argparse.ArgumentParser(
      description=('This command generates .tar.gz files for a bunch of fake '
                   'components as well as some fake JSON snapshots.  This '
                   'allows you to test the updater from the CLI manually with '
                   'some fake data.'))
  parser.add_argument('--output_dir', '-o', metavar='output-dir', required=True,
                      help='The directory to generate the data to.')
  args = parser.parse_args()

  out_dir = files.ExpandHomeDir(args.output_dir)
  util.Directories.TEMP_DIR = out_dir
  util.Directories.SetUpDirectories()

  tuples = [('a', 1, ['b']), ('b', 1, ['c']), ('c', 1, []), ('e', 1, []),
            ('f', 1, ['g']), ('g', 1, [])]
  GenerateSnapshot(out_dir, 1, tuples)

  tuples = [('a', 1, ['b']), ('b', 2, ['c']), ('c', 1, []), ('e', 2, []),
            ('f', 1, ['g']), ('g', 1, [])]
  GenerateSnapshot(out_dir, 2, tuples)

  tuples = [('a', 2, ['b']), ('b', 3, []), ('e', 2, []),
            ('f', 2, ['g']), ('g', 1, []), ('h', 1, [])]
  GenerateSnapshot(out_dir, 3, tuples)

  tuples = [('a', 2, ['b']), ('b', 3, []), ('e', 2, []),
            ('f', 2, ['g']), ('g', 1, []), ('h', 2, ['i']), ('i', 1, [])]
  GenerateSnapshot(out_dir, 4, tuples)


if __name__ == '__main__':
  main()
