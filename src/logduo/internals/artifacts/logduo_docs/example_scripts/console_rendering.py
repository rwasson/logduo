"""
console_rendering.py

Demonstrates how Logduo handles styled console output and plain-text logs.

Covers:
- console_style (Logduo message option)
- ANSI color strings
- Rich Text
- Rich Panel
- Rich Table
- PrettyTable / ColorTable string output when installed

Key idea:
- Console output may show color, styling, panels, or tables.
- Log files preserve readable plain text whenever possible.
- Rich renderables display in the console, with placeholders in plain-text logs.
- String tables from PrettyTable / ColorTable can be logged like any other multiline string.

Optional example dependency:
    pip install prettytable

Last edited: 2026-07-08
"""

from pathlib import Path

from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from logduo import log

LOG_DIR = Path.cwd() / "logs"


def section(title: str) -> None:
    log("")
    log("=" * 87)
    log(title)
    log("=" * 87)

def spaces(num: int, *, char: str= " ") -> str:
    spaces_str = char * num
    return spaces_str


def main() -> None:  # noqa: PLR0915   # example scripts can have 'too many statements'
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
        f'console_wrap_width must be an integer. '
        'Current console_wrap_width =' 
        f'{log.session_config.console_wrap_width}.'
    )

    # ------------------------------------------------------------------
    section("console_style (Logduo message option): color in console; plain text in log")

    log("console_style applies color/style to a whole string in the console.")
    log("The plain-text log records the message without console styling.")
    log('Example using console_style: log("console_style example: entire message", console_style="blue")')
    log("console_style example: entire message", console_style="blue")

    # ------------------------------------------------------------------
    section("ANSI color strings: color in console; plain text in log")

    log("ANSI escape codes can color all or part of a string in the console.")
    log("The plain-text log records the same message without ANSI color codes.")
    log('Example using ANSI: log(f"ANSI example: some colored {RED}ANSI red text{RESET} plus more plain text")')
    log(f"ANSI example: some colored {RED}ANSI red text{RESET} plus more plain text")

    # ------------------------------------------------------------------
    section("Rich Text: styled in console; plain text in log")

    log("Rich Text can style (color, bold, italic, ...) all or part of a message in the console.")
    log("The plain-text log records the readable text without Rich styling.")
    log(
        'Example using Rich Text: log(Text("Rich Text Example: (starts next line at far left): ") + '
        'Text.from_markup("[blue]Partial text with color[/blue]"))'
    )
    log(
        Text("Rich Text Example: (starts next line at far left): ")
        + Text.from_markup("[blue]Partial text with color[/blue]")
    )
    log(
        'Example using Rich Text with added spaces:  log( '
        'Text(spaces(13) + "Indented Rich Text: ") '
        '+ Text.from_markup("[blue]Partial text with color[/blue]")')
    log(
        Text(spaces(13) + "Indented Rich Text: ")
        + Text.from_markup("[blue]Partial text with color[/blue]")
    )

    # ------------------------------------------------------------------
    section("Rich Panel: displayed in console; placeholder in log")

    log("Rich Panel is only renderable in the console.")
    log("The console displays the Rich Panel; the plain-text log records a placeholder.")


    log(" ")
    log("Example using Rich Panel: log(rich_panel)")
    rich_panel = Panel.fit(
        long_msg,
        title="Example: Rich Panel around long message",
        style="blue",
    )

    log(rich_panel)

    log("Rich controls layout for Rich renderables.")
    log("Padding shifts the Rich object inside the available console width.")
    log("Set an explicit Rich width if you need exact panel sizing.")
    # available_width = log.session_config.console_wrap_width - 13
    # log("Reference * line: available_width = log.session_config.console_wrap_width - 13")
    # log(spaces(available_width, char="*"))
    log("Example using Rich Panel indented with Rich Padding: "
        "log(Padding(narrow_panel_with_padding, (0, 0, 0, 13)))")

    narrow_panel_with_padding = Panel(
        long_msg,
        title="Example: Rich Panel around long message (with Padding = 13)",
        style="blue",
        width=80,
    )
    log(Padding(narrow_panel_with_padding, (0, 0, 0, 13)))

    # ------------------------------------------------------------------
    section("Rich Table: displayed in console; placeholder in log")

    rich_table = Table(title="Example: Rich Table")
    rich_table.add_column("Name", style="cyan")
    rich_table.add_column("Value", style="green")

    rich_table.add_row("Alpha", "10")
    rich_table.add_row("Beta", "20")
    rich_table.add_row("Gamma", "30")

    log(rich_table)

    log("The same Rich Table can also be padded in the console.")
    log(Padding(rich_table, (0, 0, 0, 13)))

    # ------------------------------------------------------------------
    section("PrettyTable / ColorTable: table string in console and log")

    try:
        import prettytable.colortable as pretty_colortable  # noqa # import not defined in except
    except ImportError:
        log("PrettyTable example skipped: prettytable is not installed.")
        log("Install optional example dependency with: pip install prettytable")
    else:
        pretty_table = pretty_colortable.ColorTable(
            theme=pretty_colortable.Themes.OCEAN
        )
        pretty_table.title = "Example: Pretty_table"
        pretty_table.field_names = ["Name", "Value"]
        pretty_table.align["Name"] = "l"
        pretty_table.align["Value"] = "r"

        pretty_table.add_row([f"{BLUE}Alpha{RESET}", f"{GREEN}10{RESET}"])
        pretty_table.add_row([f"{MAGENTA}Beta{RESET}", f"{YELLOW}20{RESET}"])
        pretty_table.add_row([f"{RED}Gamma{RESET}", f"{WHITE}30{RESET}"])

        table_text = pretty_table.get_string()

        log("PrettyTable / ColorTable creates a formatted multiline string.")
        log("Logduo sends that string to both the console (in color) and the log file (plain).")
        log(table_text)

        padded_table_text = "\n".join(
            f"{' ' * 13}{line}" for line in table_text.splitlines()
        )

        log("The same table string can also be padded before logging.")
        log(padded_table_text)


    log.close()


if __name__ == "__main__":
    main()
