"""
rich_and_ansi.py

Demonstrates common Logduo rendering behavior.

Covers:
- console_style
- ANSI colors
- Rich Text
- Rich Panel
- Rich Table
- text_table()
- logging common Python objects

Last edited: 2026-06-16
"""

from pathlib import Path

import matplotlib.pyplot as plt

from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from logduo import log, text_table


LOG_DIR = Path.cwd() / "logs"

def section(title: str) -> None:
    log("")
    log("=" * 87)
    log(title)
    log("=" * 87)


def main() -> None:

    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

    log.configure(
        log_dir_path=LOG_DIR,
        console_wrap_width=100,
        log_wrap_width=120,
    )

    long_msg = ("If you set log_wrap_width in log.configure(), then log strings will be wrapped. "
                f"Current console_wrap_width = {log.session_config.console_wrap_width} (default = 120).")

    # ------------------------------------------------------------------
    section("console_style: renders in console and log (as plain text)")
    log('log("entire message", console_style= \'blue\')')
    log("entire message", console_style='blue')

    # ------------------------------------------------------------------
    section('ANSI: renders in console and log (as plain text)')

    log('log(f"some text plus {{RED}}ANSI red text{{RESET}} plus more text")')
    log("some text, plus {RED}ANSI red text{RESET} plus more text")

    # ------------------------------------------------------------------
    section("Rich Text: renders in console and log (as plain text)")
    log("Rich objects including Text are displayed like multiline structured blocks")
    log("   (flush left on the next line below prefix - so that full line width is available)")
    log('log(Text(f"Normal text: ") + Text.from_markup("[blue]Partial text with color[/blue]"))')
    log(
        Text("Normal text: ")
        + Text.from_markup("[blue]Partial text with color[/blue]")
    )

    # ------------------------------------------------------------------
    section("Rich Panel:  renders in console only (Rich placeholder in log)")
    log("Example with Rich padding: log(Padding(panel, (0, 0, 0, 13)))")
    panel = Panel.fit(
        long_msg,
        title="Example: Rich Panel (padded)",
        style="blue",
    )
    log(Padding(panel, (0, 0, 0, 13)))


    # ------------------------------------------------------------------
    section("Rich Table: renders in console only (Rich placeholder in log)")
    rich_table = Table(
        title=(
            "Example: Rich\n"
            "Table with Padding"
        )
    )


    rich_table.add_column("Name", style="cyan")
    rich_table.add_column("Value", style="green")
    rich_table.add_row("[blue]Alpha[/blue]", "[green]10[/green]")
    rich_table.add_row("[magenta]Beta[/magenta]", "[yellow]20[/yellow]")
    rich_table.add_row("[red]Gamma[/red]", "[bright_white]30[/bright_white]")

    log(Padding(rich_table, (0, 0, 0, 13)))

    # ------------------------------------------------------------------
    section("Logduo's text_table(): renders in console and log")


    rows = [
        {"Name": f"{BLUE}Alpha{RESET}", "Value": f"{GREEN}10{RESET}"},
        {"Name": f"{MAGENTA}Beta{RESET}", "Value": f"{YELLOW}20{RESET}"},
        {"Name": f"{RED}Gamma{RESET}", "Value": f"{WHITE}30{RESET}"},
    ]

    logduo_table = text_table(
        rows,
        title="Example: Logduo",
        subtitle="text_table() with indent",
        header_labels=["Name", "Value"],
        indent=13,
    )

    log(logduo_table)



    # -------------------------------------------------------------------------
    section('Logging Objects')

    x = [1, 2, 3, 4, 5]
    y = [1, 4, 9, 16, 25]


    fig = plt.figure()
    plt.plot(x, y)

    assert log.output_dir_path is not None
    image_path = (log.output_dir_path / "example_plot.png").resolve()

    plt.savefig(image_path)
    plt.close()
    log("")
    log(f"Example logging a Path object: {image_path}")
    log("")
    log(f"Example logging of a plot figure (placeholder only - does not convert to text): {fig}")

    log.close()


if __name__ == "__main__":

    main()

