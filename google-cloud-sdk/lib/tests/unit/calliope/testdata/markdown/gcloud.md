# GCLOUD(1)


## NAME

gcloud - markdown top group docstring index


## SYNOPSIS

`gcloud` _GROUP_ [*--configuration*=_CONFIGURATION_] [*--flatten*=[_KEY_,...]] [*--format*=_FORMAT_] [*--help*] [*--verbosity*=_VERBOSITY_; default="warning"] [*-h*] [*--log-http*] [*--top-group-flag*=_TOP_GROUP_FLAG_] [*--no-user-output-enabled*]


## DESCRIPTION

Markdown top group docstring description.


## GLOBAL FLAGS

*--configuration*=_CONFIGURATION_::

The configuration to use for this command invocation. For more
information on how to use configurations, run:
`gcloud topic configurations`.  You can also use the [CLOUDSDK_ACTIVE_CONFIG_NAME] environment
variable to set the equivalent of this flag for a terminal
session.

*--flatten*=[_KEY_,...]::

Flatten _name_[] output resource slices in _KEY_ into separate records
for each item in each slice. Multiple keys and slices may be specified.
This also flattens keys for *--format* and *--filter*. For example,
*--flatten=abc.def* flattens *abc.def[].ghi* references to
*abc.def.ghi*. A resource record containing *abc.def[]* with N elements
will expand to N records in the flattened output. This flag interacts
with other flags that are applied in this order: *--flatten*,
*--sort-by*, *--filter*, *--limit*.

*--format*=_FORMAT_::

Sets the format for printing command output resources. The default is a
command-specific human-friendly output format. The supported formats
are: `config`, `csv`, `default`, `diff`, `disable`, `flattened`, `get`, `json`, `list`, `multi`, `none`, `object`, `table`, `text`, `value`, `yaml`. For more details run $ link:gcloud[gcloud] topic formats.

*--help*::

Display detailed help.

*--verbosity*=_VERBOSITY_; default="warning"::

Override the default verbosity for this command with any of the supported standard verbosity levels: `debug`, `info`, `warning`, `error`, and `none`. Overrides the default *core/verbosity* property value for this command invocation.

*-h*::

Print a summary help and exit.


## OTHER FLAGS

*--log-http*::

Log all HTTP server requests and responses to stderr. Overrides the default *core/log_http* property value for this command invocation.

*--top-group-flag*=_TOP_GROUP_FLAG_::

Top group flag detailed help.

*--user-output-enabled*::

Print user intended output to the console. Overrides the default *core/user_output_enabled* property value for this command invocation. Use *--no-user-output-enabled* to disable.


## GROUPS

`_GROUP_` is one of the following:

*link:gcloud/markdown[markdown]*::

Markdown group docstring index.
