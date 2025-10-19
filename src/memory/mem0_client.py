"""
mem0 Integration Client
Handles persistent contextual memory retrieval and storage through mem0 REST API.
Subscribes to retrieval agent SSE stream for real-time memory updates.

Architecture:
- SSE Stream (8765): Retrieval agent broadcasts memory extraction events
- REST API: mem0-api.complexsimplicity.com/memories for storage/retrieval
- 7,800+ memories: Searchable knowledge base across Neo4J, Vector DB, Postgres
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import aiohttp
from aiohttp import ClientSession
import asyncio_contextmanager

logger = logging.getLogger(__name__)


class Mem0Client:
    """
    Async client for mem0 persistent memory system.
    Integrates retrieval agent (SSE) with memory storage (REST API).
    """

    def __init__(
        self,
        mem0_api_url: str = "https://mem0-api.complexsimplicity.com",
        mem0_api_key: str = "",
        retrieval_agent_host: str = "100.110.82.181",
        retrieval_agent_sse_port: int = 8765,
        enable_sse_streaming: bool = True,
    ):
        """
        Initialize mem0 client.

        Args:
            mem0_api_url: Base URL for mem0 REST API
            mem0_api_key: API key for mem0 authentication
            retrieval_agent_host: Host for retrieval agent
            retrieval_agent_sse_port: Port for SSE stream (5-second loop)
            enable_sse_streaming: Whether to subscribe to SSE stream
        """
        self.mem0_api_url = mem0_api_url
        self.mem0_api_key = mem0_api_key
        self.retrieval_agent_sse_url = (
            f"http://{retrieval_agent_host}:{retrieval_agent_sse_port}/stream"
        )
        self.enable_sse_streaming = enable_sse_streaming
        self.session: Optional[ClientSession] = None
        self.sse_task: Optional[asyncio.Task] = None
        self.memory_cache: Dict[str, Any] = {}
        self.is_connected = False

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        Connect to mem0 services and start SSE stream if enabled.

        Returns:
            bool: True if connection successful
        """
        try:
            self.session = aiohttp.ClientSession()

            # Test REST API connection
            if not await self._check_api_health():
                logger.error("mem0 REST API health check failed")
                return False

            logger.info("Connected to mem0 REST API")

            # Start SSE streaming if enabled
            if self.enable_sse_streaming:
                self.sse_task = asyncio.create_task(self._subscribe_to_sse_stream())
                logger.info("SSE stream subscription started (5-second retrieval loop)")

            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to mem0: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from mem0 services."""
        if self.sse_task:
            self.sse_task.cancel()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        self.is_connected = False
        logger.info("Disconnected from mem0")

    async def _check_api_health(self) -> bool:
        """Check mem0 REST API health."""
        try:
            async with self.session.get(
                f"{self.mem0_api_url}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"mem0 API health check error: {e}")
            return False

    async def _subscribe_to_sse_stream(self) -> None:
        """
        Subscribe to retrieval agent SSE stream (5-second loop).
        Processes memory extraction events in real-time.
        """
        while True:
            try:
                async with self.session.get(
                    self.retrieval_agent_sse_url,
                    timeout=aiohttp.ClientTimeout(total=300),  # 5-minute timeout
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            f"SSE stream returned {resp.status}, retrying..."
                        )
                        await asyncio.sleep(5)
                        continue

                    async for line in resp.content:
                        if not line:
                            continue

                        try:
                            line_str = line.decode().strip()
                            if line_str.startswith("data:"):
                                json_data = line_str[5:].strip()
                                event = json.loads(json_data)
                                await self._process_sse_event(event)
                        except json.JSONDecodeError as e:
                            logger.debug(f"SSE parse error: {e}")
                            continue

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE stream error: {e}, reconnecting in 5s...")
                await asyncio.sleep(5)

    async def _process_sse_event(self, event: Dict[str, Any]) -> None:
        """
        Process memory extraction event from retrieval agent.
        Stores in local cache for quick access.

        Args:
            event: Memory extraction event from SSE stream
        """
        try:
            memory_id = event.get("id")
            if memory_id:
                self.memory_cache[memory_id] = event
                logger.debug(f"Cached memory {memory_id} from SSE stream")
        except Exception as e:
            logger.error(f"Error processing SSE event: {e}")

    async def retrieve_memories_by_query(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories from mem0 by semantic search.
        Searches across 7,800+ memories in Neo4J/Vector DB.

        Args:
            query: Search query (will be embedded for semantic search)
            limit: Maximum memories to retrieve

        Returns:
            List of relevant memories with context
        """
        if not self.is_connected:
            logger.warning("Not connected to mem0")
            return []

        try:
            payload = {"query": query, "limit": limit}
            headers = {"Authorization": f"Bearer {self.mem0_api_key}"}

            async with self.session.post(
                f"{self.mem0_api_url}/memories/search",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    memories = data.get("memories", [])
                    logger.info(f"Retrieved {len(memories)} memories for query: {query}")
                    return memories
                else:
                    logger.error(f"Search failed with status {resp.status}")
                    return []

        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    async def retrieve_memories_by_topic(
        self, topic: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories by topic using Neo4J knowledge graph.
        Matches related conversations and contexts.

        Args:
            topic: Topic to search (e.g., "device_control", "conversations")
            limit: Maximum memories to retrieve

        Returns:
            List of topic-related memories
        """
        if not self.is_connected:
            logger.warning("Not connected to mem0")
            return []

        try:
            headers = {"Authorization": f"Bearer {self.mem0_api_key}"}

            async with self.session.get(
                f"{self.mem0_api_url}/memories/by-topic",
                params={"topic": topic, "limit": limit},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    memories = data.get("memories", [])
                    logger.info(
                        f"Retrieved {len(memories)} memories for topic: {topic}"
                    )
                    return memories
                else:
                    logger.error(f"Topic search failed with status {resp.status}")
                    return []

        except Exception as e:
            logger.error(f"Error retrieving topic memories: {e}")
            return []

    async def store_interaction(
        self,
        user_input: str,
        assistant_response: str,
        topic: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store interaction (user input + assistant response) to mem0.
        Injects into Neo4J, Vector DB, and Postgres.

        Args:
            user_input: User's voice command/question
            assistant_response: Assistant's response
            topic: Topic category for organization
            metadata: Additional metadata (device, timestamp, etc)

        Returns:
            bool: True if storage successful
        """
        if not self.is_connected:
            logger.warning("Not connected to mem0")
            return False

        try:
            payload = {
                "user_input": user_input,
                "assistant_response": assistant_response,
                "topic": topic or "general",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
            headers = {"Authorization": f"Bearer {self.mem0_api_key}"}

            async with self.session.post(
                f"{self.mem0_api_url}/memories",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Stored interaction in mem0: {topic}")
                    return True
                else:
                    logger.error(f"Storage failed with status {resp.status}")
                    return False

        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            return False

    async def get_knowledge_graph_context(
        self, entity: str, depth: int = 2
    ) -> Dict[str, Any]:
        """
        Retrieve knowledge graph context for entity.
        Shows relationships and connected memories.

        Args:
            entity: Entity to explore (person, place, concept)
            depth: Relationship depth to traverse

        Returns:
            Knowledge graph context with relationships
        """
        if not self.is_connected:
            logger.warning("Not connected to mem0")
            return {}

        try:
            headers = {"Authorization": f"Bearer {self.mem0_api_key}"}

            async with self.session.get(
                f"{self.mem0_api_url}/knowledge-graph/{entity}",
                params={"depth": depth},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Knowledge graph query failed with status {resp.status}")
                    return {}

        except Exception as e:
            logger.error(f"Error retrieving knowledge graph: {e}")
            return {}

    def get_cached_memories(self) -> Dict[str, Any]:
        """Get all cached memories from SSE stream."""
        return self.memory_cache.copy()

    async def clear_cache(self) -> None:
        """Clear local memory cache."""
        self.memory_cache.clear()
        logger.info("Memory cache cleared")


async def format_memories_for_context(memories: List[Dict[str, Any]]) -> str:
    """
    Format retrieved memories for LLM context injection.

    Args:
        memories: List of retrieved memories

    Returns:
        Formatted string for prepending to LLM prompt
    """
    if not memories:
        return ""

    context = "\n### Relevant Memory Context ###\n"
    for i, mem in enumerate(memories, 1):
        context += f"\n{i}. {mem.get('content', mem.get('text', ''))}\n"
        if metadata := mem.get("metadata"):
            context += f"   [Topic: {metadata.get('topic', 'N/A')}]\n"

    context += "\n### End Memory Context ###\n"
    return context
