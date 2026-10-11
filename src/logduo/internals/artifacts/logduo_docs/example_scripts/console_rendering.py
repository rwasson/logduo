"""
console_rendering.py

Demonstrates how Logduo renders strings and Python objects in the console
and in plain-text log files.

Covers:
- simple strings
- multiline strings
- console_style
- ANSI-styled strings
- ordinary Python objects
- Rich Text
- Rich Panel
- Rich Table
- Rich Padding
- PrettyTable / ColorTable string output when installed
- Logduo text_table() plain-text table formatting

Key ideas:
- Simple text-like values are displayed inline with the prefix.
- Multiline strings are displayed below the prefix with their line layout preserved.
- Rich objects are displayed below the prefix in the console.
- Rich Text is written as readable plain text in log files.
- Other Rich objects are represented by placeholders in plain-text logs.
- left_indent applies to strings and Rich Text.
- Rich Padding can be used to indent other Rich objects.

Optional example dependency:
    pip install prettytable
    pip install matplotlib

Last edited: 2026-08-10
"""

from __future__ import annotations

import importlib
from pathlib import Path

from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from logduo import log, text_table

LOG_DIR = Path.cwd() / "logs"

BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[97m"
RESET = "\033[0m"


log.configure(
    log_dir_path=LOG_DIR,
    console_wrap_width=120,
    log_wrap_width=120,
)

long_msg = (
    'If you set log_wrap_width in log.configure(), then log strings '
    'will be wrapped. The default log_wrap_width = "off". '
    'console_wrap_width must be an integer. '
    f'Current console_wrap_width = {log.session_config.console_wrap_width}.'
)


# --- 1. Simple strings --------------------------------------------------------

log("")
log("1. Simple strings: inline with prefix", console_style="blue bold")

log("Simple strings without \\n are displayed on the same line as the prefix.")

log(
    "Long simple strings wrap beneath the start of the message. "
    "This deliberately long example demonstrates how Logduo keeps wrapped "
    "continuation lines aligned with the beginning of the message."
)

log(
    'Demo of line options: no_prefix=True, console_style="italic blue", '
    'left_indent=13, and log_wrap_width=80. '
    'Console wrapping is controlled separately by console_wrap_width '
    f'(current session value: {log.session_config.console_wrap_width}).',
    no_prefix=True,
    console_style="italic blue",
    left_indent=13,
    log_wrap_width=80,
)


# --- 2. Multiline strings -----------------------------------------------------

log("")
log("2. Multiline strings: displayed below prefix", console_style="blue bold")

log(
    "Strings containing \\n are displayed below the prefix "
    "to preserve maximum display width"
)

multiline_text = (
    "Step 1: Load data\n"
    "Step 2: Clean data\n"
    "Step 3: Analyze results"
)

log(multiline_text)

log("The same multiline string can be indented using left_indent.")

log(
    multiline_text,
    left_indent=13,
)

log("Leading, trailing, and interior blank lines are also preserved.")

log(
    "\n"
    "First content line\n"
    "\n"
    "Second content line after an intentional blank line\n"
)


# --- 3. Styled strings --------------------------------------------------------

log("")
log("3. Styled strings: console_style and ANSI", console_style="blue bold")

log("console_style applies a Rich style to the whole string in the console.")
log("The plain-text log records the message without console styling.")

log(
    'Example: log("console_style example", console_style="blue")'
)

log(
    "console_style example: entire message",
    console_style="blue",
)

log("ANSI escape codes can style all or part of a string in the console.")
log("ANSI codes are removed from the plain-text log.")

log(
    f"ANSI example: plain text, {RED}red text{RESET}, "
    f"{GREEN}green text{RESET}, then plain text again."
)


# --- 4. Ordinary Python objects ----------------------------------------------

log("")
log("4. Ordinary Python objects: text or placeholder representation", console_style="blue bold")

log(
    "Python objects with useful text representations are displayed inline "
    "with the prefix, like ordinary text."
)

log({"a": 1, "b": 2})
log([1, 2, 3])
log(12345)

long_dict = {
    "project_name": "Logduo demonstration project",
    "description": (
        "A deliberately long dictionary used to demonstrate how ordinary "
        "Python objects are displayed when their string representation exceeds "
        "the available console and log width."
    ),
    "version": "0.2.0",
    "status": "active",
    "features": [
        "console logging",
        "plain-text log files",
        "Rich Text support",
        "custom logging levels",
        "additional user loggers",
    ],
    "configuration": {
        "console_wrap_width": log.session_config.console_wrap_width,
        "log_wrap_width": log.session_config.log_wrap_width,
        "console_verbosity": log.session_config.console_verbosity,
        "log_verbosity": log.session_config.log_verbosity,
    },
    "statistics": {
        "files_processed": 127,
        "records_processed": 18432,
        "warnings": 7,
        "errors": 2,
    },
}

log(long_dict)


class Example:
    pass


log(
    "Objects without a more useful text representation may appear as a "
    "standard Python object placeholder."
)

log(Example())


# --- 5. Rich Text -------------------------------------------------------------

log("")
log("5. Rich Text: styled in console; plain text in log", console_style="blue bold")

log(
    "Rich Text is displayed below the prefix in the console and written as "
    "readable plain text in the log file."
)

rich_text = (
    Text("Rich Text example: ", style="bold")
    + Text.from_markup("[blue]partial blue text[/blue]")
)

log(rich_text)

log(
    "left_indent can be applied directly to Rich Text while preserving its "
    "Rich styling."
)

log(
    rich_text,
    left_indent=13,
)

log(
    "console_style can also apply an additional style to the complete Rich "
    "Text message."
)

log(
    rich_text,
    left_indent=13,
    console_style="underline green",
)


# --- 6. Rich Panel ------------------------------------------------------------

log("")
log("6. Rich Panel: console renderable; placeholder in log", console_style="blue bold")

log(
    "Rich Panel is rendered below the prefix in the console. "
    "The plain-text log records a placeholder."
)

rich_panel = Panel.fit(
    long_msg,
    title="Example: Rich Panel around long message",
    style="blue",
)

log(rich_panel)

log(
    "left_indent does not alter the layout of Rich Panel. "
    "Use Rich Padding when indentation is desired."
)

narrow_panel = Panel(
    long_msg,
    title="Example: Rich Panel with Padding = 13",
    style="blue",
    width=80,
)

log(
    Padding(
        narrow_panel,
        (0, 0, 0, 13),
    )
)


# --- 7. Rich Table ------------------------------------------------------------

log("")
log("7. Rich Table: console renderable; placeholder in log", console_style="blue bold")

log(
    "Rich Table is rendered below the prefix in the console. "
    "The plain-text log records a placeholder."
)

rich_table = Table(title="Example: Rich Table")
rich_table.add_column("Name", style="cyan")
rich_table.add_column("Value", style="green")

rich_table.add_row("Alpha", "10")
rich_table.add_row("Beta", "20")
rich_table.add_row("Gamma", "30")

log(rich_table)

log("Rich Padding can also indent the entire table.")

log(
    Padding(
        rich_table,
        (0, 0, 0, 13),
    )
)


# --- 8. PrettyTable / ColorTable ---------------------------------------------

log("")
log("8. PrettyTable / ColorTable: multiline string", console_style="blue bold")

try:
    pretty_colortable = importlib.import_module("prettytable.colortable")
except ImportError:
    log("PrettyTable example skipped: prettytable is not installed.")
    log("Install optional example dependency with: pip install prettytable")
else:
    pretty_table = pretty_colortable.ColorTable(
        theme=pretty_colortable.Themes.OCEAN
    )

    pretty_table.title = "Example: PrettyTable / ColorTable"
    pretty_table.field_names = ["Name", "Value"]
    pretty_table.align["Name"] = "l"
    pretty_table.align["Value"] = "r"

    pretty_table.add_row(
        [f"{BLUE}Alpha{RESET}", f"{GREEN}10{RESET}"]
    )
    pretty_table.add_row(
        [f"{MAGENTA}Beta{RESET}", f"{YELLOW}20{RESET}"]
    )
    pretty_table.add_row(
        [f"{RED}Gamma{RESET}", f"{WHITE}30{RESET}"]
    )

    table_text = pretty_table.get_string()

    log(
        "PrettyTable / ColorTable produces a formatted multiline string, "
        "so Logduo handles it like any other multiline string."
    )

    log(table_text)

    log("The same table string can be indented using left_indent.")

    log(
        table_text,
        left_indent=13,
    )


# --- 9. text_table() ----------------------------------------------------------

log("")
log("9. text_table(): plain-text tables from Python data", console_style="blue bold")

log(
    "text_table() creates a formatted plain-text table from common Python data. "
    "The returned string can be printed directly or passed to Logduo."
)

log("Simple example: a dictionary is automatically displayed as a Field / Value table.")

settings = {
    "console_theme": "dark",
    "console_wrap_width": 120,
    "log_wrap_width": 120,
    "output_directory": LOG_DIR,
}

log(
    text_table(
        settings,
        title="Example: dictionary",
    )
)

log(
    "More advanced example: a list of dictionaries is automatically displayed "
    "as rows and columns. Display options can customize labels, widths, and wrapping."
)

investment_data = [
    {
        "name": "Alpha Fund",
        "type": "Mutual Fund",
        "value": "$125,430",
        "description": "Broad-market equity fund used as a core holding.",
    },
    {
        "name": "Beta Bond",
        "type": "Bond",
        "value": "$42,750",
        "description": (
            "Intermediate-term bond holding used for income and diversification."
        ),
    },
    {
        "name": "Gamma Corp",
        "type": "Stock",
        "value": "$18,900",
        "description": "Individual company stock position.",
    },
]

log(
    text_table(
        investment_data,
        title="Example: investment holdings",
        header_labels=["Name", "Type", "Value", "Description"],
        max_col_widths=[20, 14, 12, 30],
        wrap_table_width=90,
    )
)

# --- 10. Objects that are not console renderables -----------------------------

log("")
log("10. Other objects: placeholder representation", console_style="blue bold")
log(
    "Some Python objects, such as matplotlib Figure objects, cannot be "
    "displayed directly by Logduo. Logduo displays their object representation "
    "instead. Save figures or images to a file when the visual output is needed."
)


try:
    plt = importlib.import_module("matplotlib.pyplot")

except ImportError:
    log("Matplotlib example skipped: matplotlib is not installed.")

else:
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Example matplotlib Figure")

    log("Example: log(fig)")
    log(fig)

    plt.close(fig)

log.close()
