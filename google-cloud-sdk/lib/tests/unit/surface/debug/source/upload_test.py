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
"""Tests for gcloud debug source upload."""

from __future__ import absolute_import
from __future__ import unicode_literals
import json
import os

from googlecloudsdk.api_lib.debug import upload
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import files as file_utils
from tests.lib.surface.debug import base


def _load_json(path):
  return json.loads(file_utils.ReadFileContents(path))


class UploadTest(base.DebugSdkTest):

  def SetUp(self):
    self.tmpdir = file_utils.TemporaryDirectory().path
    self.mock_upload = self.StartObjectPatch(upload.UploadManager, 'Upload')
    self.source_context = {
        'context': {
            'cloudRepo': {
                'repoId': {
                    'projectRepoId': {
                        'projectId': self.project_id,
                        'repoName': 'google-source-captures'
                    }
                },
                'revision': {
                    'aliasContext': {
                        'kind': 'MOVABLE',
                        'name': 'randombranch',
                    }
                }
            }
        },
        'labels': {
            'category': 'capture'
        }
    }
    self.mock_upload.return_value = {
        'branch': 'randombranch',
        'files_written': 5,
        'files_skipped': 2,
        'size_written': 500,
        'source_contexts': [self.source_context]
    }

  def testUploadInvalidLocation(self):
    with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                          'is not a directory'):
      directory = os.path.join(self.tmpdir, 'invaliddir')
      self.RunDebugBeta(['source', 'upload', directory])

  def testUpload(self):
    self.RunDebugBeta(['source', 'upload', self.tmpdir])

    self.mock_upload.assert_called_with(None, self.tmpdir)
    self.AssertOutputContains('branch: randombranch')
    self.AssertErrContains('Wrote 5 file(s), 500 bytes.')
    self.AssertErrContains('Skipped 2 file(s) due to size limitations')

  def testUploadNoFilesSkipped(self):
    self.mock_upload.return_value['files_skipped'] = 0
    self.RunDebugBeta(['source', 'upload', self.tmpdir])

    self.AssertErrNotContains('Skipped 2 file(s) due to size limitations')

  def testUploadCustomBranchName(self):
    self.mock_upload.return_value['branch'] = 'branch1'

    self.RunDebugBeta(['source', 'upload', '--branch=branch1', self.tmpdir])

    self.mock_upload.assert_called_with('branch1', self.tmpdir)
    self.AssertOutputContains('branch: branch1')

  def testUploadSourceContextOutput(self):
    source_context_dir = os.path.join(self.tmpdir, 'source-contexts')
    source_context_file = os.path.join(source_context_dir,
                                       'source-context.json')
    self.RunDebugBeta([
        'source', 'upload', '--source-context-directory=' + source_context_dir,
        self.tmpdir
    ])

    self.AssertOutputContains('branch: randombranch', normalize_space=True)
    self.AssertOutputContains('context_file:')
    self.AssertOutputContains(source_context_file)

    self.assertEqual(self.source_context['context'],
                     _load_json(source_context_file))
