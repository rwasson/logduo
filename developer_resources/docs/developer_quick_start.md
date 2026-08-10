developer_quickstart.md

Last edited: 2026-08-10


=== Quick validation after any change ==========================================

Run:

- python -m developer_resources.validation.linter_runner 
- python -m developer_resources.validation.pytest_harness_runner
- python -m developer_resources.validation.example_script_runner

Checks:

- Ruff / import order
- mypy
- Vulture
- pytest suite
- bundled example scripts


=== Architecture review order ==================================================

1. Public API
   - logduo.py
   - __init__.py

2. Core state and constants
   - global_constants.py
   - runtime_classes.py

3. Configuration
   - session_config_spec.py
   - api_arg_resolver_helpers.py
   - configure_args_normalizer.py
   - session_config_resolver.py

4. Session startup / filesystem
   - start_session.py
   - initialize.py
   - path_finders.py
   - path_policy.py

5. Per-call handling
   - level_entry.py
   - level_call_args_resolver.py

6. Routing
   - dispatcher.py

7. Message formatting
   - message_prep.py
   - prefix_builder.py
   - wrap_text.py

8. Sinks
   - console.py
   - main_sink_log.py
   - user_sink_log.py
   - jsonl.py
   - created_file_record_builders.py
   - created_file_record_registration.py

9. Loguru integration
   - loguru_integration.py
   - new_loguru_sink.py

10. Artifacts
    - session_artifacts.py
    - config_table.py
    - export_logduo_docs.py

11. Shutdown / pruning
    - close_session.py
    - prune.py



=== Mental model ===============================================================

User API
→ configuration
→ SessionConfig
→ startup
→ level entry
→ call-arg resolution
→ dispatcher
→ EmitEvent
→ message preparation
→ sinks
→ shutdown


=== Core rules =================================================================

- SessionConfig is immutable after resolution.
- RuntimeRecord holds mutable session state.
- User inputs are validated early.
- _NOT_GIVEN should not survive resolver boundaries.
- Dispatcher routes; it does not render.
- Sinks render; they do not resolve configuration.
- Runtime stores canonical resolved paths.
- Output directories are created only when file output is needed.
- CreatedFileRecord tracks Logduo-managed files/artifacts.


=== When returning to the project =============================================

- Run validation first.
- Read files in the order above.
- Rebuild the architecture mentally before changing code.
