# CODING CONVENTIONS

These conventions are a concise, practical guide to writing Python code in this repository.
Follow them when creating or modifying files so code stays readable, testable, and maintainable.

Guiding Principles

- Prefer clear, deterministic logic over cleverness.
- Keep functions small and explicit in behavior.
- Avoid global state; prefer dependency injection or class-based organization.
- Use dataclasses for simple value objects; avoid them for behavior-heavy classes.
- Follow PEP 8 and use type annotations for public functions and methods.
- Format code with Black-style clarity and avoid implicit side effects.

Style specifics

- Line length: 88 characters (Black default). Shorter is fine for readability.
- Indentation: 4 spaces.
- Naming: snake_case for functions/variables, PascalCase for classes.
- Docstrings: use Google-style or simple single-line summary + short description for non-trivial functions.
- Exceptions: catch specific exceptions and avoid broad except: clauses.

Decorators & Meta-programming

- Use decorators only when they reduce boilerplate or enforce cross-cutting concerns
  (e.g., caching, retries, authorization). Avoid unnecessary metaprogramming.

Testing and Side Effects

- Keep functions pure where practical; side effects (I/O, DB, network) should be explicit and isolated.
- Write unit tests for business logic; use dependency injection to mock external systems.

Practical examples

- Small function with types and docstring:

```python
def add(a: int, b: int) -> int:
    """Return the sum of two integers.

    Args:
        a: first value
        b: second value

    Returns:
        The integer sum.
    """
    return a + b
```

Tooling

- Use `black` for formatting and `flake8` for linting. Use `isort` to sort imports consistently.
- Add pre-commit hooks (recommended) to enforce formatting on commit.

When in doubt

- Prefer the explicit and obvious solution. If a change is surprising, add a short comment explaining
  the rationale.

Acknowledgement

- These rules are not exhaustive; use judgement when edge cases arise. If you want a change to the
  conventions, open a short PR with the rationale.
