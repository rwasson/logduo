"""
aggregate_summary_data_builder.py

Last edited: 2026-07-14
"""

from pathlib import Path

from developer_resources.pytest_harness.classes import (
    AggregateTestSummary,
    CombinedCoverageResult,
    ProblemTestFileRecord,
    PytestTestFileRecord,
)


# --- _build_aggregate_summary_data() -----------------------------------
def _build_aggregate_summary_data(
    *,
    pytest_test_file_records: list[PytestTestFileRecord],
    combined_coverage_result: CombinedCoverageResult,
    debug_print: bool,
) -> AggregateTestSummary:
    """
    Build aggregate test and official combined coverage summary data.
    """

    test_file_count = len(pytest_test_file_records)

    passed_test_function_count = 0
    failed_test_function_count = 0
    error_test_function_count = 0
    skipped_test_function_count = 0
    xfailed_test_function_count = 0
    xpassed_test_function_count = 0

    passed_test_file_count = 0
    failed_test_file_count = 0
    error_test_file_count = 0
    skipped_test_file_count = 0
    xfailed_test_file_count = 0
    xpassed_test_file_count = 0

    problem_test_files: list[ProblemTestFileRecord] = []
    unexecuted_test_files: list[str] = []

    for test_file_record in pytest_test_file_records:
        passed_test_function_count += (
            test_file_record.passed_test_function_count
        )
        failed_test_function_count += (
            test_file_record.failed_test_function_count
        )
        error_test_function_count += (
            test_file_record.error_test_function_count
        )
        skipped_test_function_count += (
            test_file_record.skipped_test_function_count
        )
        xfailed_test_function_count += (
            test_file_record.xfailed_test_function_count
        )
        xpassed_test_function_count += (
            test_file_record.xpassed_test_function_count
        )

        if test_file_record.total_test_function_count == 0:
            unexecuted_test_files.append(
                Path(test_file_record.test_file_path).name
            )

        problem_record = ProblemTestFileRecord(
            test_file_name=Path(test_file_record.test_file_path).name,
            failed_test_function_names=(
                test_file_record.failed_test_function_names
            ),
            error_test_function_names=(
                test_file_record.error_test_function_names
            ),
            skipped_test_function_names=(
                test_file_record.skipped_test_function_names
            ),
            xfailed_test_function_names=(
                test_file_record.xfailed_test_function_names
            ),
            xpassed_test_function_names=(
                test_file_record.xpassed_test_function_names
            ),
        )

        if problem_record.has_failures:
            failed_test_file_count += 1
        if problem_record.has_errors:
            error_test_file_count += 1
        if problem_record.has_skips:
            skipped_test_file_count += 1
        if problem_record.has_xfails:
            xfailed_test_file_count += 1
        if problem_record.has_xpasses:
            xpassed_test_file_count += 1

        if problem_record.has_problems:
            problem_test_files.append(problem_record)
        else:
            passed_test_file_count += 1

    source_file_coverage_records = sorted(
        combined_coverage_result.source_file_coverage_records.values(),
        key=lambda record: record.statement_coverage_pct,
    )

    executed_line_count = combined_coverage_result.executed_line_count
    total_line_count = combined_coverage_result.total_line_count
    executed_branch_count = combined_coverage_result.executed_branch_count
    total_branch_count = combined_coverage_result.total_branch_count

    statement_coverage_pct = combined_coverage_result.statement_coverage_pct
    branch_coverage_pct = combined_coverage_result.branch_coverage_pct
    total_coverage_pct = combined_coverage_result.total_coverage_pct


    if debug_print:
        print("Official combined Coverage.py counts of: executed / total")
        print(
            f"statements: {executed_line_count} / "
            f"{total_line_count}"
        )
        print(
            f"branches:   {executed_branch_count} / "
            f"{total_branch_count}\n"
        )

    return AggregateTestSummary(
        source_file_count=len(source_file_coverage_records),
        test_file_count=test_file_count,
        passed_test_file_count=passed_test_file_count,
        failed_test_file_count=failed_test_file_count,
        error_test_file_count=error_test_file_count,
        skipped_test_file_count=skipped_test_file_count,
        xfailed_test_file_count=xfailed_test_file_count,
        xpassed_test_file_count=xpassed_test_file_count,
        passed_test_function_count=passed_test_function_count,
        failed_test_function_count=failed_test_function_count,
        error_test_function_count=error_test_function_count,
        skipped_test_function_count=skipped_test_function_count,
        xfailed_test_function_count=xfailed_test_function_count,
        xpassed_test_function_count=xpassed_test_function_count,
        executed_line_count=executed_line_count,
        total_line_count=total_line_count,
        executed_branch_count=executed_branch_count,
        total_branch_count=total_branch_count,

        statement_coverage_pct=statement_coverage_pct,
        branch_coverage_pct=branch_coverage_pct,
        total_coverage_pct=total_coverage_pct,

        problem_test_files=problem_test_files,
        unexecuted_test_files=unexecuted_test_files,
        source_file_coverage_records=source_file_coverage_records,
    )

