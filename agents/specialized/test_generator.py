import textwrap
from typing import Dict, Any
from ..base import BaseAgent
from ...core.models import Capability

class TestGeneratorAgent(BaseAgent):
    async def initialize(self):
        await self.add_capability(Capability(
            name="generate_unit_tests",
            handler=self._generate_unit_tests
        ))
        
        await self.add_capability(Capability(
            name="generate_integration_tests",
            handler=self._generate_integration_tests
        ))

    async def _generate_unit_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        class_name = payload.get("class_name", "ExampleClass")
        methods = payload.get("methods", ["method1", "method2"])
        
        test_code = self._generate_pytest_unit_tests(class_name, methods)
        
        return {
            "code": test_code,
            "framework": "pytest",
            "type": "unit"
        }

    async def _generate_integration_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        api_endpoints = payload.get("endpoints", ["/api/users", "/api/posts"])
        
        test_code = self._generate_api_integration_tests(api_endpoints)
        
        return {
            "code": test_code,
            "framework": "pytest",
            "type": "integration"
        }

    def _generate_pytest_unit_tests(self, class_name: str, methods: list) -> str:
        test_methods = []
        for method in methods:
            test_methods.append(self._generate_unit_test_method(method))
        
        tests_str = "\n\n".join(test_methods)
        
        return textwrap.dedent(f'''
            import pytest
            from unittest.mock import Mock, patch
            from your_module import {class_name}
            
            class Test{class_name}:
                @pytest.fixture
                def instance(self):
                    return {class_name}()
            
            {tests_str}
        ''').strip()

    def _generate_unit_test_method(self, method_name: str) -> str:
        return textwrap.dedent(f'''
            def test_{method_name}_success(self, instance):
                # Arrange
                expected_result = "expected_value"
                
                # Act
                result = instance.{method_name}()
                
                # Assert
                assert result == expected_result
            
            def test_{method_name}_failure(self, instance):
                # Arrange
                with patch.object(instance, '{method_name}', side_effect=Exception("Test error")):
                    # Act & Assert
                    with pytest.raises(Exception):
                        instance.{method_name}()
        ''').strip()

    def _generate_api_integration_tests(self, endpoints: list) -> str:
        test_methods = []
        for endpoint in endpoints:
            test_methods.extend(self._generate_api_test_methods(endpoint))
        
        tests_str = "\n\n".join(test_methods)
        
        return textwrap.dedent(f'''
            import pytest
            import httpx
            from fastapi.testclient import TestClient
            from your_app import app
            
            @pytest.fixture
            def client():
                return TestClient(app)
            
            {tests_str}
        ''').strip()

    def _generate_api_test_methods(self, endpoint: str) -> list:
        clean_name = endpoint.replace("/", "_").replace("-", "_").strip("_")
        
        return [
            textwrap.dedent(f'''
                def test_{clean_name}_get_success(self, client):
                    response = client.get("{endpoint}")
                    assert response.status_code == 200
                    assert response.json() is not None
            ''').strip(),
            
            textwrap.dedent(f'''
                def test_{clean_name}_post_success(self, client):
                    test_data = {{"name": "Test", "description": "Test description"}}
                    response = client.post("{endpoint}", json=test_data)
                    assert response.status_code in [200, 201]
                    assert response.json() is not None
            ''').strip(),
            
            textwrap.dedent(f'''
                def test_{clean_name}_not_found(self, client):
                    response = client.get("{endpoint}/999999")
                    assert response.status_code == 404
            ''').strip()
        ]