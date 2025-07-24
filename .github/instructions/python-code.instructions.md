---
applyTo: ["lib/**/*.py", "bin/**/*.py", "tests/**/*.py"]
---

# Python Code Development Instructions

## Code Style & Formatting

### Type Hints
```python
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

# Always use type hints for function signatures
def process_config(config: Dict[str, Any], output_path: Path) -> Optional[bool]:
    """Process configuration with proper typing"""
    pass

# Use generics for collections
def process_items(items: List[str]) -> Dict[str, int]:
    """Return mapping of items to their lengths"""
    return {item: len(item) for item in items}
```

### Pydantic Model Patterns
```python
from pydantic import BaseModel, Field, validator
from enum import Enum

class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class ConfigModel(BaseModel):
    """Configuration model with validation"""
    name: str = Field(..., min_length=1, description="Configuration name")
    status: StatusEnum = Field(default=StatusEnum.ACTIVE)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('name')
    def name_must_not_contain_spaces(cls, v):
        if ' ' in v:
            raise ValueError('Name cannot contain spaces')
        return v.lower()
    
    class Config:
        use_enum_values = True
        validate_assignment = True
```

### Error Handling Patterns
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CustomError(Exception):
    """Domain-specific error with context"""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}

async def robust_api_call(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Make API call with proper error handling"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"API call failed: {e}", extra={"url": url})
        raise CustomError(f"Failed to fetch data from {url}", {"original_error": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in API call")
        raise CustomError("Unexpected error occurred", {"original_error": str(e)})
```

### Async/Await Best Practices
```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource():
    """Async context manager for resource cleanup"""
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        await cleanup_resource(resource)

async def concurrent_operations(items: List[str]) -> List[Dict[str, Any]]:
    """Process items concurrently with controlled concurrency"""
    semaphore = asyncio.Semaphore(5)  # Limit concurrent operations
    
    async def process_item(item: str) -> Dict[str, Any]:
        async with semaphore:
            return await expensive_operation(item)
    
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Logging Standards
```python
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

def process_vm_operation(vm_id: str, operation: str) -> bool:
    """Process VM operation with structured logging"""
    logger.info("Starting VM operation", vm_id=vm_id, operation=operation)
    
    try:
        result = perform_operation(vm_id, operation)
        logger.info("VM operation completed", vm_id=vm_id, operation=operation, success=True)
        return result
    except Exception as e:
        logger.error("VM operation failed", 
                    vm_id=vm_id, 
                    operation=operation, 
                    error=str(e),
                    exc_info=True)
        raise
```

### Configuration Management
```python
from pathlib import Path
import json
from typing import TypeVar, Type

T = TypeVar('T', bound=BaseModel)

class ConfigManager:
    """Type-safe configuration management"""
    
    @staticmethod
    def load_config(config_path: Path, model_class: Type[T]) -> T:
        """Load and validate configuration"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path) as f:
                data = json.load(f)
            return model_class(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    @staticmethod
    def save_config(config: BaseModel, config_path: Path) -> None:
        """Save configuration with backup"""
        backup_path = config_path.with_suffix('.bak')
        
        # Create backup if original exists
        if config_path.exists():
            backup_path.write_text(config_path.read_text())
        
        # Write new configuration
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(config.json(indent=2))
```

### Testing Patterns
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

@pytest.fixture
def mock_config():
    """Provide mock configuration for tests"""
    return ConfigModel(name="test", status=StatusEnum.ACTIVE)

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operations with proper mocking"""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.json = AsyncMock(return_value={"status": "success"})
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await robust_api_call("http://example.com")
        assert result["status"] == "success"

@pytest.mark.parametrize("input_value,expected", [
    ("valid_name", "valid_name"),
    ("UPPER_NAME", "upper_name"),
])
def test_name_validation(input_value, expected):
    """Test configuration validation"""
    config = ConfigModel(name=input_value)
    assert config.name == expected

def test_error_with_context():
    """Test custom error handling"""
    try:
        raise CustomError("Test error", {"key": "value"})
    except CustomError as e:
        assert e.context["key"] == "value"
```

### Code Organization
```python
# Module structure for lib/ files
"""
Module docstring explaining purpose and main classes/functions.

Example:
    from lib.module_name import MainClass
    
    instance = MainClass(config)
    result = instance.process()
"""

from __future__ import annotations  # For forward references

# Standard library imports
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Third-party imports
import aiohttp
from pydantic import BaseModel

# Local imports
from .base_classes import BasePlugin
from .exceptions import CustomError

__all__ = ['MainClass', 'helper_function']  # Explicit exports

class MainClass:
    """Main class with clear responsibilities"""
    
    def __init__(self, config: ConfigModel) -> None:
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    def status(self) -> str:
        """Property with type hint and docstring"""
        return self._status
    
    async def main_operation(self) -> Dict[str, Any]:
        """Primary operation with async support"""
        self._logger.info("Starting main operation")
        # Implementation here
        return {"success": True}
```

### Performance Considerations
```python
from functools import lru_cache, wraps
import asyncio
from typing import Callable, Any

def async_lru_cache(maxsize: int = 128):
    """LRU cache decorator for async functions"""
    def decorator(func: Callable) -> Callable:
        func = lru_cache(maxsize=maxsize)(func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper.cache_info = func.cache_info
        wrapper.cache_clear = func.cache_clear
        return wrapper
    return decorator

# Memory-efficient processing
async def process_large_dataset(data_source: AsyncIterable) -> None:
    """Process data in chunks to manage memory"""
    batch_size = 100
    batch = []
    
    async for item in data_source:
        batch.append(item)
        if len(batch) >= batch_size:
            await process_batch(batch)
            batch.clear()
    
    # Process remaining items
    if batch:
        await process_batch(batch)
```

## Common Anti-patterns to Avoid

1. **Bare except clauses**: Always specify exception types
2. **Mutable default arguments**: Use `None` and create new objects inside function
3. **Blocking calls in async functions**: Use async alternatives
4. **Hardcoded strings**: Use constants or configuration
5. **Deep nesting**: Extract functions for better readability
6. **Missing type hints**: Always provide type information
7. **Inconsistent naming**: Follow snake_case for functions/variables, PascalCase for classes