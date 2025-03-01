# Python Code Conventions

This document outlines the conventions to be followed for all Python code in this project. Adhering to these conventions ensures that the codebase remains clean, maintainable, and consistent.

## General Guidelines

- **Idiomatic Python**: Write code that is idiomatic to Python, following the principles of the Zen of Python (PEP 20). This includes using list comprehensions, context managers, and other Pythonic constructs where appropriate.

- **Type Annotations**: All functions and methods should include type annotations for parameters and return types. This helps with code readability and can assist with static analysis tools.

- **Modern Python**: Use features from the latest stable version of Python that the project supports. This includes f-strings for formatting, the `pathlib` module for file paths, and other modern Python features.

- **Comments and Documentation**: 
  - Write clear and concise comments where necessary to explain complex logic.
  - Use docstrings for all public modules, classes, and functions. Follow the Google Python Style Guide for docstrings.
  - Keep comments up-to-date with code changes.

## Specific Conventions

- **Imports**: 
  - Group imports into three categories: standard library imports, third-party imports, and local application imports. Separate each group with a blank line.
  - Use absolute imports rather than relative imports.

- **Naming Conventions**:
  - Use `snake_case` for variable and function names.
  - Use `CamelCase` for class names.
  - Use `UPPER_SNAKE_CASE` for constants.

- **Error Handling**: 
  - Use exceptions to handle errors. Avoid using return codes or other non-exception-based error handling.
  - Catch specific exceptions rather than using a bare `except:` clause.

- **Testing**: 
  - Write unit tests for all new features and bug fixes.
  - Use a consistent testing framework across the project (e.g., `pytest`).
  - Ensure tests are isolated and do not depend on external state.

- **Code Style**: 
  - Follow PEP 8 for code style, with the exception of line length, which can be extended to 100 characters if necessary for readability.
  - Use a linter (e.g., `flake8`) and a formatter (e.g., `black`) to maintain code style consistency.

By following these conventions, we ensure that our codebase remains robust, readable, and easy to maintain. Any deviations from these guidelines should be discussed and documented.
