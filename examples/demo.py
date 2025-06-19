import asyncio
from ..core.framework import AgentFramework
from ..core.models import AgentConfig, AgentMessage, MessageType
from ..agents.factory import AgentFactory
from ..interfaces.rest_api import APIServer
from ..systems.monitoring import MonitoringManager
from ..systems.persistence import PersistenceManager

async def demo_basic_agents():
    print("=== AgentAPI Framework Demo ===")
    
    framework = AgentFramework()
    await framework.start()
    
    try:
        strategist_config = AgentConfig(
            name="strategist-1",
            capabilities=["plan_project", "analyze_requirements"]
        )
        
        strategist = AgentFactory.create_agent(
            "strategist",
            strategist_config,
            framework.message_bus,
            framework.resource_manager
        )
        
        await framework.registry.register(strategist)
        
        code_gen_config = AgentConfig(
            name="codegen-1",
            capabilities=["generate_api", "generate_model"]
        )
        
        code_gen = AgentFactory.create_agent(
            "code_generator",
            code_gen_config,
            framework.message_bus,
            framework.resource_manager
        )
        
        await framework.registry.register(code_gen)
        
        print("Agents registered successfully")
        
        agents = await framework.registry.list_agents()
        print(f"Active agents: {len(agents)}")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['status']})")
        
        request_message = AgentMessage(
            type=MessageType.REQUEST,
            sender="demo",
            receiver="strategist-1",
            capability="plan_project",
            payload={"requirements": "Build a REST API for user management"}
        )
        
        await framework.message_bus.send_message(request_message)
        print("Message sent to strategist")
        
        api_request = AgentMessage(
            type=MessageType.REQUEST,
            sender="demo",
            receiver="codegen-1",
            capability="generate_api",
            payload={"name": "users", "method": "POST"}
        )
        
        await framework.message_bus.send_message(api_request)
        print("Message sent to code generator")
        
        await asyncio.sleep(2)
        
        metrics = await framework.get_metrics()
        print(f"System metrics - CPU: {metrics.cpu_percent}%, Memory: {metrics.memory_percent}%")
        
    finally:
        await framework.stop()
        print("Framework stopped")

async def demo_full_system():
    print("=== Full System Demo ===")
    
    persistence = PersistenceManager()
    await persistence.initialize()
    
    monitoring = MonitoringManager()
    await monitoring.start()
    
    framework = AgentFramework()
    await framework.start()
    
    try:
        agents_config = [
            ("strategist", "strategy-agent", ["plan_project", "analyze_requirements"]),
            ("code_generator", "codegen-agent", ["generate_api", "generate_model"]),
            ("test_generator", "test-agent", ["generate_unit_tests"]),
            ("build", "build-agent", ["generate_dockerfile", "generate_docker_compose"])
        ]
        
        for agent_type, name, capabilities in agents_config:
            config = AgentConfig(name=name, capabilities=capabilities)
            agent = AgentFactory.create_agent(
                agent_type, config, framework.message_bus, framework.resource_manager
            )
            await framework.registry.register(agent)
            await persistence.save_agent(name, config.__dict__, "running")
        
        print("Full agent pipeline created")
        
        workflow_messages = [
            ("strategy-agent", "analyze_requirements", {"text": "Create a user management system with authentication"}),
            ("codegen-agent", "generate_api", {"name": "auth", "method": "POST"}),
            ("test-agent", "generate_unit_tests", {"class_name": "AuthService", "methods": ["login", "register"]}),
            ("build-agent", "generate_dockerfile", {"language": "python", "app_type": "api"})
        ]
        
        for receiver, capability, payload in workflow_messages:
            message = AgentMessage(
                type=MessageType.REQUEST,
                sender="demo",
                receiver=receiver,
                capability=capability,
                payload=payload
            )
            await framework.message_bus.send_message(message)
            await persistence.save_message(message)
            await asyncio.sleep(1)
        
        print("Workflow executed")
        
        await asyncio.sleep(5)
        
        health = await monitoring.health_check()
        print(f"System health: {health['status']}")
        
        summary = monitoring.get_metrics_summary()
        if summary:
            print(f"Average CPU: {summary['avg_cpu']:.1f}%")
        
    finally:
        await monitoring.stop()
        await framework.stop()
        print("Full system demo completed")

if __name__ == "__main__":
    print("Starting AgentAPI Demo...")
    asyncio.run(demo_basic_agents())
    print("\n" + "="*50 + "\n")
    asyncio.run(demo_full_system())