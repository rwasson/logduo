# Vendored pytest_harness

pytest_harness is bundled here only as a vendored development and validation tool.

Because pytest_harness itself depends on Logduo, Logduo does not declare it as a normal package 
dependency. This internal copy is intentionally frozen at the version adopted by this Logduo release 
and may differ from future standalone pytest_harness releases on PyPi.

It is not part of Logduo's public API.

- Edits should not be required in this directory. To run tests, right click on 

     `pytest_harness_runner.py'` in the `developer_resources\logduo_validation` directory.
- See docstring in pytest_harness.py for more details