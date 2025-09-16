#!/usr/bin/env python3
"""
Production startup script for Fantasy Football AI Multi-Agent System.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.api.multi_agent_server import MultiAgentFantasyServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fantasy_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check that required environment variables are set."""
    required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please check your .env file or environment configuration")
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    directories = [
        'logs',
        'database',
        'database/vector_store'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

async def test_system_health():
    """Test system components before starting."""
    logger.info("Testing system health...")
    
    try:
        # Test that we can import all components
        from backend.agents.coordinator import AgentCoordinator
        from backend.agents.llm_integration import LLMManager
        from backend.scrapers.sleeper_api import SleeperAPI
        
        # Test Sleeper API connection
        async with SleeperAPI() as sleeper:
            test_user = await sleeper.get_user('testuser')
            logger.info("✓ Sleeper API connection successful")
        
        # Test agent initialization
        coordinator = AgentCoordinator()
        logger.info(f"✓ Agent coordinator initialized with {len(coordinator.agents)} agents")
        
        # Test LLM manager
        llm_manager = LLMManager()
        logger.info("✓ LLM manager initialized")
        
        logger.info("System health check passed!")
        return True
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return False

def main():
    """Main entry point for production server."""
    logger.info("Starting Fantasy Football AI Multi-Agent System...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Test system health
    if not asyncio.run(test_system_health()):
        logger.error("System health check failed. Exiting.")
        sys.exit(1)
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8001))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Initialize and run server
    try:
        server = MultiAgentFantasyServer(
            enable_vector_db=os.getenv('ENABLE_VECTOR_DB', 'true').lower() == 'true',
            enable_background_tasks=os.getenv('ENABLE_BACKGROUND_TASKS', 'true').lower() == 'true'
        )
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info("API documentation available at: http://localhost:8001/docs")
        
        server.run(
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()