"""Tests for chat module - code validation and WebSocket."""

import pytest

from app.chat import validate_code, extract_python_code, _is_valid_uuid


class TestCodeValidation:
    """Tests for code validation against whitelist."""

    def test_valid_simple_code(self):
        """Should accept simple pandas code."""
        code = """
import pandas as pd
media = df['Close'].mean()
print(f"Média: {media}")
"""
        is_valid, error = validate_code(code)
        assert is_valid is True
        assert error == ""

    def test_valid_numpy_code(self):
        """Should accept numpy code."""
        code = """
import numpy as np
arr = np.array([1, 2, 3])
print(arr.mean())
"""
        is_valid, error = validate_code(code)
        assert is_valid is True

    def test_valid_math_code(self):
        """Should accept math/statistics code."""
        code = """
import math
import statistics
data = [1, 2, 3, 4, 5]
print(math.sqrt(statistics.mean(data)))
"""
        is_valid, error = validate_code(code)
        assert is_valid is True

    def test_rejects_os_module(self):
        """Should reject os module usage."""
        code = """
import os
os.system('ls')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False
        assert "não permitido" in error.lower() or "os" in error.lower()

    def test_rejects_sys_module(self):
        """Should reject sys module usage."""
        code = """
import sys
print(sys.path)
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_subprocess(self):
        """Should reject subprocess module."""
        code = """
import subprocess
subprocess.run(['ls'])
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_eval(self):
        """Should reject eval() calls."""
        code = """
result = eval("1 + 1")
print(result)
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_exec(self):
        """Should reject exec() calls."""
        code = """
exec("print('hello')")
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_open(self):
        """Should reject file open() calls."""
        code = """
with open('/etc/passwd') as f:
    print(f.read())
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_dunder_import(self):
        """Should reject __import__ calls."""
        code = """
os = __import__('os')
os.system('ls')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_requests(self):
        """Should reject requests module."""
        code = """
import requests
requests.get('http://evil.com')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_urllib(self):
        """Should reject urllib module."""
        code = """
import urllib
urllib.request.urlopen('http://evil.com')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_builtins_access(self):
        """Should reject __builtins__ access."""
        code = """
__builtins__['open']('/etc/passwd')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_globals(self):
        """Should reject globals() access."""
        code = """
g = globals()
print(g)
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_getattr(self):
        """Should reject getattr() calls."""
        code = """
import pandas
getattr(pandas, '__builtins__')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_importlib(self):
        """Should reject importlib module."""
        code = """
import importlib
os = importlib.import_module('os')
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_compile(self):
        """Should reject compile() calls."""
        code = """
code = compile('print(1)', '<string>', 'exec')
exec(code)
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_class_dunder(self):
        """Should reject __class__ access."""
        code = """
''.__class__.__mro__[1].__subclasses__()
"""
        is_valid, error = validate_code(code)
        assert is_valid is False

    def test_rejects_too_long_code(self):
        """Should reject code that exceeds max length."""
        # Generate code longer than chat_max_code_length (5000 chars default)
        code = "x = 1\n" * 2000
        is_valid, error = validate_code(code)
        assert is_valid is False
        assert "too long" in error.lower() or "muito" in error.lower()


class TestCodeExtraction:
    """Tests for Python code block extraction."""

    def test_extracts_single_block(self):
        """Should extract single code block."""
        text = """
Vou calcular a média:

```python
import pandas as pd
media = df['Close'].mean()
print(media)
```

Isso mostra a média.
"""
        blocks = extract_python_code(text)
        assert len(blocks) == 1
        assert "import pandas" in blocks[0]

    def test_extracts_multiple_blocks(self):
        """Should extract multiple code blocks."""
        text = """
Primeiro:
```python
x = 1
```

Segundo:
```python
y = 2
```
"""
        blocks = extract_python_code(text)
        assert len(blocks) == 2

    def test_returns_empty_for_no_blocks(self):
        """Should return empty list when no blocks."""
        text = "Não há código aqui."
        blocks = extract_python_code(text)
        assert len(blocks) == 0

    def test_ignores_other_languages(self):
        """Should ignore non-Python code blocks."""
        text = """
```javascript
console.log('hello');
```

```python
print('hello')
```
"""
        blocks = extract_python_code(text)
        assert len(blocks) == 1
        assert "print" in blocks[0]


class TestUUIDValidation:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Should accept valid UUID."""
        assert _is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self):
        """Should accept uppercase UUID."""
        assert _is_valid_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_invalid_uuid_short(self):
        """Should reject short string."""
        assert _is_valid_uuid("550e8400-e29b-41d4") is False

    def test_invalid_uuid_format(self):
        """Should reject invalid format."""
        assert _is_valid_uuid("not-a-uuid-string") is False

    def test_invalid_uuid_empty(self):
        """Should reject empty string."""
        assert _is_valid_uuid("") is False

    def test_invalid_uuid_none(self):
        """Should handle None gracefully."""
        # This tests the ValueError/AttributeError exception handling
        assert _is_valid_uuid(None) is False  # type: ignore


class TestMessageSizeLimit:
    """Tests for message size validation."""

    def test_message_size_constant_exists(self):
        """MAX_MESSAGE_SIZE should be defined."""
        from app.chat import MAX_MESSAGE_SIZE
        assert MAX_MESSAGE_SIZE > 0
        assert MAX_MESSAGE_SIZE == 10 * 1024  # 10KB
