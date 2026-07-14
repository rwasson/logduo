pycharm_venv_management.txt

Practical workflow notes for:
    - PyCharm 2025.3.5 Community Edition
    - macOS
    - zsh (% prompt in Terminal)
    - one-venv-per-project workflow
    - pyproject.toml stores list of dependencies for every project

Example: project_root = /Users/<username>/PycharmProjects/test_project

Last edited: 2026-7-11


=== 1. Create a new venv =======================================================

A. New project
- Step 1: Within PyCharm in any project, from the top menu bar: File -> New Project
- Step 2: In the resulting "New Project" popup box:
    - Location: type desired location
        Example: `/Users/<username>/PycharmProjects/test_project`
- Optionally check box: 'Create Git Repository'
    - Select Interpreter type: Project venv
    - Select Python version from dropdown (Example: Python 3.13)
- Step 3: Click: Create
    - PyCharm will:
        - create the project folder
        - create the .venv folder
        - connect the interpreter automatically

B. Existing project WITH a .venv folder: Delete the old .venv folder.
    - In the PyCharm project file panel: right-click the .venv folder and select "delete"
    - Or in Terminal:
  
          % command to change directory to project root
          % rm -rf .venv

C. Existing project WITHOUT a .venv folder
- Step 1: Open the project in PyCharm.
    - In PyCharm, make sure that the project identified at top, is the desired project.
    - If not, click on the project drop-down menu and select desired project.
- Step 2: To open popup box 'Add Python Interpreter', click on:
    - PyCharm, Settings, PyCharm, Interpreter, Add Interpreter, Add Local Interpreter
- Step 3: Within the 'Add Python Interpreter' popup box, select:
    - Environment: choose 'Generate New'
    - Type: select 'Virtualenv' from dropdown menu
    - Base Python: Select desired Python from dropdown menu (example: Python 3.13)
    - Location: Type desired location. Example:  
  
          /Users/renyawasson/Local/PycharmProjects_local/logduo_project/.venv
  
    - Do NOT Check either of these options:
        - Inherit packages from base interpreter
        - Make available to all projects
        then click 'Ok' twice to exit (or your PyCharm version's confirmation steps) 
        should see .venv folder now in project's folder


=== 2. Update Python packaging tools ===========================================

In PyCharm Terminal:
    `% python -m pip install --upgrade pip setuptools wheel`


=== 3. Recommended for all projects ============================================

Store project dependencies in pyproject.toml located in project_root.
Example: `pyproject.toml`

    [project]
    name = "logduo"
    requires-python = ">=3.13"
    dependencies = ["loguru>=0.7,<0.8", "rich>=13,<16"]

    [project.optional-dependencies]
    dev = [
      "build",
      "pytest",
      "pytest-cov",
      "ruff",
      "mypy",
      "vulture",
    ]

=== 4. Install dependencies stored in pyproject.toml ===========================

In PyCharm Terminal:

    % pwd                               # display current directory
    % cd /absolute/path/to/project      # change to project directory if necessary
    % ls                                # list files, should see pyproject.toml

A. Standard project (e.g., data science project)

    % python -m pip install ".[dev]"     # installs project dependencies +
                                         # optional [dev] dependencies (if any)

B. Project developed as an editable Python package (e.g., logduo):
Changes to local source code immediately affect projects using that package.

    % python -m pip install -e ".[dev]"  # installs project dependencies +
                                         # optional [dev] dependencies (if any)


=== 5. Install a different local project as an editable package ================

In PyCharm Terminal:

    % python -m pip install -e /Users/renyawasson/Local/PycharmProjects_local/logduo_project


=== 6. Periodically update dependencies ========================================

Within version constraints in pyproject.toml:
In PyCharm Terminal:

    % python -m pip install --upgrade pip setuptools wheel
    % python -m pip install --upgrade ".[dev]"

If you later see a message like:

    [notice] To update, run: pip install --upgrade pip

then run again:

    % python -m pip install --upgrade pip setuptools wheel
