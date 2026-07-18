"""
summary_table_builder.py

Last edited: 2026-06-11
"""

from pathlib import Path

from developer_resources.pytest_harness_old.classes import AggregateTestSummary


# --- _build_summary_table() ----------------------------------------------
def _build_summary_table(
    *,
    summary_data: AggregateTestSummary,
) -> str:
    """
    Builds text string for reporting testing output from an instance of
    AggregateTestSummary.
    """
    round_digit = 0
    divider_width = 60


    lines = [
        "═" * divider_width,
        "       TEST SUMMARY",
        "═" * divider_width,
        "",
        f"Source files covered:       {summary_data.source_file_count}",
        f"Test files run:             {summary_data.test_file_count}",
        "",
        "Test file outcomes:",
        "-" * divider_width,
        f"    Passed all tests:        {summary_data.passed_test_file_count}",
        f"    Had failures:            {summary_data.failed_test_file_count}",
        f"    Had errors:              {summary_data.error_test_file_count}",
        f"    Had skipped tests:       {summary_data.skipped_test_file_count}",
        f"    Had xfailed tests:       {summary_data.xfailed_test_file_count}",
        f"    Had xpassed tests:       {summary_data.xpassed_test_file_count}",
        "",
        "Individual test function outcomes:",
        "-" * divider_width,
        f"    Passed:                  {summary_data.passed_test_function_count}",
        f"    Failed:                  {summary_data.failed_test_function_count}",
        f"    Errors:                  {summary_data.error_test_function_count}",
        f"    Skipped:                 {summary_data.skipped_test_function_count}",
        f"    XFailed:                 {summary_data.xfailed_test_function_count}",
        f"    XPassed:                 {summary_data.xpassed_test_function_count}",
        "",
        "Note: While an individual test can only have one type of outcome, ",
        "      a test file can have multiple outcomes."
    ]

    if summary_data.problem_test_files:
        lines.append("")
        lines.append(f"Test files with problems ({len(summary_data.problem_test_files)}):")
        lines.append("-" * divider_width)

        for problem_file in summary_data.problem_test_files:
            lines.append(
                f"    {problem_file.test_file_name}"
                f" ({problem_file.problem_count} problem/s)"
            )
            if problem_file.failed_test_function_names:
                lines.append("        FAILURES:")
                for test_name in problem_file.failed_test_function_names:
                    lines.append(f"            - {test_name}")
            if problem_file.error_test_function_names:
                lines.append("        ERRORS:")
                for test_name in problem_file.error_test_function_names:
                    lines.append(f"            - {test_name}")
            if problem_file.skipped_test_function_names:
                lines.append("        SKIPPED:")
                for test_name in problem_file.skipped_test_function_names:
                    lines.append(f"            - {test_name}")
            if problem_file.xfailed_test_function_names:
                lines.append("        XFAILED:")
                for test_name in problem_file.xfailed_test_function_names:
                    lines.append(f"            - {test_name}")
            if problem_file.xpassed_test_function_names:
                lines.append("        XPASSED:")
                for test_name in problem_file.xpassed_test_function_names:
                    lines.append(f"            - {test_name}")

    if summary_data.unexecuted_test_files:
        lines.append("")
        lines.append(
            f"Test files with zero executed test functions "
            f"({len(summary_data.unexecuted_test_files)}):"
        )
        lines.append("-" * divider_width)
        for test_file_name in summary_data.unexecuted_test_files:
            lines.append(f"    {test_file_name}")

    lines.append("")
    lines.append("Coverage")
    lines.append("-" * divider_width)
    lines.append(f"    Statements:      {summary_data.statement_coverage_pct:.{round_digit}f}%")
    lines.append(f"    Branches:        {summary_data.branch_coverage_pct:.{round_digit}f}%")
    lines.append(f"    Total:           {summary_data.total_coverage_pct:.{round_digit}f}%")

    lines.append("")
    lines.append("Statement coverage (executed/statements) by source file:")
    lines.append("-" * divider_width)
    for source_file_coverage_record in summary_data.source_file_coverage_records:
        # do not display empty __init__ files
        if source_file_coverage_record.total_line_count == 0:
            continue

        lines.append(
            f"    "
            f"{source_file_coverage_record.statement_coverage_pct:5.0f}%  "
            f"("
            f"{source_file_coverage_record.executed_line_count}"
            f"/"
            f"{source_file_coverage_record.total_line_count}"
            f")"
            f"  "
            f"{Path(source_file_coverage_record.source_file_path).name}"
        )

    return "\n".join(lines)
