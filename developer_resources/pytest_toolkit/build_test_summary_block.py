"""
build_test_summary_block.py

Last edited: 2026-06-11
"""

from pathlib import Path

from developer_resources.pytest_toolkit.pytest_harness_classes import AggregateTestSummary


# --- _build_test_summary_block() ----------------------------------------------
def _build_test_summary_block(
    *,
    summary_data: AggregateTestSummary,
) -> str:
    """
    Builds text string for reporting testing output from an instance of
    AggregateTestSummary.
    """
    round_digit = 0
    statement_coverage_pct = 0.0
    branch_coverage_pct = 0.0
    combined_coverage_pct = 0.0

    if summary_data.total_line_count > 0:
        statement_coverage_pct = round(
            100 * summary_data.executed_line_count
            / summary_data.total_line_count,
            round_digit,
        )

    if summary_data.total_branch_count > 0:
        branch_coverage_pct = round(
            100 * summary_data.executed_branch_count
            / summary_data.total_branch_count,
            round_digit,
        )

    denominator = summary_data.total_line_count + summary_data.total_branch_count

    if denominator > 0:
        combined_coverage_pct = round(
            100 * (summary_data.executed_line_count + summary_data.executed_branch_count)
            / denominator,
            round_digit,
        )


    lines = []
    lines.append("═" * 26)
    lines.append("       TEST SUMMARY")
    lines.append("═" * 26)
    lines.append("")
    lines.append(f"Source files covered:       {summary_data.source_file_count}")
    lines.append(f"Test files run:             {summary_data.test_file_count}")
    lines.append("")

    lines.append("Test file outcomes:")
    lines.append(f"    Clean:                  {summary_data.passed_test_file_count}")
    lines.append(f"    Failed:                 {summary_data.failed_test_file_count}")
    lines.append(f"    Errors:                 {summary_data.error_test_file_count}")
    lines.append(f"    Skipped:                {summary_data.skipped_test_file_count}")
    lines.append(f"    XFailed:                {summary_data.xfailed_test_file_count}")
    lines.append(f"    XPassed:                {summary_data.xpassed_test_file_count}")
    lines.append("")

    lines.append("Individual test_files:")
    lines.append(f"    Passed:                 {summary_data.passed_test_function_count}")
    lines.append(f"    Failed:                 {summary_data.failed_test_function_count}")
    lines.append(f"    Errors:                 {summary_data.error_test_function_count}")
    lines.append(f"    Skipped:                {summary_data.skipped_test_function_count}")
    lines.append(f"    XFailed:                {summary_data.xfailed_test_function_count}")
    lines.append(f"    XPassed:                {summary_data.xpassed_test_function_count}")
    lines.append("")

    if summary_data.problem_test_files:
        lines.append(
            f"Test files with problems "
            f"({len(summary_data.problem_test_files)}):"
        )

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
            f"Test files with zero executed test_files "
            f"({len(summary_data.unexecuted_test_files)}):"
        )
        for test_file_name in summary_data.unexecuted_test_files:
            lines.append(f"    {test_file_name}")

    lines.append("")
    lines.append("Coverage")
    lines.append(f"    Statements:      {statement_coverage_pct:.{round_digit}f}%")
    lines.append(f"    Branches:        {branch_coverage_pct:.{round_digit}f}%")
    lines.append(f"    Overall:         {combined_coverage_pct:.{round_digit}f}%")

    lines.append("")
    lines.append("Statement coverage (executed/statements) by source file:")
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
