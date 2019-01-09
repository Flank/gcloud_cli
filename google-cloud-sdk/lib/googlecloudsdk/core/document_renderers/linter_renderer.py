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

"""Cloud SDK markdown document linter renderer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.document_renderers import text_renderer


class LinterRenderer(text_renderer.TextRenderer):
  """Renders markdown to a list of lines where there is a linter error."""

  _HEADINGS_TO_LINT = ['NAME', 'EXAMPLES', 'DESCRIPTION']
  _NAME_WORD_LIMIT = 15
  _PERSONAL_PRONOUNS = [' me ', ' we ', ' I ', ' us ', ' he ', ' she ', ' him ',
                        ' her ', ' them ', ' they ']

  def __init__(self, *args, **kwargs):
    super(LinterRenderer, self).__init__(*args, **kwargs)
    self._file_out = self._out  # the output file inherited from TextRenderer
    self._null_out = io.StringIO()
    self._buffer = io.StringIO()
    self._out = self._buffer
    self._analyze = {'NAME': self._analyze_name,
                     'EXAMPLES': self._analyze_examples,
                     'DESCRIPTION': self._analyze_description}
    self._heading = ''
    self._prev_heading = ''
    self.example = False
    self.command_name = ''
    self.name_section = ''
    self.command_name_length = 0
    self.command_text = ''
    self.violation_flags = []

  def _CaptureOutput(self, heading):
    # check if buffer is full from previous heading
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
      # refresh the StringIO()
      self._buffer = io.StringIO()
    self._out = self._buffer
    # save heading so can get it in next section
    self._prev_heading = self._heading

  def _DiscardOutput(self, heading):
    self._out = self._null_out

  def _Analyze(self, heading, section):
    self._analyze[heading](section)

  def check_for_personal_pronouns(self, section):
    warnings = ''
    for pronoun in self._PERSONAL_PRONOUNS:
      if pronoun in section:
        warnings += '\nPlease remove personal pronouns.'
        break
    return warnings

  def Finish(self):
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
    self._buffer.close()
    self._null_out.close()
    # TODO(b/121258430): only check if it is command level and not group level
    if not self.example:
      self._file_out.write('Refer to the detailed style guide: '
                           'go/cloud-sdk-help-guide#examples\nThis is the '
                           'analysis for EXAMPLES:\nYou have not included an '
                           'example in the Examples section.\n\n')

  def Heading(self, level, heading):
    self._heading = heading
    if heading in self._HEADINGS_TO_LINT:
      self._CaptureOutput(heading)
    else:
      self._DiscardOutput(heading)

  def Example(self, line):
    # ensure this example is in the EXAMPLES section
    if self._heading == 'EXAMPLES':
      # if previous line ended in a backslash, it is not the last line of the
      # command so append new line of command to command_text
      if self.command_text and self.command_text.endswith('\\'):
        self.command_text += line.strip()
      # This is the first line of the command and ignore the `$ ` in it.
      else:
        self.command_text = line.replace('$ ', '')
      # if the current line doesn't end with a `\`, it is the end of the command
      # so self.command_text is the whole command
      if not line.endswith('\\'):
        self.example = True
        # check that the example starts with the command of the help text
        if self.command_text.startswith(self.command_name):
          rest_of_command = self.command_text[self.command_name_length:].split()
          flag_names = []
          for word in rest_of_command:
            word = word.replace('\\--', '--')
            if word.startswith('--'):
              flag_names.append(word[2:])
          # Until b/121254697 is resolved, this line will not be active
          # self._analyze_example_flags_equals(flag_names)

  # TODO(b/121254697): this check shouldn't apply to boolean flags
  def _analyze_example_flags_equals(self, flags):
    for flag in flags:
      if '=' not in flag:
        self.violation_flags.append(flag)

  def _analyze_name(self, section):
    warnings = self.check_for_personal_pronouns(section)
    self.command_name = section.strip().split(' - ')[0]
    if len(section.strip().split(' - ')) == 1:
      self.name_section = ''
      warnings += '\nPlease add an explanation for the command.'
    self.command_name_length = len(self.command_name)
    # check that name section is not too long
    if len(section.split()) > self._NAME_WORD_LIMIT:
      warnings += '\nPlease shorten the name section to less than '
      warnings += str(self._NAME_WORD_LIMIT) + ' words.'
    if warnings:
      # TODO(b/119550825): remove the go/ link from open source code
      self._file_out.write('Refer to the detailed style guide: '
                           'go/cloud-sdk-help-guide#name\nThis is the '
                           'analysis for NAME:')
      self._file_out.write(warnings + '\n\n')
    else:
      self._file_out.write('There are no errors for the NAME section.\n\n')

  def _analyze_examples(self, section):
    warnings = self.check_for_personal_pronouns(section)
    if self.violation_flags:
      warnings += '\nThere should be a `=` between the flag name and the value.'
      warnings += '\nThe following flags are not formatted properly:'
      for flag in self.violation_flags:
        warnings += '\n' + flag
    if warnings:
      # TODO(b/119550825): remove the go/ link from open source code
      self._file_out.write('Refer to the detailed style guide: '
                           'go/cloud-sdk-help-guide#examples\n'
                           'This is the analysis for EXAMPLES:')
      self._file_out.write(warnings + '\n\n')
    else:
      self._file_out.write('There are no errors for the EXAMPLES '
                           'section.\n\n')

  def _analyze_description(self, section):
    warnings = self.check_for_personal_pronouns(section)
    if warnings:
      # TODO(b/119550825): remove the go/ link from open source code
      self._file_out.write('Refer to the detailed style guide: '
                           'go/cloud-sdk-help-guide#description\n'
                           'This is the analysis for DESCRIPTION:')
      self._file_out.write(warnings + '\n\n')
    else:
      self._file_out.write('There are no errors for the DESCRIPTION '
                           'section.\n\n')

