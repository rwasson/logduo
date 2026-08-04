LOGDUO MINOR UPDATE CHECKLIST (GitHub only)
===========================================
STAMP=$(date +%Y-%m-%d_%H-%M)

git status --short --untracked-files=all
git add .
git diff --cached --stat
git commit -m "Update $STAMP"
git push origin main
git status



LOGDUO RELEASE CHECKLIST
========================
1. Local computer checks:

A. Local validation (in PyCharm Project window)
-----------------------------------------------
Run:

    example_scripts_runner.py
    linter_runner.py
    pytest_harness_runner.py

Confirm:

- all tests pass
- Ruff, mypy, and Vulture pass
- console and log output look correct
- README and exported examples are current


B. Update package version (in pyproject.toml)
---------------------------------------------
Edit pyproject.toml:

    version = "X.Y.Z"

PyPI versions cannot be replaced after publication.




II.  GitHub updates (in Pycharm's Terminal)
---------------------------------------------

A. Confirm project directory:
----------------------------
    pwd

Expected:

    /Users/renyawasson/Local/PycharmProjects_local/logduo_project


B. Read and save the version from pyproject.toml:
-------------------------------------------------

    VERSION=$(python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')

Confirm:

    echo "$VERSION"


C. Review changed files:
------------------------

    git status --short --untracked-files=all

This only displays changes. It does not alter anything.


D. Stage all changes (does not change GitHub yet):
--------------------------------------------------

    git add .

This prepares modified, new, and deleted files for the next commit.


E. Review staged changes:
-------------------------

    git diff --cached --stat
    git status --short


F. Commit and push:
-------------------

    git commit -m "Release $VERSION"
    git push origin main


G. Confirm local and GitHub branches match:
-------------------------------------------
    git status

Expected:

    On branch main
    Your branch is up to date with 'origin/main'.
    nothing to commit, working tree clean


H. Verify the version stored in GitHub's pyproject.toml:
--------------------------------------------------------

    git fetch origin

    git show origin/main:pyproject.toml |python -c 'import sys, tomllib; print(tomllib.loads(sys.stdin.read())["project"]["version"])'

Expected:

    X.Y.Z


I. Create and push the Git tag
------------------------------

1. Create tag name from the package version:

    TAG="v$VERSION"

2. Confirm the intended tag:

    echo "$TAG"

3. Stop if the tag already exists:

    if git rev-parse "$TAG" >/dev/null 2>&1; then
        echo "Tag $TAG already exists."
        exit 1
    fi

4. Create and push the tag (if step 3 returns silently):

    git tag "$TAG"
    git push origin "$TAG"


J. Confirm GitHub Actions
--------------------------

Confirm all required jobs pass on:

- macOS
- Windows
- Ubuntu

Do not publish to PyPI until all required GitHub Actions jobs pass.


K. If GitHub Actions fails before PyPI publication
--------------------------------------------------
1. Correct the source files, tests, or workflow configuration locally.

2. Stage, commit, and push all corrections:

    git status --short --untracked-files=all
    git add .
    git diff --cached --stat
    git commit -m "Fix release workflow for $VERSION"
    git push origin main

3. Check whether the release tag already exists:

    git tag --list "$TAG"
    git ls-remote --tags origin "refs/tags/$TAG"

4. If the tag does not exist, create and push it:

    git tag "$TAG"
    git push origin "$TAG"

5. If the tag already exists and this version has not been published to PyPI,
   delete and recreate the tag so it points to the corrected commit:

    git tag -d "$TAG"
    git push origin --delete "$TAG"
    git tag "$TAG"
    git push origin "$TAG"

6. Confirm the tag points to the current corrected commit:

    git rev-parse HEAD
    git rev-parse "$TAG"

   The two commit hashes should match.

7. Confirm GitHub Actions passes before creating or publishing the GitHub


Release and before proceeding to PyPI.
If a GitHub Release was already created for the old tag, delete that draft or
release and create it again after the corrected tag has been pushed.

Do not reuse or move a tag after that version has been published to PyPI.
After PyPI publication, corrections require a new package version.

  

L. Create the GitHub Release
----------------------------
Pushing the tag does not necessarily create a GitHub Release.

On GitHub:

1. Open the Logduo repository.
2. Open Releases.
3. Select Draft a new release.
4. Choose the existing tag vX.Y.Z.
5. Use title:

       Logduo vX.Y.Z

6. Add release notes or generate them.
7. Make sure it is not marked as a prerelease.
8. Mark it as the latest release.
9. Publish the release.

This is the step that updates the GitHub Releases panel from v0.1.4 to v0.1.5.




III. PyPI release
=================

A. Build the distributions locally
----------------------------------

1. Confirm you are in the Logduo project root:

    pwd
    test -f pyproject.toml && echo "Project root confirmed"

Expected path:

    /Users/renyawasson/Local/PycharmProjects_local/logduo_project

Expected confirmation:

    Project root confirmed

2. Read and confirm the package version:

    VERSION=$(python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
    echo "$VERSION"

Expected:

    X.Y.Z


3. Remove files from previous builds:

    rm -rf build dist

    find . -maxdepth 2 -type d -name "*.egg-info" -exec rm -rf {} +

This removes:

- the previous build directory
- the previous dist directory
- generated package metadata directories

It does not remove source files.


4. Build the wheel and source distribution:

    python -m build

This should create:

    dist/logduo-X.Y.Z-py3-none-any.whl
    dist/logduo-X.Y.Z.tar.gz


5. Confirm the expected files were created:

    ls -la dist

Verify that both filenames contain the current version.


6. Validate the distribution metadata:

    python -m twine check --strict dist/*

Expected result for both files:

    PASSED


7. List the contents of the wheel:

    python -m zipfile -l "dist/logduo-$VERSION-py3-none-any.whl"

Confirm the wheel contains:

- the Logduo package modules
- `py.typed`
- bundled `README.txt`
- bundled example scripts
- required package-data files
- the `logduo-X.Y.Z.dist-info` metadata directory

Do not expect developer-only files such as tests, validation runners,
GitHub workflows, or local logs to appear in the wheel.


8. Optionally list the source distribution:

    tar -tzf "dist/logduo-$VERSION.tar.gz"

The source distribution normally contains additional source-project files
needed to build the package. Its contents do not need to match the wheel
exactly.


9. Verify the version recorded inside the wheel:

    rm -rf /tmp/logduo_wheel_check

    python -m zipfile -e \
        "dist/logduo-$VERSION-py3-none-any.whl" \
        /tmp/logduo_wheel_check

    grep '^Version:' \
        "/tmp/logduo_wheel_check/logduo-$VERSION.dist-info/METADATA"

Expected:

    Version: X.Y.Z


B. Test the locally built wheel
-------------------------------

Use a clean temporary project or virtual environment so the test cannot
accidentally import Logduo from the development source directory.


1. Change to the temporary project:

    cd /path/to/temp_project

Confirm:

    pwd


2. Activate the temporary project's virtual environment:

    source .venv/bin/activate

Confirm which Python is active:

    which python
    python --version


3. Remove any previously installed Logduo version:

    python -m pip uninstall -y logduo


4. Confirm Logduo is no longer installed:

    python -m pip show logduo

Expected:

    WARNING: Package(s) not found: logduo


5. Install the exact local wheel:

    VERSION=$(python -c 'import tomllib; print(tomllib.load(open("/Users/renyawasson/Local/PycharmProjects_local/logduo_project/pyproject.toml", "rb"))["project"]["version"])')
    python -m pip install "/Users/renyawasson/Local/PycharmProjects_local/logduo_project/dist/logduo-$VERSION-py3-none-any.whl"
    
Important:

- `VERSION` must be set in this terminal session.
- If this is a newly opened terminal, set it again or type the exact filename.
- Do not place quotation marks in the middle of the path.
- Using the exact wheel filename is safer than using `*.whl`.


6. Confirm the installed package and version:

    python -m pip show logduo

Then:

    python -c 'import importlib.metadata; print(importlib.metadata.version("logduo"))'

Expected:

    X.Y.Z


7. Confirm the package imports from the virtual environment:

    python -c 'import logduo; print(logduo.__file__)'

The displayed path should point into the temporary virtual environment,
not into `logduo_project/src`.


8. Run a basic logging test:

    python - <<'PY'
    from logduo import log

    log("local wheel test")
    log.close()
    PY

Confirm:

- console output appears
- a Logduo output directory is created
- the main log file is created
- the log file contains the test message
- the footer is written correctly


9. Test documentation export:

    python - <<'PY'
    from pathlib import Path
    from logduo import log

    export_dir = Path.cwd() / "logduo_docs_test"
    log.export_logduo_docs(export_dir)

    print(export_dir)
    for path in sorted(export_dir.rglob("*")):
        if path.is_file():
            print(path.relative_to(export_dir))
    PY

Confirm that the exported files include:

    README.txt
    examples/first_script.py
    examples/console_rendering.py
    examples/data_analysis.py
    examples/math_report_notation.py
    examples/script_parent.py
    examples/script_child.py


10. Confirm the installed package does not rely on development-project files.

The basic logging and documentation-export tests should work while the
current directory is the temporary project, with no dependency on files
inside the Logduo development repository.


C. Upload the distributions to PyPI
-----------------------------------

Only continue after:

- local validation passes
- GitHub Actions passes
- the GitHub release is published
- the local wheel test passes
- `twine check --strict` passes


1. Return to the Logduo project root:

    cd /Users/renyawasson/Local/PycharmProjects_local/logduo_project

Confirm:

    pwd


2. Confirm the distribution files one final time:

    ls -la dist

Expected:

    logduo-X.Y.Z-py3-none-any.whl
    logduo-X.Y.Z.tar.gz


3. Confirm no old-version distributions are mixed into `dist`:

    find dist -maxdepth 1 -type f -print

Only the two current-version files should be present.


4. Upload both distributions:

    python -m twine upload dist/*

When prompted, use:

    username: __token__
    password: Logduo's PyPI API token

The token will not be displayed while it is typed or pasted.


5. Wait for Twine to report successful uploads.

Expected messages should indicate that both files were uploaded:

    logduo-X.Y.Z-py3-none-any.whl
    logduo-X.Y.Z.tar.gz

PyPI does not allow an uploaded version file to be replaced. If the upload
fails because that version already exists, increment the version, rebuild,
retest, and upload the new version.


6. Confirm the release on PyPI.

Check that:

- version `X.Y.Z` appears
- it is shown as the current release
- the README renders correctly
- the wheel is present
- the source distribution is present
- the Python requirement is correct
- dependencies are correct
- author and project metadata are correct
- the short project description is correct


D. Test the package published on PyPI
-------------------------------------

Use a clean environment. Do not reuse an environment that still contains
the locally installed wheel.


1. Create or use a separate clean temporary virtual environment:

    mkdir -p /tmp/logduo_pypi_test
    cd /tmp/logduo_pypi_test

    python3.13 -m venv .venv
    source .venv/bin/activate

    python -m pip install --upgrade pip


2. Install Logduo from PyPI:

    python -m pip install --upgrade logduo

To require the exact release version:

    python -m pip install "logduo==$VERSION"


3. Confirm the installed package:

    python -m pip show logduo

Then:

    python -c 'import importlib.metadata; print(importlib.metadata.version("logduo"))'

Expected:

    X.Y.Z


4. Confirm the package location:

    python -c 'import logduo; print(logduo.__file__)'

The path should point into the clean virtual environment.


5. Run a basic logging test:

    python - <<'PY'
    from logduo import log

    log("PyPI installation test")
    log.warning("warning test")
    log.close()
    PY

Confirm:

- import succeeds
- console output appears
- logging starts automatically
- the output directory is created
- `session.log` is created
- `config_table.txt` is created
- both messages appear in the log
- the footer reports generated files


6. Test the focused help documentation:

    python - <<'PY'
    from logduo import log, run

    help(log.configure)
    help(log.new_logger)
    help(run)
    PY

Confirm that the installed package contains the expected docstrings.


7. Test documentation export from the PyPI installation:

    python - <<'PY'
    from pathlib import Path
    from logduo import log

    export_dir = Path.cwd() / "logduo_docs"
    log.export_logduo_docs(export_dir)

    for path in sorted(export_dir.rglob("*")):
        if path.is_file():
            print(path.relative_to(export_dir))
    PY

Confirm that the README and all expected examples are exported.


8. Final confirmation

The release is complete when:

- GitHub shows the correct latest release
- GitHub Actions passes
- PyPI shows the correct version
- the wheel and source distribution are available
- installation from PyPI succeeds in a clean environment
- basic logging succeeds
- documentation export succeeds
- the installed package version is correct
