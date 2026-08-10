Logduo 0.2.0 2026-08-09

This release focuses on configuration behavior, per-message formatting, and documentation/validation improvements.

* Added left_indent as a per-message option for log(), standard logging levels, and Rich Text.
    * Applies consistently to wrapped and multiline text.
    * Works with no_prefix, console_style, and log_wrap_width.
* log.configure() now accepts explicit None values to reset individual settings to their Logduo defaults, making it easier for packages using Logduo to override [tool.logduo] settings programmatically.
* Preserved user-supplied leading, trailing, and interior newlines in multiline messages.
* Clarified rendering behavior for strings, ordinary Python objects, Rich Text, and other Rich renderables.
* Expanded bundled examples, especially console_rendering.py, to demonstrate wrapping, indentation, Rich output, Python objects, tables, and placeholder behavior.
* Improved export_logduo_docs() argument handling and documentation.
* Expanded integration tests for logging-level options and message rendering.
* Updated validation scripts and GitHub Actions coverage, including Python 3.13 and 3.14 across macOS, Windows, and Ubuntu.
* Various validation, typing, documentation, and cleanup fixes.