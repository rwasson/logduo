1. Logduo None / _NOT_GIVEN Policy

Public Logduo arguments
-----------------------
For Logduo-owned public arguments:

    argument omitted
        -> represented internally by _NOT_GIVEN when omission
           must be distinguished from an explicit value

    argument=None
        -> invalid unless the API explicitly documents a special meaning

    explicit value
        -> validate and use value


configure()
-----------
configure() is the intentional exception.

Configuration precedence is:

    built-in defaults -> TOML -> configure()

Because configure() receives **kwargs, an omitted argument is represented
by absence of the key and does not require _NOT_GIVEN.

For configure():

    argument omitted
        -> no configure override
        -> TOML value remains effective, if present

    argument=None
        -> explicit configure override
        -> reset field to its built-in schema default
        -> overrides TOML
        -> Source is reported as "configure"

    argument=<value>
        -> explicit configure override
        -> validate/coerce and use value


Loguru passthrough
------------------
Arguments passed through **kwargs by new_loguru_sink() follow Loguru's
native API semantics, including None where Loguru allows it.


Internal None
-------------
None may be used internally when it represents an actual resolved/runtime
state.

Examples:

    omitted exception message -> internal None
    default docs path         -> internal None

    rotation="off"            -> None
    retention="off"           -> None
    compression="off"         -> None

None may also appear in return values/runtime state when a value does not
currently exist, for example:

    main_log_file_path -> Path | None
    output_dir_path    -> Path | None


_NOT_GIVEN
----------
_NOT_GIVEN means only:

    "the caller omitted this argument"

It is an API/resolution sentinel, not a resolved value.

_NOT_GIVEN must never leak into final SessionConfig or runtime data.


Design rule
-----------
_NOT_GIVEN describes omission.

None describes an actual semantic/internal state.

Do not use None to mean "argument omitted."


2. Block strategy
Any string containing "\n" is STRUCTURED.

All user-supplied newlines are preserved:
- leading
- trailing
- interior

A structured message is still one logging event, so the prefix is emitted once.
left_indent applies to nonblank content lines within the block.
Blank lines remain blank.

3. Creation of log dir:
- if startup file requested
    -> ensure run directory + marker

- if new_logger() called uses session output directory

    -> ensure run directory + marker

- if new_loguru_sink called and uses session output directory

    -> ensure run directory + marker

- explicit external sink/docs path

    -> create only that destination

    -> do not materialize unused Logduo run directory

- console-only session

    -> no directory creation

    -> no marker

    -> no pruning
- 