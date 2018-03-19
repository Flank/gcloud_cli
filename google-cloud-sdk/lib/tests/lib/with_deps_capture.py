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

"""Base class to save module dependencies of the test."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import imp
import inspect
import os
import StringIO
import sys

from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import yaml_printer
from tests.lib import sdk_test_base

from six.moves import range  # pylint: disable=redefined-builtin


INIT_SUFFIX = '.__init__'
GOOGLECLOUDSDK_PREFIX = 'googlecloudsdk.'
TEST_ROOT_DIR_ENV_VAR = 'CLOUD_SDK_TEST_REGEN_DEPS'


def ModuleByPath(path, pre_root):
  result = os.path.relpath(path, pre_root).rsplit(
      '.', 1)[0].replace(os.sep, '.')
  if result.endswith(INIT_SUFFIX):
    result = result[:-len(INIT_SUFFIX)]
  return result


class _LoadModuleMock(object):
  """A class saving all modules imported by imp.load_module."""

  _object_by_class_name = {}
  _latest_object = None

  @classmethod
  def GetOrCreate(cls, clazz):
    name = clazz.__name__
    if name not in cls._object_by_class_name:
      cls._object_by_class_name[name] = cls(clazz.Resource())
    return cls._object_by_class_name[name]

  @classmethod
  def Clean(cls, clazz):
    name = clazz.__name__
    del cls._object_by_class_name[name]

  def __init__(self, googlecloudsdk_root):
    self._real_load = imp.load_module
    self._test = None
    self.imported_modules = []
    self._pre_root = googlecloudsdk_root
    _LoadModuleMock._latest_object = self

  def Mock(self, test):
    if not self._test:
      self._test = test
    test.StartObjectPatch(imp, 'load_module', new=self)

  def UnMock(self, test):
    del test
    self._test = None

  def __call__(self, *args, **kwargs):
    module = self._real_load(*args, **kwargs)
    self.imported_modules.append(module.__file__)
    return module

  def GetDepString(self, path):
    m = ModuleByPath(path, self._pre_root)
    if m.startswith(GOOGLECLOUDSDK_PREFIX):
      m = m[len(GOOGLECLOUDSDK_PREFIX):]
    return m

  @classmethod
  def TearDownClass(cls):
    """Called after tests in an individual class have run."""

    # Check that all the test classes in module run
    if not cls._object_by_class_name:
      return
    for clazz in cls._latest_object.GetClasses():
      if clazz.__name__ not in cls._object_by_class_name:
        return

    # Collect all modules imported from file
    deps = set()
    for load_module_mock in cls._object_by_class_name.values():
      for module in load_module_mock.imported_modules:
        deps.add(cls._latest_object.GetDepString(module))

    filtered_deps = []
    if deps:
      deps = sorted(deps)
      for i in range(len(deps) - 1):
        if not deps[i + 1].startswith(deps[i]):
          filtered_deps.append(deps[i])
      filtered_deps.append(deps[-1])

    stream = StringIO.StringIO()
    yaml_printer.YamlPrinter(stream).AddRecord(filtered_deps)
    deps = stream.getvalue()

    cls._latest_object.Finalize(deps)

  def GetClasses(self):
    if not self._test:  # No tests in class
      return []
    test_module = sys.modules[self._test.__class__.__module__]
    return [clazz for _, clazz in inspect.getmembers(test_module)
            if inspect.isclass(clazz) and issubclass(clazz, WithDepsCapture)]

  def Finalize(self, deps):
    """Compare or save the deps."""

    test_module = sys.modules[self._test.__class__.__module__]

    deps_file = test_module.__file__.rsplit('.', 1)[0] + '.deps'
    deps_file_relpath = os.path.relpath(deps_file, self._test.Resource())

    regen_root = os.environ.get(TEST_ROOT_DIR_ENV_VAR)
    if regen_root:
      if not os.path.isdir(regen_root):
        raise ValueError('Environment variable {} points to [{}] but there is '
                         'no such directory.'.format(TEST_ROOT_DIR_ENV_VAR,
                                                     regen_root))
      with open(os.path.join(regen_root, deps_file_relpath), 'w') as f:
        f.write(deps)
    elif os.path.isfile(deps_file):
      with open(deps_file) as f:
        expected_content_str = f.read()
      if expected_content_str != deps:
        expected_content = yaml.load(expected_content_str)
        actual_content = yaml.load(deps)
        if expected_content != actual_content:
          self._test.assertMultiLineEqual(
              expected_content_str, deps,
              'Update file [{}] with above changes.'.format(deps_file_relpath))
    else:
      raise ValueError(
          'Each e2e file must have accompanying .deps file. '
          'Please create [{filename}] with the following yaml content '
          '(between the markers):\n>>> START <<<\n{content}\n>>> END <<<\n'
          'Alternatively you can set {env_var} environment variable to '
          'directory which contains "tests/" directory and rerun the test to '
          'automatically create .deps file.'.format(
              filename=deps_file_relpath,
              content=deps,
              env_var=TEST_ROOT_DIR_ENV_VAR
          ))


class WithDepsCapture(sdk_test_base.SdkBase):
  """A base class for tests capturing dependencies."""

  def PreSetUp(self):
    clazz = self.__class__
    if not hasattr(clazz, 'load_module_mock'):
      self._originals['state'].add('load_module_mock')
    clazz.load_module_mock = _LoadModuleMock.GetOrCreate(clazz)
    clazz.load_module_mock.Mock(self)

  def TearDown(self):
    exc_type, _, _ = sys.exc_info()
    if exc_type is not None:
      clazz = self.__class__
      clazz.load_module_mock.UnMock(self)
      _LoadModuleMock.Clean(clazz)
      del clazz.load_module_mock

  @classmethod
  def TearDownClass(cls):
    _LoadModuleMock.TearDownClass()
