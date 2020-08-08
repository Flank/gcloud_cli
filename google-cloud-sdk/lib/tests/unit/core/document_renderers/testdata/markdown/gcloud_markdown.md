# GCLOUD_MARKDOWN(1)


## NAME

gcloud markdown - markdown group docstring index


## SYNOPSIS

`gcloud markdown` _COMMAND_ [*--optional-flag* _OPTIONAL_FLAG_] *--required-flag* _REQUIRED_FLAG_ [_GCLOUD-WIDE-FLAG ..._]

## DESCRIPTION

Markdown group docstring description.

This is a markdown test. If you change the docstrings or help strings
or argparse flags or argparse positionals in this file you should get
test regressions.

Markdown DESCRIPTION detailed_help. The index entry is `_Markdown group docstring index._`.
Here comes _italic_ emphasis. And here comes *bold* emphasis. And
asciidoc(1) says `monospace` looks like this, but I think its really
literal. And Cloud SDK has its own `_text_` emphasis.

Markdown lists are supported:

* First item.
** First sub-item.
* Second item.
* Last item for now.
** Last sub-item for now.

Did the end of list work? Also, tables are recognized:

Alias | Project | Image Name
--- | --- | ---
a1a1a | p1p1p | i1ii1
a222 | p2 | i22222i2222
a3aaaa3a3a3 | p3p3pp3p | iii3i3i

Did the end of table work?

I don't, you won't 'and' they didn't.

Look at the files matching $HOME/*.txt or */x.

And some manpage *ssh*(1)/*scp*(1) references. And alternate
*ssh(1)*/*scp(1)* style too.

Or maybe */* and *.go or why *.py.

And what `_happens_` with `_air quotes_`. And _then_ there's 'literal'
quotes too.

Perhaps *.c?

And here are some hanging indent lists:

*outer*::

This is a big category:

*inner-1*::: This is an inline example.
*inner-2*::: Another example with no line separation.

*inner-3*::: And a third one. With blah blah blah blah blah blah blah blah blah blah blah blah blah blah wrapping text.

*inner-4*:::
On a separate line. With more blah blah blah blah blah.
And a second line.

*outer-2*::

And a smaller category:

*inner-2-1*:::

This is the first inner of the second outer.
+
And this is the second paragraph of the first inner of the second
outer.

And this should be back to normal text.

  $ link:../with/a/command/line[gcloud with a command line] EXAMPLE

and more prose

  # example command.
  $ echo and more commands

And the conclusion.


## FLAGS

*--optional-flag* _OPTIONAL_FLAG_::

Optional flag.

*--required-flag* _REQUIRED_FLAG_::

Required flag.


## GCLOUD WIDE FLAGS

Run *$ link:../[gcloud] help* for a description of flags available to
all commands.


## COMMANDS

`_COMMAND_` is one of the following:

*link:markdown-command[markdown-command]*::

Markdown command docstring index.


## EXAMPLES

Inline $ link:../command-group/sub-sommand[gcloud command-group sub-sommand] POSITIONAL command examples
should become links. And example blocks should be monospace with
links:

  $ link:../group/sub-command/list[gcloud group sub-command list] POSITIONAL
  $ link:../upper/case/stop/command[gcloud upper case stop command] ABC-DEF abc xyz
  $ link:../group-a/command[gcloud group-a command] example-arg a b c
  $ link:../group-b/subgroup-c/command[gcloud group-b subgroup-c command] my-arg a b c
  $ link:../with/group[gcloud with group] sample-arg a b c
  $ link:../group/set/property/value/a/b/c[gcloud group set] property value a b c
  $ link:../group/unset/property/a/b/c[gcloud group unset] property a b c

Long examples should scroll horizontally:

  $ link:../group/long-windeded/super-verbose/way/too-long/who-could[gcloud group long-windeded super-verbose way too-long who-could] \
      ever remember-this obscure-command maybe too much of-the \
      underlying-api IS EXPOSED

And how does a multi-line example fare?

  $ link:../first/part[gcloud first part]
  $ link:../second/part[gcloud second part]

And the conclusion.
