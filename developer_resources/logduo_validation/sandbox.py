"""
first_script.py

Logduo example.

Demonstrates:
- session configuration
- help
- verbosity
- standard log levels
- custom levels
- message wrapping
- structured blocks (messages containing \n)
- output path helpers
- additional log files
- log.close()

Last edited: 2026-6-22
"""

from pathlib import Path

from rich.text import Text

from logduo import log

# from logduo import log, text_table, run
PROJECT_ROOT = Path(__file__).resolve().parents[2]
log_dir = (
    PROJECT_ROOT
    / "developer_resources"
    / "logduo_validation"
    / "logs"
)


# verbosity=3 so DEBUG and TRACE messages are visible in example_scripts
log.configure(
    log_dir_path=log_dir,
    console_wrap_width=150,
    log_wrap_width=80,
)

log("hello world")
log("")
log(
    'Testing line options: no_prefix=True, console_style="italic blue", '
    'left_indent=27, and log_wrap_width=80. '
    'Console wrapping is controlled separately by console_wrap_width '
    f'(current session value: {log.session_config.console_wrap_width}).',
    no_prefix=True,
    console_style="italic blue",
    left_indent=27,
    log_wrap_width=80,
)

log({"a": 1, "b": 2})

log([1, 2, 3])

log(12345)

class Example:

    pass


log(Example())

long_dict = {

    "project_name": "Logduo demonstration project",

    "description": "A deliberately long dictionary used to test how ordinary Python objects are displayed when their string representation exceeds the available console and log width.",

    "version": "0.2.0",

    "author": "Example User",

    "status": "active",

    "features": [

        "console logging",

        "plain-text log files",

        "Rich Text support",

        "custom logging levels",

        "additional user loggers",

    ],

    "configuration": {

        "console_wrap_width": 120,

        "log_wrap_width": 80,

        "console_verbosity": 3,

        "log_verbosity": 3,

        "console_prefix": "level",

        "log_prefix": "timestamp",

    },

    "statistics": {

        "files_processed": 127,

        "records_processed": 18432,

        "warnings": 7,

        "errors": 2,

    },

}

log(long_dict)


# --- Basic text examples with left_indent -------------------------------------
log("")
log("*** Basic text examples with left_indent ***")

# Inline via log()
log(
    "(left_indent=5, inline via log()) plain string",
    left_indent=5,
)

# Inline via log.info()
log.info(
    "(left_indent=5, inline via log.info()) plain string",
    left_indent=5,
)

# Long inline string: verify wrapping keeps the same left indent
log(
    "(left_indent=5, wrapped inline) This is a deliberately long plain-text "
    "message intended to wrap across multiple physical lines so the continuation "
    "lines can be checked for the same left indentation.",
    left_indent=5,
)

# Larger indent + wrapping
log(
    "(left_indent=13, wrapped inline, no_prefix=False) This is another deliberately long message "
    "used to verify that a larger left indent reduces the available content width "
    "and remains aligned on wrapped continuation lines.",
    left_indent=13,  no_prefix=False,
)

log(
    "(left_indent=13, wrapped inline, no_prefix=True) This is another deliberately long message "
    "used to verify that a larger left indent reduces the available content width "
    "and remains aligned on wrapped continuation lines.",
    left_indent=13,  no_prefix=True,
)

# Simple structured block
log(
    "(left_indent=13, structured block) line one\n"
    "line two\n"
    "line three",
    left_indent=13,
)

# Structured block with an interior blank line
log(
    "(left_indent=8, interior blank line) line one\n"
    "\n"
    "line three",
    left_indent=8,
)

# Structured block with leading newline
log(
    "\n"
    "(left_indent=6, leading newline preserved) hello",
    left_indent=6,
)

# Structured block with trailing newline
log(
    "(left_indent=6, trailing newline preserved) hello\n",
    left_indent=6,
)

# Structured block with both leading and trailing newlines
log(
    "\n"
    "(left_indent=6, leading + trailing newlines preserved) hello"
    "\n",
    left_indent=6,
)

# Leading, trailing, and interior blank lines together
log(
    "\n"
    "(left_indent=10, full block test) first content line\n"
    "\n"
    "second content line after interior blank line\n"
    "\n"
    "third content line"
    "\n",
    left_indent=10,
)

# Control: same long message without left_indent
log(
    "(control, no left_indent) This is a deliberately long plain-text message "
    "intended to wrap across multiple physical lines for comparison with the "
    "indented versions above."
)


log("")
log("*** RICH examples ***")
# --- Rich Text: short inline -------------------------------------------------
rich_short = Text()
rich_short.append("Rich inline: ", style="bold cyan")
rich_short.append("left_indent = 5", style="yellow")
log(rich_short, left_indent=5)

# --- Rich Text: multiline ----------------------------------------------------
rich_multiline = Text()
rich_multiline.append("Rich block line one", style="bold cyan")
rich_multiline.append("\n")
rich_multiline.append("Rich block line two", style="green")
rich_multiline.append("\n")
rich_multiline.append("Rich block line three", style="magenta")
log(rich_multiline, left_indent=8)

# --- Rich Text: long inline, force wrapping ---------------------------------
rich_long = Text()
rich_long.append("Rich wrapped text: ", style="bold cyan")
rich_long.append(
    "This is deliberately long Rich Text intended to exceed the console "
    "wrap width so we can see whether continuation lines retain the requested "
    "left indentation or fall back to the normal left edge.",
    style="green",
)
log(rich_long, left_indent=5)

# --- Rich Text: styles changing within wrapped text --------------------------
rich_mixed = Text()
rich_mixed.append("START ", style="bold red")
rich_mixed.append(
    "This section is green and deliberately long enough that it should wrap "
    "onto another display line when rendered in the console. ",
    style="green",
)
rich_mixed.append(
    "This final section is blue so we can verify that styling survives "
    "indentation and wrapping.",
    style="bold blue",
)
log(rich_mixed, left_indent=10)

# --- Rich Text: no indent control case ---------------------------------------
rich_control = Text()
rich_control.append("Rich control: ", style="bold cyan")
rich_control.append(
    "This short message provides a comparison.",
    style="yellow",
)
log("rich control:")
log(rich_control)
log("")
log("rich_control without prefix:")
log(rich_control, no_prefix=True)
log("")
log("rich_control without prefix and with indent = 13:")
log(rich_control, no_prefix=True, left_indent=13)
log("rich_control without prefix, with indent = 13, and with console_style='underline green':")
log(rich_control, no_prefix=True, left_indent=13, console_style="underline green")



log.close()
