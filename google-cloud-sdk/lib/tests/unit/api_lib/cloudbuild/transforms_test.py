# -*- coding: utf-8 -*- #
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

"""Unit tests for cloudbuild transforms module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import transforms
from tests.lib import test_case


_UNDEFINED = 'UNDEFINED'


class TransformTest(test_case.Base):

  def testTransformBuildImagesNoImages(self):
    r = {}
    out = transforms.TransformBuildImages(r, undefined=_UNDEFINED)
    self.assertEqual(out, _UNDEFINED)

    # Same output if images is present but empty.
    r = {
        'results': {
            'images': [],
        }
    }
    out = transforms.TransformBuildImages(r, undefined=_UNDEFINED)
    self.assertEqual(out, _UNDEFINED)

  def testTransformBuildImagesOneImage(self):
    r = {
        'results': {
            'images': [
                {
                    'name': 'my-cool-image'
                }
            ]
        }
    }
    out = transforms.TransformBuildImages(r, undefined=_UNDEFINED)
    self.assertEqual(out, 'my-cool-image')

  def testTransformBuildImagesManyImages(self):
    r = {
        'results': {
            'images': [
                {
                    'name': 'my-cool-image-1'
                },
                {
                    'name': 'my-cool-image-2'
                },
                {
                    'name': 'my-cool-image-3'
                },
                {
                    'name': 'my-cool-image-4'
                }
            ]
        }
    }
    out = transforms.TransformBuildImages(r, undefined=_UNDEFINED)
    self.assertEqual(out, 'my-cool-image-1 (+3 more)')

  def testTransformBuildSourceNoSource(self):
    r = {}
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out, _UNDEFINED)

    r = {
        'source': {},
    }
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out, _UNDEFINED)

  def testTransformBuildSourceBranch(self):
    r = {
        'source': {
            'repoSource': {
                'repoName': 'my-repo',
                'branchName': 'master'
            }
        }
    }
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out, 'my-repo@master')

  def testTransformBuildSourceNoRepoName(self):
    r = {
        'source': {
            'repoSource': {
                'branchName': 'master'
            }
        }
    }
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out, 'default@master')

  def testTransformBuildSourceTag(self):
    r = {
        'source': {
            'repoSource': {
                'repoName': 'my-repo',
                'tagName': 'release-foo'
            }
        }
    }
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out, 'my-repo@release-foo')

  def testTransformBuildSourceCommitSHA(self):
    r = {
        'source': {
            'repoSource': {
                'repoName': 'my-repo',
                'commitSha': '1234567890abcdef1234567890abcdef12345678',
            }
        }
    }
    out = transforms.TransformBuildSource(r, undefined=_UNDEFINED)
    self.assertEqual(out,
                     'my-repo@1234567890abcdef1234567890abcdef12345678')


if __name__ == '__main__':
  test_case.main()
