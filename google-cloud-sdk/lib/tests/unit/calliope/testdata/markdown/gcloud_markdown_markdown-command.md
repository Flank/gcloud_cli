# GCLOUD_MARKDOWN_MARKDOWN-COMMAND(1)


## NAME

gcloud markdown markdown-command - markdown command docstring index


## SYNOPSIS

`gcloud markdown markdown-command` [[_USER_@]_INSTANCE_:]_SRC_ [[[_USER_@]_INSTANCE_:]_SRC_ ...] [[_USER_@]_INSTANCE_:]_DEST_ [_USER_@]_INSTANCE_ *--required-flag*=_REQUIRED_FLAG_ *--z-required-flag*=_Z_REQUIRED_FLAG_ [*--y-common-flag*=_Y_COMMON_FLAG_; default="VALUE"] [*--choices-dict*=_CHOICE_; default="none"] [*--choices-dict-arg-list*=[_CHOICE_,...]; default="none"] [*--choices-dict-bloviate*=_CHOICE_; default="none"] [*--choices-dict-only-one-choice-yes-we-really-do-this*=_CHOICE_; default="this-is-it"] [*--choices-list*=_CHOICE_; default="none"] [*--choices-list-arg-list*=[_CHOICE_,...]; default="none"] [*--choices-list-only-one-choice-yes-we-really-do-this*=_CHOICE_; default="this-is-it"] [*--dict-flag*=[_ITEM_,...]; default="aaa=1,bbb=22,ccc=aha"] [*--list-flag*=[_ITEM_,...]; default="aaa,bbb,ccc"] [*--optional-flag*=_OPTIONAL_FLAG_] [*--question-flag*[=_QUESTION_FLAG_]] [*--root-flag*=_ROOT_PATH_; default="/"] [*--store-false-default-false-flag*] [*--store-false-default-none-flag*] [*--no-store-false-default-true-flag*] [*--store-true-default-false-flag*] [*--store-true-default-none-flag*] [*--no-store-true-default-true-flag*] [*--value-flag*=_VALUE_FLAG_; default="VALUE"] [*--filter*=_EXPRESSION_] [_GCLOUD_WIDE_FLAG ..._] [-- _IMPLEMENTATION_ARGS_ ...]


## DESCRIPTION

Markdown command docstring description. This is a markdown test. If you
change the docstrings or help strings or argparse flags or argparse
positionals in this file you should get test regressions. Use
gcloud markdown foo. Don't forget the `_MAGIC_SAUCE@FOO_BAR.COM_` arg.
See *link:gcloud/command/abc-xyz/list[gcloud command abc-xyz list]*(1) or run $ link:gcloud[gcloud] command abc-xyz list --help
for more information.


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

[-- _IMPLEMENTATION_ARGS_ ...]::

Flags and positionals passed to the underlying ssh implementation.
+
        The '--' argument must be specified between gcloud specific args on
        the left and IMPLEMENTATION-ARGS on the right. Example:
+
          $ gcloud markdown markdown-command example-instance \
      --zone us-central1-a -- -vvv -L 80:%INSTANCE%:80
+
+
The '--' argument must be specified between gcloud specific args on the left and IMPLEMENTATION_ARGS on the right.


## REQUIRED FLAGS

*--required-flag*=_REQUIRED_FLAG_::

Required flag.

*--z-required-flag*=_Z_REQUIRED_FLAG_::

Command required flag help.


## COMMONLY USED FLAGS

*--y-common-flag*=_Y_COMMON_FLAG_; default="VALUE"::

Command common flag help.


## FLAGS

*--choices-dict*=_CHOICE_; default="none"::

The ... must be one of ... line should be in this paragraph. _CHOICE_ must be one of:
+
*bar*::: Choice description for bar.
*foo*::: Choice description for foo.
*none*::: Choice description for none.
:::
+

*--choices-dict-arg-list*=[_CHOICE_,...]; default="none"::

The ... must be one of ... line should be in this paragraph. _CHOICE_ must be one of:
+
*bar*::: Choice description for bar.
*foo*::: Choice description for foo.
*none*::: Choice description for none.
:::
+

*--choices-dict-bloviate*=_CHOICE_; default="none"::

Choices dict bloviate flag help.
+
Another paragraph for some complication.
+
The '... must be one of ...' line should be in its own paragraph.
+
_CHOICE_ must be one of:
+
*bar*::: Choice description for bar.
*foo*::: Choice description for foo.
*none*::: Choice description for none.
:::
+

*--choices-dict-only-one-choice-yes-we-really-do-this*=_CHOICE_; default="this-is-it"::

Automaticallly fess up to only one choice. _CHOICE_ must be (currently only one value is supported):
+
*this-is-it*::: You have no choice in this matter.
:::
+

*--choices-list*=_CHOICE_; default="none"::

Choices list flag help. _CHOICE_ must be one of: *bar*, *foo*, *none*.

*--choices-list-arg-list*=[_CHOICE_,...]; default="none"::

Choices list flag help. _CHOICE_ must be one of: *bar*, *foo*, *none*.

*--choices-list-only-one-choice-yes-we-really-do-this*=_CHOICE_; default="this-is-it"::

Automaticallly fess up to only one choice. _CHOICE_ must be (currently only one value is supported): *this-is-it*.

*--dict-flag*=[_ITEM_,...]; default="aaa=1,bbb=22,ccc=aha"::

Command star flag help.

*--list-flag*=[_ITEM_,...]; default="aaa,bbb,ccc"::

Command star flag help.

*--optional-flag*=_OPTIONAL_FLAG_::

Optional flag.

*--question-flag*[=_QUESTION_FLAG_]::

Command question flag help.

*--root-flag*=_ROOT_PATH_; default="/"::

Command root flag help.

*--store-false-default-false-flag*::

Detailed help for --store-false-default-false-flag.

*--store-false-default-none-flag*::

Command store_false flag with None default value.

*--store-false-default-true-flag*::

Command store_false flag with True default value. Enabled by default, use *--no-store-false-default-true-flag* to disable.

*--store-true-default-false-flag*::

Command store_true flag with False default value.

*--store-true-default-none-flag*::

Command store_true flag with None default value.

*--store-true-default-true-flag*::

Command store_true flag with True default value. Enabled by default, use *--no-store-true-default-true-flag* to disable.

*--value-flag*=_VALUE_FLAG_; default="VALUE"::

Command value flag help.


## LIST COMMAND FLAGS

*--filter*=_EXPRESSION_::

Apply a Boolean filter _EXPRESSION_ to each resource item to be listed.
If the expression evaluates `True`, then that item is listed. For more
details and examples of filter expressions, run $ link:gcloud[gcloud] topic filters. This
flag interacts with other flags that are applied in this order: *--flatten*,
*--sort-by*, *--filter*, *--limit*.


## GCLOUD WIDE FLAGS

These flags are available to all commands: --configuration, --flags-file, --flatten, --format, --help, --log-http, --top-group-flag, --user-output-enabled, --verbosity.

Run *$ link:gcloud[gcloud] help* for details.


## SPECIAL MODES

* STOPPED - not running

* RUNNING - not stopped


## EXAMPLES

To foo the command run:

  $ gcloud markdown markdown-command list --foo

To bar the parent command run:

  $ link:gcloud/markdown[gcloud markdown] --bar list


## SEE ALSO

https://foo.bar.com/how-to-foo-the-bar
