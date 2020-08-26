#! /bin/bash
# Copyright 2016 Google LLC. All Rights Reserved.
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


# Run the gcloud TAB completion tests.

set -e

if [[ $0 == */* ]]; then
  test_dir=${0%/*}
else
  test_dir=.
fi

test_flags=''
test_cases=$test_dir/testcases
if [[ ! -r $test_cases ]]; then
  echo testcases file not found >&2
  exit 2
fi
test_count=0
test_passed=0
test_shell=/bin/bash
test_trace=0

while (( $# )); do
  case $1 in
    --no-*)
      test_flags+=,${1#--}
      ;;
    --shell=*)
      test_shell=${1#*=}
      ;;
    --test-cases=*)
      test_cases=${1#*=}
      ;;
    --trace)
      test_trace=1
      ;;
    --*)
      echo "$0: $1: unknown flag -- --shell=SHELL  or --no-* expected." >&2
      echo "Usage: $ [ --shell=SHELL --test-cases=FILE --no-* ]" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
  shift
done

shell=$(basename $test_shell)
gcloud_dir=$1
if [[ $gcloud_dir != '' ]]; then
  completion_script="$gcloud_dir"/completion.$shell.inc
else
  echo "No argument specified for directory of $shell completion file" >&2
  exit 2
fi
unset IFS
if [[ ! -r $completion_script ]]; then
  echo $shell "$completion_script" not found >&2
  exit 2
fi

current_shell=$(ps -o "command=" -p "$$" | cut -d " " -f 1)

if [[ "$test_shell" != "$current_shell" ]]; then
    export SHELL=$test_shell
    $test_shell "$0" --shell="$test_shell" $gcloud_dir
    exitval=$?
    unset -f gsutil
    exit $exitval
fi

[[ $current_shell == *zsh ]] && emulate sh


run_test() {
  # Called by test_case to run one completion test case.
  #
  # Args:
  #   $1  The command line.
  #   $2  The expected completion.

  local expected="$2" tail
  declare -i last
  COMP_LINE=$1
  COMP_POINT=${#COMP_LINE}
  COMP_WORDS=($COMP_LINE)
  ((last= ${#COMP_WORDS[@]} - 1))
  unset IFS
  if [[ "${COMP_WORDS[last]}" == *=?* ]]; then
    name=${COMP_WORDS[last]%%=*}
    value=${COMP_WORDS[last]#*=}
    COMP_WORDS[last]=$name
    COMP_WORDS+=( = $value)
  fi
  COMP_CWORD=${#COMP_WORDS[@]}
  unset COMPREPLY
  ((last= $# - 1))
  "$fname" "${COMP_WORDS[0]}" "${COMP_WORDS[last]}" "${COMP_WORDS[last-1]}"
  actual="${COMPREPLY[*]}"

  if [[ $expected != "$actual" ]]; then
    if [[ $actual == *' '?* ]]; then
      # Sort multiple reply args to match the already sorted expected value.
      if [[ $actual == *' ' ]]; then
        tail=' '
        actual=${actual%$tail}
      else
        tail=''
      fi
      set -- $(echo "$actual" | tr ' ' '\n' | sort)
      actual=$*$tail
    fi
    if [[ $expected != "$actual" ]]; then
      echo FAIL test $test_count "'$COMP_LINE' : '$expected' != '$actual'" >&2
      return 1
    fi
  fi
  return 0
}

add_to_cache() {
   fpath=$path/"$1"
   [[ ! -d $fpath ]] && mkdir -p "$fpath"
   if [[ ! -f $fpath/_names_ ]]; then
     echo  "$2" > "$fpath/_names_"
     echo  ___ >> "$fpath/_names_"
   fi
   touch -r "$fpath/_names_" -d '10 minutes' "$fpath/_names_"
}

test_case() {
  # Sets up the test and calls run_test() to run the test
  #
  # Args:
  #   1  The command line.
  #   2   The expected completion.
  #   3   If specified, the completion resource

  (( ++test_count ))

  # Reset the completer state.
  __gcloud__flag_key=''

  if [[ $SHELL == *bash && $3 != '' ]]; then
    add_to_cache "$3" "$2"
  fi
  if run_test "$1" "$2"; then
    (( ++test_passed ))
  fi
}

# mock gsutil when called in completer
function gsutil {
    echo '/tmp/foobar ' >&8
}

# name of the gcloud completion function
fname=_python_argcomplete
path=$HOME/.config/gcloud/completion_cache/$LOGNAME@google.com
[[ $current_shell == *zsh ]] && emulate zsh
source "$completion_script"
[[ $current_shell == *zsh ]] && emulate sh
source $test_dir/testcases
(( test_passed == test_count )) && exit 0
exit 1
