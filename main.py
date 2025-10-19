# Windows AI Assistant
# Local AI-powered voice assistant with device control capabilities
# Runs entirely offline using Ollama + DirectML acceleration

import asyncio
import logging
from pathlib import Path

from src.core.assistant import WindowsAIAssistant
from src.config.settings import load_config

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/assistant.log'),
            logging.StreamHandler()
        ]
    )

async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Windows AI Assistant...")
    
    # Load configuration
    config = load_config()
    
    # Create and start the assistant
    assistant = WindowsAIAssistant(config)
    
    try:
        await assistant.start()
    except KeyboardInterrupt:
        logger.info("Shutting down assistant...")
    except Exception as e:
        logger.error(f"Error running assistant: {e}")
    finally:
        await assistant.stop()

if __name__ == "__main__":
    asyncio.run(main())