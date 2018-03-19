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

"""Fake messages for tests."""

from apitools.base.protorpclite import messages as _messages


class FakeMessage(_messages.Message):
  """A FakeMessage object.

  Fields:
    string1: the first string
    string2: a repeated string
    enum1: a FakeEnum
    enum2: a repeated FakeEnum
    bool1: a boolean
    int1: an int
    float1: a float
    message1: an InnerMessage message
    message2: an InnerMessage2 message
    repeated_message: a repeated InnerMessage message.
  """

  class InnerMessage(_messages.Message):
    """A InnerMessage object.

    Fields:
      string1: the first string
      string2: The second string. It also happens to have a really long
        description that wraps lines, which is convenient for testing that
        capability.
      int1: an integer
      enum1: an enum
    """
    string1 = _messages.StringField(1)
    string2 = _messages.StringField(2)
    int1 = _messages.IntegerField(3)
    enum1 = _messages.EnumField('FakeEnum', 4)

  class InnerMessage2(_messages.Message):
    """A InnerMessage2 object.

    Fields:
      deeper_message: a DeeperMessage message
    """

    class DeeperMessage(_messages.Message):
      """A DeeperMessage object.

      Fields:
        deep_string: a string
        output_string: [Output Only] a string that cannot be set.
        output_string2: another string that cannot be set.@OutputOnly
      """
      deep_string = _messages.StringField(1)
      output_string = _messages.StringField(2)
      output_string2 = _messages.StringField(3)

    deeper_message = _messages.MessageField('DeeperMessage', 1)

  class FakeEnum(_messages.Enum):
    """A FakeEnum object.

    Values:
      THING_ONE: the first thing
      THING_TWO: the second thing
    """
    THING_ONE = 0
    THING_TWO = 1

  string1 = _messages.StringField(1)
  string2 = _messages.StringField(2, repeated=True)
  enum1 = _messages.EnumField('FakeEnum', 3)
  enum2 = _messages.EnumField('FakeEnum', 4, repeated=True)
  bool1 = _messages.BooleanField(5)
  int1 = _messages.IntegerField(6)
  float1 = _messages.FloatField(7)
  message1 = _messages.MessageField('InnerMessage', 8)
  message2 = _messages.MessageField('InnerMessage2', 9)
  repeated_message = _messages.MessageField('InnerMessage', 10, repeated=True)
