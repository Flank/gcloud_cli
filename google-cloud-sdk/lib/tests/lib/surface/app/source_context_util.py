# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Test data for source contexts in `gcloud app`."""

PROJECT = 'fakeproject'

REMOTE_CONTEXT = {
    'labels': {'category': 'remote_repo'},
    'context': {
        'cloudRepo': {
            'repoId': {
                'projectRepoId': {'repoName': 'default',
                                  'projectId': PROJECT}},
            'revisionId': 'fake_revision'}}}

SNAPSHOT_CONTEXT = {
    'labels': {'category': 'snapshot'},
    'context': {
        'cloudWorkspace': {
            'workspaceId': {
                'name': 'fake_workspace',
                'repoId': {
                    'projectRepoId': {'repoName': 'google-source-snapshots',
                                      'projectId': PROJECT}}}}}}

FAKE_CONTEXTS = [REMOTE_CONTEXT, SNAPSHOT_CONTEXT]
