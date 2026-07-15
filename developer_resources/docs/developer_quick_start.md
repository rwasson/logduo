developer_quickstart.md

Last edited: 2026-07-14


=== Quick check that code works after any change ===============================

Run the validation scripts (or just right-click in Pycharm):
    python -m developer_resources.validation.linter_runner
    python -m developer_resources.validation.pytest_harness_runner
    python -m developer_resources.validation.example_script_runner
    python -m developer_resources.validation.export_logduo_docs_demo


These scripts quickly verify:
- source linting and import order
- likely dead or unreachable code
- type-checking
- pytest test suite behavior (over 500 tests)
- bundled example scripts
- local docs export behavior


=== Quick review of essential code =============================================

Read in order. Later files assume understanding of earlier files.

=== 1. PUBLIC API: logduo.py, init.py ==========================================

Focus:
- Public user-facing API
- log.configure()
- log.join()
- log.new_logger()
- log.new_level()
- log.close()
- Dynamic level methods

Goal:
Understand what users see and how the system is intended
to be used.


=== 2. GLOBAL CONTRACTS: global_constants.py, runtime_classes.py ===============

Focus:
- Shared constants
- MessageKind enum
- Session runtime state
- Created file tracking
- Core data structures

Goal:
Understand system-wide invariants and the data flowing
through the system.

=== 3. CONFIG SPECIFICATION: session_config_spec.py ============================

Focus:
- Allowed configuration fields
- Defaults
- Types
- Validation rules

Goal:
Understand what users are allowed to specify.


=== 4. CONFIG RESOLUTION  ======================================================

Files:
    api_arg_resolver_helpers.py,
    configure_args_normalizer.py,
    session_config_resolver.py

Focus:
- Resolve “auto” values
- Normalize user inputs
- Interactive defaults
- Path resolution
- Final SessionConfig creation

Goal:
Understand how raw user input becomes immutable session state.

=== 5. SESSION STARTUP =========================================================

Files:
start_session.py
initialize.py
path_finders.py
path_validators.py

Focus:
- Session creation
- Runtime initialization
- Directory creation
- Log file path selection
- Artifact setup

Goal:
Understand how a session becomes operational.


=== 6. LEVEL ENTRY: level_entry.py, level_call_args_resolver.py ================

Focus:
- Capture raw user calls
- Resolve per-call arguments
- Validate user input
- Eliminate _NOT_GIVEN

Goal:
All per-call behavior becomes concrete here.


=== 7. DISPATCHER: dispatcher.py ===============================================

Focus:
- Message classification
- MessageKind determination
- EmitEvent creation
- Sink routing

Goal:
Understand the central control point for all logging.


=== 8. MESSAGE PREPARATION =====================================================

Files:
message_prep.py
prefix_builder.py
wrap_lines.py

Focus:
- Message normalization
- Prefix generation
- Wrapping
- Layout preparation

Goal:
Understand how raw messages become display-ready text.


=== 9. SINK IMPLEMENTATIONS ====================================================

Files:
main_sink_log.py
user_sink_log.py
console.py
jsonl.py

Focus:
- Main log behavior
- User-created file loggers
- Console rendering
- JSONL event output

Goal:
Understand how the same EmitEvent is rendered differently
for each destination.


=== 10. LOGURU INTEGRATION: loguru_integration.py, new_loguru_sink.py ==========

Focus:
- External sink integration
- Loguru interoperability

Goal:
Understand advanced sink extension points.


=== 11. SESSION ARTIFACTS ======================================================

Files:
session_artifacts.py
text_table.py
build_dict_table.py
config_table.py
show_env_table.py
export_logduo_docs.py

Focus:
- Config reports
- Environment reports
- Session artifact generation

Goal:
Understand how Logduo records session metadata.


=== 12. SESSION FINALIZATION ===================================================

Files:
close_session.py
prune.py
created_file_record_builders.py
created_file_record_registration.py

Focus:
Execution order:
1. Finalize runtime
2. Write footers
3. Validate created files
4. Register artifacts
5. Prune old run directories
6. Present final summary

Goal:
Understand lifecycle shutdown and cleanup behavior.



=== MENTAL MODEL (FINAL STATE) =================================================

User API
↓
Configuration
↓
SessionConfig
↓
Session Startup
↓
Level Entry
↓
Call Argument Resolution
↓
Dispatcher
↓
EmitEvent
↓
Message Preparation
↓
Sinks
↓
Session Finalization


=== IMPORTANT RULES ============================================================

Configuration
* SessionConfig is immutable after resolution.
* RuntimeRecord is mutable session state.
* Interactive defaults are applied only during configuration.

Validation
* User validation happens early.
* Downstream code assumes validated inputs.
* _NOT_GIVEN does not survive resolvers.

Dispatcher
* Dispatcher classifies and routes.
* Dispatcher does not format output.
* Dispatcher does not perform presentation logic.

Sinks
* Sinks render.
* Sinks do not validate.
* Sinks do not resolve configuration.

Runtime
* Runtime is the single source of truth.
* CreatedFileRecord tracks all managed artifacts.
* Session state lives in RuntimeRecord.

Paths
* Path resolution occurs during startup.
* Sinks should not invent paths.
* Runtime contains canonical resolved paths.


=== HOW TO USE THIS ROADMAP ====================================================

1. Run the example scripts.
2. Read files in order.
3. Do not modify code during the first pass.
4. Rebuild the mental model before refactoring.

Goal:
Regain architectural context quickly without rediscovering
system behavior from scratch.
