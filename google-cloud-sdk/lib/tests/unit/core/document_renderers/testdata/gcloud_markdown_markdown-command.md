# GCLOUD_MARKDOWN_MARKDOWN-COMMAND(1)


## NAME

gcloud markdown markdown-command - markdown command docstring index


## SYNOPSIS

`gcloud markdown markdown-command` [[_USER_@]_INSTANCE_:]_SRC_ [[[_USER_@]_INSTANCE_:]_SRC_ ...] [[_USER_@]_INSTANCE_:]_DEST_ [_USER_@]_INSTANCE_ [*--dict-flag* [_ITEM_,...]; default="aaa=1,bbb=22,ccc=aha"] [*--false-flag*] [*--list-flag* [_ITEM_,...]; default="aaa,bbb,ccc"] [*--optional-flag* _OPTIONAL_FLAG_] [*--question-flag* _QUESTION_FLAG_] [*--root-flag* _ROOT_PATH_; default="/"] [*--true-flag*] [*--value-flag* _VALUE_FLAG_; default="VALUE"] [_GCLOUD-WIDE-FLAG ..._] [-- _IMPLEMENTATION-ARGS_ ...]

## DESCRIPTION

Markdown command docstring description. This is a markdown test. If you
change the docstrings or help strings or argparse flags or argparse
positionals in this file you should get test regressions. Use
gcloud markdown foo. Don't forget the `_MAGIC_SAUCE@FOO_BAR.COM_` arg.


## POSITIONAL ARGUMENTS

[[_USER_@]_INSTANCE_:]_SRC_ [[[_USER_@]_INSTANCE_:]_SRC_ ...]::

Specifies a source file.

[[_USER_@]_INSTANCE_:]_DEST_::

Specifies a destination for the source files.

[_USER_@]_INSTANCE_::

Specifies the instance to SSH into.
+
`_USER_` specifies the username with which to SSH. If omitted,
$USER from the environment is selected.

[-- _IMPLEMENTATION-ARGS_ ...]::

Flags and positionals passed to the underlying ssh implementation.
+
The '--' argument must be specified between gcloud specific args on
the left and IMPLEMENTATION-ARGS on the right. Example:
+
  $ link:../markdown/markdown-command[gcloud markdown markdown-command] example-instance \
      --zone us-central1-a -- -vvv -L 80:%INSTANCE%:80


## FLAGS

*--dict-flag* [_ITEM_,...]; default="aaa=1,bbb=22,ccc=aha"::

Command star flag help.

*--false-flag*::

Command false flag detailed help.

*--list-flag* [_ITEM_,...]; default="aaa,bbb,ccc"::

Command star flag help.

*--question-flag* _QUESTION_FLAG_::

Command question flag help.

*--root-flag* _ROOT_PATH_; default="/"::

Command value flag help.

*--true-flag*::

Command true flag help.

*--value-flag* _VALUE_FLAG_; default="VALUE"::

Command value flag help.


## GROUP FLAGS

*--optional-flag* _OPTIONAL_FLAG_::

Optional flag.


## GCLOUD WIDE FLAGS

Run *$ link:../[gcloud] help* for a description of flags available to
all commands.


## EXAMPLES

To foo the command run:

  $ link:../markdown/markdown-command/list[gcloud markdown markdown-command list] --foo

To bar the parent command run:

  $ link:../markdown[gcloud markdown] --bar list


## NOTES

A special note.
