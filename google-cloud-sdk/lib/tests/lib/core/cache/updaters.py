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

"""Mock updaters for the resource and completion cache module tests."""

from __future__ import absolute_import
from __future__ import division
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.cache import resource_cache


NOW_START_TIME = 12345678


class ZeroRequiredCollectionUpdater(resource_cache.Updater):
  """Upater with 0 required columns."""

  _UPDATES = [
      [
          ('aaa', 'pdq-a', 'xyz-a'),
          ('aab', 'pdq-b', 'xyz-b'),
          ('abc', 'pdq-c', 'xyz-b'),
      ],
      [
          ('abb', 'pdq-b', 'xyz-a'),
          ('abc', 'pdq-c', 'xyz-b'),
          ('acc', 'pdq-d', 'xyz-b'),
          ('ace', 'pdq-e', 'xyz-c'),
      ],
  ]

  def __init__(self, cache):
    super(ZeroRequiredCollectionUpdater, self).__init__(
        cache, collection='test.api', columns=3, timeout=1)

  def ParameterInfo(self, parsed_args=None, argument=None):

    class ZeroRequiredCollectionParameterInfo(resource_cache.ParameterInfo):
      pass

    return ZeroRequiredCollectionParameterInfo()

  def Update(self, parameter_info=None, aggregations=None):
    return self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]


class ColumnOneUpdater(resource_cache.Updater):
  """Value updater for TwoRequiredCollectionUpdater."""

  _UPDATES = [
      [
          ('pdq-a',),
          ('pdq-b',),
      ],
      [
          ('pdq-b',),
          ('pdq-c',),
      ],
  ]

  def __init__(self, cache):
    super(ColumnOneUpdater, self).__init__(
        cache, collection='test.zone', columns=1, timeout=1)

  def Update(self, parameter_info=None, aggregations=None):
    return self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]


class ColumnTwoUpdater(resource_cache.Updater):
  """Value updater for OneRequiredCollectionUpdater."""

  _UPDATES = [
      [
          ('xyz-a',),
          ('xyz-b',),
      ],
      [
          ('xyz-a',),
          ('xyz-b',),
          ('xyz-c',),
      ],
  ]

  def __init__(self, cache):
    super(ColumnTwoUpdater, self).__init__(
        cache, collection='test.project', columns=1, timeout=1)

  def Update(self, parameter_info=None, aggregations=None):
    return self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]


class OneRequiredCollectionUpdater(resource_cache.Updater):
  """Upater with 1 required column."""

  _UPDATES = [
      [
          ('aaa', 'pdq-a', 'xyz-a'),
          ('aab', 'pdq-b', 'xyz-b'),
          ('abc', 'pdq-c', 'xyz-b'),
      ],
      [
          ('abb', 'pdq-b', 'xyz-a'),
          ('abc', 'pdq-c', 'xyz-b'),
          ('acc', 'pdq-d', 'xyz-b'),
          ('ace', 'pdq-e', 'xyz-c'),
      ],
  ]

  def __init__(self, cache):
    super(OneRequiredCollectionUpdater, self).__init__(
        cache, collection='test.api', columns=3, timeout=1,
        parameters=[
            resource_cache.Parameter(column=2, name='two'),
        ])

  def ParameterInfo(self, parsed_args=None, argument=None):
    return resource_cache.ParameterInfo(
        updaters={
            'two': (ColumnTwoUpdater, True),
        },
    )

  def Update(self, parameter_info=None, aggregations=None):
    generation = int(persistent_cache_base.Now() != NOW_START_TIME)
    return self._UPDATES[generation]


class TwoRequiredCollectionUpdater(resource_cache.Updater):
  """Upater with 2 required columns."""

  _UPDATES = [
      [
          ('aaa', 'pdq-a', 'xyz-a'),
          ('aab', 'pdq-b', 'xyz-b'),
          ('abc', 'pdq-a', 'xyz-b'),
      ],
      [
          ('abb', 'pdq-b', 'xyz-a'),
          ('abc', 'pdq-c', 'xyz-b'),
          ('acc', 'pdq-b', 'xyz-b'),
          ('ace', 'pdq-c', 'xyz-c'),
      ],
  ]

  def __init__(self, cache):
    super(TwoRequiredCollectionUpdater, self).__init__(
        cache, collection='test.api', columns=3, timeout=1,
        parameters=[
            resource_cache.Parameter(column=1, name='one'),
            resource_cache.Parameter(column=2, name='two'),
        ])

  def ParameterInfo(self, parsed_args=None, argument=None):
    return resource_cache.ParameterInfo(
        updaters={
            'one': (ColumnOneUpdater, True),
            'two': (ColumnTwoUpdater, True),
        },
    )

  def Update(self, parameter_info=None, aggregations=None):
    generation = int(persistent_cache_base.Now() != NOW_START_TIME)
    return self._UPDATES[generation]


class ColumnZeroUpdater(resource_cache.Updater):
  """Value updater for a zeroth-column param."""

  _UPDATES = [
      [
          ('aaa',),
          ('aab',),
          ('abc',),
      ],
      [
          ('abb',),
          ('abc',),
          ('acc',),
          ('ace',),
      ],
  ]

  def __init__(self, cache):
    super(ColumnZeroUpdater, self).__init__(
        cache, collection='test.project', columns=1, timeout=1,
        parameters=[
            resource_cache.Parameter(column=0, name='zero')])

  def ParameterInfo(self, parsed_args=None, argument=None):
    return resource_cache.ParameterInfo(updaters={})

  def Update(self, parameter_info=None, aggregations=None):
    updates = self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]
    return updates


class ColumnOneCumulativeUpdater(resource_cache.Updater):
  """Value updater with two parameters.

  Parameter 'one' depends on parameter 'zero'.
  """

  _UPDATES = [
      [
          ('aaa', 'pdq-a'),
          ('aab', 'pdq-b'),
          ('abc', 'pdq-a'),
      ],
      [
          ('abb', 'pdq-b'),
          ('abc', 'pdq-c'),
          ('acc', 'pdq-b'),
          ('ace', 'pdq-c'),
      ],
  ]

  def __init__(self, cache):
    super(ColumnOneCumulativeUpdater, self).__init__(
        cache, collection='test.project.zone', columns=2, timeout=1,
        column=1, parameters=[
            resource_cache.Parameter(column=0, name='zero'),
            resource_cache.Parameter(column=1, name='one')])

  def ParameterInfo(self, parsed_args=None, argument=None):
    return resource_cache.ParameterInfo(updaters={
        'zero': ColumnZeroUpdater
    })

  def Update(self, parameter_info=None, aggregations=None):
    zero = parameter_info.GetValue('zero')
    if not zero:
      zero = ([a.value for a in aggregations if a.name == 'zero'] or [None])[0]
    updates = self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]
    updates = [u for u in updates if u[0] == zero]
    return updates


class TwoRequiredCollectionCumulativeUpdater(resource_cache.Updater):
  """Updater with 3 required columns.

  Parameter 'two' depends on parameter 'one.' Parameter 'one' depends on
  parameter 'zero'.
  """

  _UPDATES = [
      [
          ('aaa', 'pdq-a', 'xyz-a'),
          ('aab', 'pdq-b', 'xyz-b'),
          ('abc', 'pdq-a', 'xyz-b'),
      ],
      [
          ('abb', 'pdq-b', 'xyz-a'),
          ('abc', 'pdq-c', 'xyz-b'),
          ('acc', 'pdq-b', 'xyz-b'),
          ('ace', 'pdq-c', 'xyz-c'),
      ],
  ]

  def __init__(self, cache):
    super(TwoRequiredCollectionCumulativeUpdater, self).__init__(
        cache, collection='test.project.zone.instance', columns=3, timeout=1,
        column=2, parameters=[
            resource_cache.Parameter(column=0, name='zero'),
            resource_cache.Parameter(column=1, name='one'),
            resource_cache.Parameter(column=2, name='two'),
        ])

  def ParameterInfo(self, parsed_args=None, argument=None):
    return resource_cache.ParameterInfo(
        updaters={
            'zero': (ColumnZeroUpdater, True),
            'one': (ColumnOneCumulativeUpdater, True)
        },
    )

  def Update(self, parameter_info=None, aggregations=None):
    zero = parameter_info.GetValue('zero')
    if not zero:
      zero = ([a.value for a in aggregations if a.name == 'zero'] or [None])[0]
    one = parameter_info.GetValue('one')
    if not one:
      one = ([a.value for a in aggregations if a.name == 'one'] or [None])[0]
    updates = self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]
    updates = [u for u in updates if u[0] == zero and u[1] == one]
    return updates


class NoCollectionUpdater(resource_cache.Updater):
  """Updater with no collection."""

  _UPDATES = [
      [
          ('thing-1',),
          ('thing-2',),
      ],
      [
          ('thing-0',),
          ('thing-1',),
          ('thing-n',),
      ],
  ]

  def __init__(self, cache):
    super(NoCollectionUpdater, self).__init__(
        cache, timeout=1)

  def Update(self, parameter_info=None, aggregations=None):
    return self._UPDATES[int(persistent_cache_base.Now() != NOW_START_TIME)]
