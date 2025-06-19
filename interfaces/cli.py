import click
import asyncio
import json
from typing import Dict, Any
from ..core.framework import AgentFramework
from ..core.models import AgentConfig
from ..agents.factory import AgentFactory

class CLIManager:
    def __init__(self):
        self.framework = AgentFramework()

    async def start_framework(self):
        await self.framework.start()

    async def stop_framework(self):
        await self.framework.stop()

@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['cli_manager'] = CLIManager()

@cli.command()
@click.option('--port', default=8000, help='Port to run the API server')
@click.pass_context
def serve(ctx, port):
    async def run_server():
        cli_manager = ctx.obj['cli_manager']
        await cli_manager.start_framework()
        
        from ..interfaces.rest_api import APIServer
        import uvicorn
        
        api_server = APIServer(cli_manager.framework)
        
        try:
            config = uvicorn.Config(api_server.app, host="0.0.0.0", port=port)
            server = uvicorn.Server(config)
            await server.serve()
        finally:
            await cli_manager.stop_framework()
    
    asyncio.run(run_server())

@cli.command()
@click.argument('agent_type')
@click.argument('name')
@click.option('--capabilities', multiple=True, help='Agent capabilities')
@click.pass_context
def create_agent(ctx, agent_type, name, capabilities):
    async def create():
        cli_manager = ctx.obj['cli_manager']
        await cli_manager.start_framework()
        
        try:
            config = AgentConfig(name=name, capabilities=list(capabilities))
            agent = AgentFactory.create_agent(
                agent_type,
                config,
                cli_manager.framework.message_bus,
                cli_manager.framework.resource_manager
            )
            await cli_manager.framework.registry.register(agent)
            click.echo(f"Agent '{name}' created successfully")
        except Exception as e:
            click.echo(f"Error creating agent: {e}")
        finally:
            await cli_manager.stop_framework()
    
    asyncio.run(create())

@cli.command()
@click.pass_context
def list_agents(ctx):
    async def list_all():
        cli_manager = ctx.obj['cli_manager']
        await cli_manager.start_framework()
        
        try:
            agents = await cli_manager.framework.registry.list_agents()
            if agents:
                for agent in agents:
                    click.echo(f"- {agent['name']} ({agent['status']}) - {', '.join(agent['capabilities'])}")
            else:
                click.echo("No agents found")
        finally:
            await cli_manager.stop_framework()
    
    asyncio.run(list_all())

@cli.command()
@click.pass_context
def metrics(ctx):
    async def show_metrics():
        cli_manager = ctx.obj['cli_manager']
        await cli_manager.start_framework()
        
        try:
            metrics = await cli_manager.framework.get_metrics()
            click.echo(f"CPU: {metrics.cpu_percent}%")
            click.echo(f"Memory: {metrics.memory_percent}%")
            click.echo(f"Disk: {metrics.disk_usage}%")
            click.echo(f"Active Agents: {metrics.active_agents}")
        finally:
            await cli_manager.stop_framework()
    
    asyncio.run(show_metrics())

@cli.command()
def agent_types():
    types = AgentFactory.list_agent_types()
    click.echo("Available agent types:")
    for agent_type in types:
        click.echo(f"- {agent_type}")

if __name__ == '__main__':
    cli()