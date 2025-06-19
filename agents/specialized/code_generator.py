import textwrap
from typing import Dict, Any
from ..base import BaseAgent
from ...core.models import Capability

class CodeGeneratorAgent(BaseAgent):
    async def initialize(self):
        await self.add_capability(Capability(
            name="generate_api",
            handler=self._generate_api
        ))
        
        await self.add_capability(Capability(
            name="generate_model",
            handler=self._generate_model
        ))
        
        await self.add_capability(Capability(
            name="generate_service",
            handler=self._generate_service
        ))

    async def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        endpoint_name = payload.get("name", "example")
        method = payload.get("method", "GET").upper()
        
        if method == "GET":
            code = self._generate_get_endpoint(endpoint_name)
        elif method == "POST":
            code = self._generate_post_endpoint(endpoint_name)
        else:
            code = self._generate_generic_endpoint(endpoint_name, method)
        
        return {
            "code": code,
            "language": "python",
            "framework": "FastAPI"
        }

    async def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        model_name = payload.get("name", "ExampleModel")
        fields = payload.get("fields", [])
        
        code = self._generate_pydantic_model(model_name, fields)
        
        return {
            "code": code,
            "language": "python",
            "framework": "Pydantic"
        }

    async def _generate_service(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service_name = payload.get("name", "ExampleService")
        operations = payload.get("operations", [])
        
        code = self._generate_service_class(service_name, operations)
        
        return {
            "code": code,
            "language": "python"
        }

    def _generate_get_endpoint(self, name: str) -> str:
        return textwrap.dedent(f'''
            from fastapi import APIRouter, HTTPException
            from typing import List
            
            router = APIRouter()
            
            @router.get("/{name}")
            async def get_{name}():
                try:
                    # TODO: Implement business logic
                    return {{"message": "Success", "data": []}}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
        ''').strip()

    def _generate_post_endpoint(self, name: str) -> str:
        return textwrap.dedent(f'''
            from fastapi import APIRouter, HTTPException
            from pydantic import BaseModel
            
            router = APIRouter()
            
            class {name.title()}Request(BaseModel):
                # TODO: Define request fields
                name: str
                description: str = ""
            
            @router.post("/{name}")
            async def create_{name}(request: {name.title()}Request):
                try:
                    # TODO: Implement creation logic
                    return {{"message": "Created successfully", "id": 1}}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
        ''').strip()

    def _generate_generic_endpoint(self, name: str, method: str) -> str:
        return textwrap.dedent(f'''
            from fastapi import APIRouter, HTTPException
            
            router = APIRouter()
            
            @router.{method.lower()}("/{name}")
            async def {method.lower()}_{name}():
                try:
                    # TODO: Implement {method} logic
                    return {{"message": "{method} operation completed"}}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
        ''').strip()

    def _generate_pydantic_model(self, name: str, fields: list) -> str:
        if not fields:
            fields = [{"name": "id", "type": "int"}, {"name": "name", "type": "str"}]
        
        field_definitions = []
        for field in fields:
            field_name = field.get("name", "field")
            field_type = field.get("type", "str")
            default = field.get("default", "")
            
            if default:
                field_definitions.append(f"    {field_name}: {field_type} = {repr(default)}")
            else:
                field_definitions.append(f"    {field_name}: {field_type}")
        
        fields_str = "\n".join(field_definitions)
        
        return textwrap.dedent(f'''
            from pydantic import BaseModel
            from typing import Optional
            from datetime import datetime
            
            class {name}(BaseModel):
            {fields_str}
                
                class Config:
                    from_attributes = True
        ''').strip()

    def _generate_service_class(self, name: str, operations: list) -> str:
        if not operations:
            operations = ["create", "get", "update", "delete"]
        
        methods = []
        for op in operations:
            if op == "create":
                methods.append(self._generate_create_method())
            elif op == "get":
                methods.append(self._generate_get_method())
            elif op == "update":
                methods.append(self._generate_update_method())
            elif op == "delete":
                methods.append(self._generate_delete_method())
        
        methods_str = "\n\n".join(methods)
        
        return textwrap.dedent(f'''
            from typing import Dict, List, Any, Optional
            
            class {name}:
                def __init__(self):
                    # TODO: Initialize dependencies (database, external services, etc.)
                    pass
            
            {methods_str}
        ''').strip()

    def _generate_create_method(self) -> str:
        return textwrap.dedent('''
            async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
                # TODO: Implement creation logic
                return {"id": 1, "status": "created"}
        ''').strip()

    def _generate_get_method(self) -> str:
        return textwrap.dedent('''
            async def get(self, id: int) -> Optional[Dict[str, Any]]:
                # TODO: Implement retrieval logic
                return {"id": id, "status": "found"}
        ''').strip()

    def _generate_update_method(self) -> str:
        return textwrap.dedent('''
            async def update(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
                # TODO: Implement update logic
                return {"id": id, "status": "updated"}
        ''').strip()

    def _generate_delete_method(self) -> str:
        return textwrap.dedent('''
            async def delete(self, id: int) -> bool:
                # TODO: Implement deletion logic
                return True
        ''').strip()
