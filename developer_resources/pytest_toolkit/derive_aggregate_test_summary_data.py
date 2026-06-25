"""
derive_aggregate_test_summary_data.py

Last edited: 2026-06-11
"""

from pathlib import Path

from developer_resources.pytest_toolkit.pytest_harness_classes import (
    SourceFileCoverageRecord,
    AggregateTestSummary,
    PytestTestFileRecord,
    ProblemTestFileRecord,
)


# --- _derive_aggregate_test_summary_data() -------------------------------------------
def _derive_aggregate_test_summary_data(
    *,
    pytest_test_file_records: list[PytestTestFileRecord],
    debug_print: bool,
) -> AggregateTestSummary:
    """
    Builds a AggregateTestSummary class instance
    USed by master test runner to generate summary text block
    """

    if debug_print:
        print("debug_print = True in pytest_harness_engine.py")

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


    # --- Aggregate coverage by source file ---
    merged_records: dict[str, SourceFileCoverageRecord] = {}

    for test_file_record in pytest_test_file_records:

        passed_test_function_count += test_file_record.passed_test_function_count
        failed_test_function_count += test_file_record.failed_test_function_count
        error_test_function_count += test_file_record.error_test_function_count
        skipped_test_function_count += test_file_record.skipped_test_function_count
        xfailed_test_function_count += test_file_record.xfailed_test_function_count
        xpassed_test_function_count += test_file_record.xpassed_test_function_count

        total_test_function_count = test_file_record.total_test_function_count

        if total_test_function_count == 0:
            unexecuted_test_files.append(
                Path(test_file_record.test_file_path).name
            )

        problem_record = ProblemTestFileRecord(
            test_file_name=Path(test_file_record.test_file_path).name,
            failed_test_function_names=test_file_record.failed_test_function_names,
            error_test_function_names=test_file_record.error_test_function_names,
            skipped_test_function_names=test_file_record.skipped_test_function_names,
            xfailed_test_function_names=test_file_record.xfailed_test_function_names,
            xpassed_test_function_names=test_file_record.xpassed_test_function_names,
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

        '''
        if test_file_record.failed_test_count == 0:
            passed_file_count += 1
        else:
            failed_file_count += 1
            problem_test_files.append(
                ProblemTestFileRecord(
                    test_file_name=Path(test_file_record.test_file_path).name,
                    failed_test_count=test_file_record.failed_test_count,
                    failed_test_names=test_file_record.failed_test_names,
                )
            )
        '''

        # --- Merge coverage records ---
        for source_file_path, source_file_coverage_record in (
            test_file_record.source_file_coverage_records.items()
        ):

            # --- START DEBUG: show covered lines for selected package files ---
            if debug_print:
                debug_files = {
                    "short_path.py",
                    "header_footer_formatters.py",
                    # "log_header_footer_builders.py",
                    # "runtime_classes.py",
                    # "path_finders.py",

                }
                source_file_name = Path(source_file_path).name
                total_number_statements = (len(source_file_coverage_record.executed_lines) +
                                          len(source_file_coverage_record.missing_lines))
                if source_file_name in debug_files:
                    print("")

                    print(f"TEST FILE      : {Path(test_file_record.test_file_path).name}")
                    print(f"TARGET FILE    : {source_file_name}")
                    print(f"EXECUTED       : {sorted(source_file_coverage_record.executed_lines)}")
                    print(f"# of EXECUTED  : {len(source_file_coverage_record.executed_lines)}")
                    print(f"# of STATEMENTS: {total_number_statements}")
            #  --- END DEBUG

            if source_file_path not in merged_records:
                merged_records[source_file_path] = (
                    SourceFileCoverageRecord(
                        source_file_path=source_file_coverage_record.source_file_path,
                        executed_lines=set(source_file_coverage_record.executed_lines),
                        missing_lines=set(source_file_coverage_record.missing_lines),
                        total_line_count=source_file_coverage_record.total_line_count,
                        branch_source=source_file_coverage_record.branch_source,
                        total_branch_pairs=source_file_coverage_record.total_branch_pairs,
                        executed_branch_pairs=source_file_coverage_record.executed_branch_pairs,
                    )
                )
                continue


            merged = merged_records[source_file_path]


            # --- Statement coverage ---
            merged.executed_lines |= source_file_coverage_record.executed_lines
            merged.missing_lines -= source_file_coverage_record.executed_lines


            # --- Branch coverage ---
            merged.executed_branch_pairs |= source_file_coverage_record.executed_branch_pairs

            # --- Safety checks ---
            if merged.branch_source != source_file_coverage_record.branch_source:
                print("*******************************************************")
                print(f"test_file_name = {Path(test_file_record.test_file_path).name}")
                print(f"source_file_name = {Path(source_file_path).name}")
                print("only in branch_source (not in source_file_coverage_record):")
                print(merged.branch_source - source_file_coverage_record.branch_source)
                print("only in source_file_coverage_record (not in branch_source):")
                print(source_file_coverage_record.branch_source - merged.branch_source)
                print("merged.branch_source:")
                print(merged.branch_source)
                print("source_file_coverage_record.branch_source:")
                print(source_file_coverage_record.branch_source)
                print("*******************************************************")
                print(" ")

            ''' 
            FUTURE: once resolve Python -C issue
            assert merged.total_line_count == source_file_coverage_record.total_line_count
            assert merged.branch_source == source_file_coverage_record.branch_source
            assert merged.total_branch_pairs == source_file_coverage_record.total_branch_pairs
            '''


    if debug_print:
        # --- Start Merged Debug ---
        print("")
        print("════════════════════")
        print("MERGED COVERAGE")
        print("════════════════════")
        debug_files = {
            "short_path.py",
            "header_footer_formatters.py",
            # "log_header_footer_builders.py",
            # "runtime_classes.py",
            # "path_finders.py",
        }

        for (source_file_path, source_file_coverage_record) in merged_records.items():
            source_file_name = Path(source_file_path).name
            if source_file_name not in debug_files:
                continue

            print("")
            print(f"PACKAGE   : {source_file_name}")
            print(f"EXECUTED  : {sorted(source_file_coverage_record.executed_lines)}")
            print(f"COUNT of EXECUTED: {len(source_file_coverage_record.executed_lines)}")
            # print(f"MISSING   : {sorted(source_file_coverage_record.missing_lines)}")

        # --- End Merged Debug ---

    # --- Final coverage totals ---
    total_line_count = 0
    executed_total_line_count = 0
    executed_branch_count = 0
    total_branch_count = 0

    for source_file_coverage_record in merged_records.values():
        total_line_count += source_file_coverage_record.total_line_count
        executed_total_line_count += source_file_coverage_record.executed_line_count
        total_branch_count += source_file_coverage_record.total_branch_count
        executed_branch_count += source_file_coverage_record.executed_branch_count

    source_file_coverage_records = sorted(
        merged_records.values(),
        key=lambda r: r.statement_coverage_pct,
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
        executed_line_count=executed_total_line_count,
        total_line_count=total_line_count,
        executed_branch_count=executed_branch_count,
        total_branch_count=total_branch_count,
        problem_test_files=problem_test_files,
        unexecuted_test_files=unexecuted_test_files,
        source_file_coverage_records=source_file_coverage_records,
    )

