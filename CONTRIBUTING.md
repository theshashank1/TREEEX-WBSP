# Contributing to TREEEX-WBSP

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to TREEEX-WBSP and its packages. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## 📚 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submission Guidelines](#submission-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-handle/TREEEX-WBSP.git
    cd TREEEX-WBSP
    ```
3.  **Set up the environment**:
    Follow the [Setup Guide](docs/SETUP.md) to install dependencies and configure your local environment.

## Development Workflow

1.  **Create a branch**: Always work on a new branch for your changes.
    ```bash
    git checkout -b feature/my-new-feature
    # or
    git checkout -b fix/issue-123
    ```

2.  **Make changes**: Write code that is clear, concise, and commented where necessary.

3.  **Run Tests**: Ensure your changes don't break existing functionality.
    ```bash
    python -m pytest tests/
    ```

## Code Style

We use `ruff` and `black` to ensure consistent code styling.

- **Formatting**:
  ```bash
  # Check formatting
  ruff check .

  # specific file
  ruff check server/api/messages.py
  ```

- **Naming Conventions**:
  - Variables/Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

## Testing

All new features and bug fixes must be accompanied by tests.

- We use **pytest** for testing.
- Place tests in the `tests/` directory.
- Follow the [Testing Guide](docs/TESTING.md) for more details on writing and running tests.

## Submission Guidelines

### Opening a Pull Request

1.  **Update Documentation**: If your change affects usage or configuration, update the relevant docs in `docs/`.
2.  **Update Changelog**: Add a note to `docs/CHANGELOG.md` under the `[Unreleased]` section.
3.  **Push to GitHub**:
    ```bash
    git push origin feature/my-new-feature
    ```
4.  **Create PR**: Open a Pull Request against the `main` branch.
    - Title: Clear and descriptive (e.g., "Add template message validation").
    - Description: Explain *what* changed and *why*. Link to meaningful issues (e.g., "Fixes #123").

### Code Review

- Wait for a maintainer to review your PR.
- Address any feedback constructively.
- Once approved, your PR will be merged!

---
**Happy Coding!** 🚀
