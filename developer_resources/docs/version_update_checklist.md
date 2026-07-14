LOGDUO UPDATE CHECKLIST
=======================

Use Parts 1–3 for each release.
Part 4 contains one-time setup and workflow-maintenance instructions.

Quick GitHub update
===================
1. Check what changed:
    git status --short --untracked-files=all
    git diff --stat

2. Stage all intended changes:
    git add .

3. Confirm what will be committed:
    git diff --cached --stat

   If the listed files look wrong, stop and inspect before committing.
   Optional detailed inspection:

    git diff --cached

   If this opens a long scrollable view, press q to exit.

4. Commit and push:
    git commit -m "Short description of update"
    git push origin main

5. Confirm clean status:
    git status


PART 1 — VERIFY CHANGES LOCALLY
===============================

1. Review the project:
   - intended code changes are complete
   - documentation changes are complete
   - temporary debugging code is removed
   - obsolete comments and TODO notes are removed
   - public names and configuration fields are consistent
   - README.md and exported README.txt agree where appropriate


2. Run the Logduo validation scripts. Run:
       example_scripts_runner.py
       export_logduo_docs_demo.py
       linter_check.py
       pytest_harness_runner.py

   Confirm:
       - all tests pass
       - all lint and type checks pass  (Ruff, mypy, Vulture)
       - console output looks correct
       - main logs look correct
       - extra logger files look correct
       - configuration artifacts look correct
       - nested scripts behave correctly
       - exported documentation is complete


3. Test interactive behavior
   In a Python or PyCharm interactive session:

       from logduo import log
       log("interactive test")
       log.warning("warning test")
       log.close()

   Test any other interactive behavior affected by the changes.


4. Update the version
   In pyproject.toml:
       version = "X.Y.Z"

   Confirm that this version has not already been published to PyPI.
   A published PyPI version cannot be replaced with different files.


5. After updating the version in pyproject.toml, in Terminal:

    rm -rf build dist
    find . -maxdepth 2 -type d -name "*.egg-info" -exec rm -rf {} +
    python -m build
    python -m twine check dist/*
    python -m zipfile -l dist/logduo-X.Y.Z-py3-none-any.whl

   - first two lines remove previous build directory, distribution files, stale metadata
   - third line created a source distribution (ends in .tar.gz) and a wheel (ends in .whl)
   - fourth line confirms each updated file PASSED (ensure before upload to PYPI)
   - fifth line prints the files in the new wheel. Should see:
       - Logduo package source
       - py.typed
       - bundled README.txt
       - bundled example scripts
       - other required package data
       - package metadata

6. Test the newly built wheel in a blank PyCharm project
   Create a new blank PyCharm project with a new virtual environment.
   Open its Terminal and install the wheel using its complete path:

       python -m pip install "/absolute/path/to/logduo_project/dist/logduo-X.Y.Z-py3-none-any.whl"

   Test:

       from logduo import log

       log("local wheel test")
       log.warning("warning test")
       log.close()

   Confirm:
       - Logduo imports normally
       - the correct version is installed
       - a basic logging session works
       - generated paths are correct
       - bundled documentation can be exported
       - no files from the Logduo development project are required


PART 2 — VERIFY ON GITHUB
=========================
IMPORTANT: AUTHORITATIVE COPY ON LOCAL DRIVE
--------------------------------------------
The local project on disk is always the authoritative copy:
    /Users/renyawasson/Local/PycharmProjects_local/logduo_project

Never allow GitHub to overwrite the local project.
Make changes locally, commit locally, and push to GitHub.
Do not edit files directly on GitHub. Browser edits create remote commits that
are not present locally and can cause branch conflicts.
Do not run the following unless intentionally choosing to merge GitHub changes
into the local project:
    git pull

If GitHub contains accidental browser edits and the local project is correct:
    cd /Users/renyawasson/Local/PycharmProjects_local/logduo_project
    git fetch origin
    git push --force-with-lease origin main

git fetch origin checks GitHub and updates Git's information about the remote.
It does not alter the local project files.
Use --force-with-lease only when deliberately replacing GitHub with the
authoritative local copy.

GitHub Actions checks the committed copy on temporary GitHub runners.
The current tests workflow does not modify or push changes to main.
-----------------------------

1. Run from the Logduo project directory in Terminal:
    git status
    git add .
    git diff --cached
    git commit -m "Release X.Y.Z"
    git push origin main
    git status

   Confirm after the final git status:
       - the working tree is clean
       - pyproject.toml contains the intended version
       - the commit tested by GitHub contains all release changes

   If git push origin main succeeds, continue normally.
   If git push origin main is rejected because GitHub contains commits that
   are not present locally:
       - stop
       - do not run git pull
       - determine whether someone intentionally changed GitHub
       - if the GitHub changes were accidental and the local project is
         definitely correct, use the recovery commands in the
         AUTHORITATIVE COPY section above

2. Confirm GitHub Actions starts. On GitHub:
   - open the Logduo repository
   - select Actions
   - open the workflow run for the new commit


3. Confirm the operating-system jobs pass

   The tests.yml workflow should create jobs for:

   - Ubuntu
   - Windows
   - macOS

   Confirm that every required job passes.
   Do not publish while a required GitHub Actions job is failing.
   Possible causes  of failures include:
   - an actual cross-platform bug
   - path handling
   - line-ending differences
   - terminal or ANSI behavior
   - dependency differences
   - an error in tests.yml



PART 3 — PUBLISH TO PYPI
========================

COMMANDS IN TERMINAL
---------------------
1. Rebuild and upload: Run only after local validation and GitHub Actions pass
Should see PASSED after third command.
For the fourth command, you will be asked to provide Logduo's token (saved in password manager).
Token will not be visbile after pasting.

    rm -rf dist
    python -m build
    python -m twine check dist/*
    python -m twine upload dist/*


2. Confirm the release on PyPI
   Open the Logduo project page on PyPI.
   Confirm:
       - the new version appears
       - the README renders correctly
       - the source distribution is present
       - the wheel is present
       - Python requirements and other metadata are correct


3. Test the published package
   In the blank PyCharm test project:
       - open the Packages window
       - update Logduo to the new version
       - close and reopen PyCharm if the new version does not appear immediately

   Alternatively, run:

       python -m pip install --upgrade logduo

   Confirm the installed version:

       python -m pip show logduo

   Test:

       from logduo import log

       log("published package test")
       log.warning("warning test")
       log.close()


4. Tag the release. Run in Terminal from the Logduo project:

       git tag vX.Y.Z
       git push origin vX.Y.Z

   Confirm that the tag appears on GitHub.




PART 4 — ONE-TIME SETUP AND WORKFLOW MAINTENANCE
================================================

A. GITHUB REPOSITORY SETUP
--------------------------

COMMANDS
--------

For a completely new repository:

    git remote add origin <repository-url>
    git push -u origin main


Confirm that the repository contains:

- pyproject.toml
- README.md
- LICENSE
- src/logduo/
- tests/
- developer_resources/
- .gitignore
- .github/workflows/tests.yml


B. GITHUB OPERATING-SYSTEM TESTING
----------------------------------

GitHub operating-system testing is controlled by:

    .github/workflows/tests.yml

It is not controlled by the PyPI upload commands.

The workflow needs a matrix containing:

    ubuntu-latest
    windows-latest
    macos-latest

Example matrix structure:

    strategy:
      fail-fast: false
      matrix:
        os:
          - ubuntu-latest
          - windows-latest
          - macos-latest

    runs-on: ${{ matrix.os }}


C. GITHUB TEST COMMANDS
-----------------------

The steps in tests.yml determine exactly what each GitHub runner executes.

The workflow should install Logduo and its test requirements before running
tests.

Example structure:

    - name: Install package and test dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -e ".[dev]"

    - name: Run tests
      run: pytest


Use the actual installation command supported by Logduo's pyproject.toml.

If Logduo does not define a test dependency group named test, replace:

    python -m pip install -e ".[test]"

with the actual commands needed to install Logduo and its test dependencies.


D. ADDING EXAMPLE SCRIPTS TO GITHUB TESTING
-------------------------------------------

GitHub does not run the examples unless tests.yml tells it to.

Since Logduo already has a validation runner, the simplest option may be to
run that rather than list every example separately:

    - name: Run example scripts
      run: python developer_resources/logduo_validation/example_scripts_runner.py

Only use this in GitHub Actions if the runner:

- works without PyCharm
- requires no manual input
- uses cross-platform paths
- returns a nonzero exit status when an example fails
- does not depend on files excluded from GitHub
- can safely create its output files on a temporary GitHub runner

The documentation-export validation can be added separately:

    - name: Test documentation export
      run: python developer_resources/logduo_validation/export_logduo_docs_demo.py

Ruff, mypy, and Vulture can either run through linter_check.py or through
separate workflow commands.

Example:

    - name: Run static checks
      run: python developer_resources/logduo_validation/linter_check.py


E. REVIEWING OR UPDATING tests.yml
----------------------------------

Before the next release, inspect:

    .github/workflows/tests.yml

Confirm that it matches:

- the Python versions Logduo supports
- Ubuntu, Windows, and macOS
- current dependency-installation commands
- current test locations
- current validation-script paths

After changing tests.yml:

1. Commit and push the change.
2. Open the Actions page on GitHub.
3. Confirm that all intended jobs appear.
4. Open each job and confirm the expected commands ran.
5. Correct tests.yml if a validation script was skipped.


F. INITIAL PYPI SETUP
---------------------

For a new package:

1. Create a PyPI account.
2. Enable two-factor authentication.
3. Confirm the project name is available.
4. Build the source distribution and wheel.
5. Run Twine check.
6. Upload the initial release with Twine.
7. Confirm the project page and metadata.
8. Install the published package in a clean environment.

Routine releases continue to use Part 3.


G. OPTIONAL FUTURE: AUTOMATED PYPI PUBLISHING
---------------------------------------------

Logduo currently uses manual Twine uploads.

Automated publishing is optional and is not required for GitHub
cross-platform testing.

If automated publishing is added later:

- configure PyPI Trusted Publishing
- create a separate GitHub publishing workflow
- allow the publishing workflow to run only for an intentional release event
- require successful tests before publication
- avoid storing a permanent PyPI password in the workflow

Keep automated publishing separate from tests.yml so an ordinary push cannot
accidentally publish a release.









