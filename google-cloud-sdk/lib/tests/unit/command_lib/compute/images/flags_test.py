# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit tests for the compute.images.flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.images import flags
from tests.lib import completer_test_base
from tests.lib.surface.compute.images import test_resources


def _Uris(resources):
  return [resource.selfLink for resource in resources]


_COMMAND_RESOURCES = {
    'compute.images.list': _Uris(test_resources.IMAGES),
}

_SEARCH_RESOURCES = {
    'compute.images': _Uris(test_resources.IMAGES),
}


class ImagesCompleterTest(completer_test_base.CompleterBase):

  def testImagesCompleter(self):
    completer = self.Completer(flags.ImagesCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        ['image-1', 'image-2', 'image-3', 'image-4'],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        ['image-2'],
        completer.Complete('*2', self.parameter_info))
    self.assertEqual(
        [],
        completer.Complete('q', self.parameter_info))

  def testSearchImagesCompleter(self):
    completer = self.Completer(flags.SearchImagesCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        ['image-1', 'image-2', 'image-3', 'image-4'],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        ['image-2'],
        completer.Complete('*2', self.parameter_info))
    self.assertEqual(
        [],
        completer.Complete('q', self.parameter_info))


class ComputeFlagCompleterTest(completer_test_base.FlagCompleterBase):

  def testImagesCompleter(self):
    completer = self.Completer(flags.ImagesCompleter,
                               args={'--project': None,
                                     '--zone': None},
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        4,
        len(completer.Complete('', self.parameter_info)))
    self.assertEqual(
        ['image-2 --project=my-project'],
        completer.Complete('*2', self.parameter_info))

  def testImagesCompleterWithsMismatchedProjectArg(self):
    completer = self.Completer(flags.ImagesCompleter,
                               args={'project': 'my_x_project'},
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        [],
        completer.Complete('*2', self.parameter_info))

  def testImagesCompleterWithProjectArg(self):
    completer = self.Completer(flags.ImagesCompleter,
                               args={'project': 'my-project'},
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        ['image-2'],
        completer.Complete('*2', self.parameter_info))

  def testSearchImagesCompleter(self):
    completer = self.Completer(flags.SearchImagesCompleter,
                               args={'--project': None,
                                     '--zone': None},
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        4,
        len(completer.Complete('', self.parameter_info)))
    self.assertEqual(
        ['image-2 --project=my-project'],
        completer.Complete('*2', self.parameter_info))

  def testSearchImagesCompleterWithsMismatchedProjectArg(self):
    completer = self.Completer(flags.SearchImagesCompleter,
                               args={'project': 'my_x_project'},
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        [],
        completer.Complete('*2', self.parameter_info))

  def testSearchImagesCompleterWithProjectArg(self):
    completer = self.Completer(flags.SearchImagesCompleter,
                               args={'project': 'my-project'},
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        ['image-2'],
        completer.Complete('*2', self.parameter_info))


class ComputeGRICompleterTest(completer_test_base.GRICompleterBase):

  def testImagesCompleter(self):
    completer = self.Completer(flags.ImagesCompleter,
                               command_resources=_COMMAND_RESOURCES)
    self.assertEqual(
        4,
        len(completer.Complete('', self.parameter_info)))
    self.assertEqual(
        [
            'image-1:my-project',
            'image-2:my-project',
            'image-3:my-project',
            'image-4:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        ['image-2:my-project'],
        completer.Complete('*-2', self.parameter_info))

  def testSearchImagesCompleter(self):
    completer = self.Completer(flags.SearchImagesCompleter,
                               search_resources=_SEARCH_RESOURCES)
    self.assertEqual(
        4,
        len(completer.Complete('', self.parameter_info)))
    self.assertEqual(
        [
            'image-1:my-project',
            'image-2:my-project',
            'image-3:my-project',
            'image-4:my-project',
        ],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        ['image-2:my-project'],
        completer.Complete('*-2', self.parameter_info))


if __name__ == '__main__':
  completer_test_base.main()
