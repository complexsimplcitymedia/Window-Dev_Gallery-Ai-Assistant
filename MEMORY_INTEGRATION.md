# mem0 Persistent Memory Integration

This guide explains how the Windows AI Assistant learns and grows smarter from every interaction using mem0's 7,800+ persistent memories.

## Overview: How Memory Works

```
User Voice Input
      ↓
┌─────────────────────────────────────────────────┐
│  Retrieval Agent (SSE Stream, Port 8765)        │
│  - 5-second processing loop                     │
│  - Extracts relevant memories from user input   │
│  - Categorizes by topic/context                 │
│  - Continuously scans for patterns              │
└─────────────────────────────────────────────────┘
      ↓ SSE Streaming
┌─────────────────────────────────────────────────┐
│  Voice Assistant (Windows)                       │
│  1. RETRIEVE: Query mem0 for relevant memories  │
│  2. INJECT: Add memories to LLM context         │
│  3. REASON: Ollama generates better response    │
│  4. STORE: Save interaction back to mem0        │
└─────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────┐
│  mem0 REST API (Entry Point - Your Fix!)        │
│  Status: ✅ Stable connection to Neo4J          │
└─────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────┐
│  Data Storage Layer (6 Containers)              │
│  ┌─────────────────────────────────────────┐   │
│  │ PostgreSQL: Structured interaction data │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ Vector DB: Semantic similarity search   │   │
│  │ (embeddings of all 7,800+ memories)     │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ Neo4J: Knowledge graph with 7,800+      │   │
│  │ relationships, patterns, entities       │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## The 4-Step Memory Cycle

Every voice command follows this cycle:

### 1. RETRIEVE - Query Relevant Memories

```python
# Voice Assistant queries mem0 for context
memories = await mem0_client.retrieve_memories_by_query(
    query="open calculator",
    limit=5
)

# Returns something like:
[
  {
    "id": "mem_xyz_123",
    "content": "User asked to open calculator yesterday. Preferred using Win+R shortcut.",
    "topic": "device_control",
    "metadata": {"source": "past_interaction", "confidence": 0.95}
  },
  {
    "id": "mem_xyz_456", 
    "content": "User prefers calculator to open in certain position on screen.",
    "topic": "preferences",
    "metadata": {"learned_from": 7, "times_repeated": 3}
  }
]
```

**What happens:**
- Voice input: "Open calculator"
- Semantic search across 7,800 memories
- Vector DB finds most similar past interactions
- Neo4J knowledge graph returns relationships
- Result: 5 most relevant memories injected into LLM context

### 2. INJECT - Augment LLM Prompt with Memory

```python
# Memory context is added to system prompt
system_prompt = base_system_prompt + memory_context

# LLM sees:
"""
System: You are a Windows AI Assistant...

### Relevant Memory Context ###

1. User asked to open calculator yesterday. Preferred using Win+R shortcut.
   [Topic: device_control]

2. User prefers calculator to open in certain position on screen.
   [Topic: preferences]

### End Memory Context ###

User: Open calculator
"""

# Result: Ollama generates smarter response using historical context
response = await ollama.generate(system_prompt + user_input)
```

**What this means:**
- LLM knows it opened calculator before
- LLM knows user preferences about placement
- LLM can reference: "I remember you opened this yesterday using Win+R"
- Assistant becomes contextually aware

### 3. REASON - Enhanced LLM Response

With memory context, Ollama generates better responses:

**Without memory:**
```
User: "Open calculator"
Assistant: "Opening calculator."
[Generic response, no context]
```

**With 7,800 memories:**
```
User: "Open calculator"
Assistant: "I remember you opened this yesterday and preferred the Win+R shortcut. 
Opening calculator the same way in your preferred window position."
[Contextually aware, learns patterns]
```

### 4. STORE - Save Interaction for Future Learning

```python
# After assistant responds, interaction is stored in mem0
await mem0_client.store_interaction(
    user_input="open calculator",
    assistant_response="Opening calculator with Win+R...",
    topic="device_control",
    metadata={
        "success": True,
        "device": "voice_assistant",
        "execution_time_ms": 245,
        "user_confirmed": True
    }
)

# This interaction joins 7,800+ others in:
# - PostgreSQL (raw data)
# - Vector DB (semantic embeddings)
# - Neo4J (knowledge graph with relationships)
```

**What happens:**
- Interaction stored with timestamp
- Embedded into vectors for future semantic search
- Connected in Neo4J knowledge graph
- Now available for next similar voice command

## Memory Retrieval Strategies

The assistant uses multiple strategies to retrieve relevant memories:

### 1. Semantic Search (Primary)

```python
# Find memories by meaning, not just keywords
memories = await mem0_client.retrieve_memories_by_query(
    query="launch a web browser",
    limit=5
)

# Matches similar concepts:
# - "open chrome"
# - "start firefox"  
# - "web browser"
# - "browser window"
```

### 2. Topic-Based Search

```python
# Find all memories about specific topic
device_control_memories = await mem0_client.retrieve_memories_by_topic(
    topic="device_control",
    limit=10
)

# Retrieves all past device commands:
# - "shutdown in 5 minutes"
# - "restart computer"
# - "lock workstation"
# - "launch application"
```

### 3. Knowledge Graph Context

```python
# Explore connected relationships
context = await mem0_client.get_knowledge_graph_context(
    entity="calculator",
    depth=2
)

# Returns:
{
    "calculator": {
        "related_commands": ["open", "launch", "start"],
        "user_preferences": ["window_position", "theme"],
        "past_failures": ["timeout", "slow_startup"],
        "success_rate": 0.98
    }
}
```

## Real-World Example: Learning from Mistakes

### Day 1: First Interaction
```
User: "Shut down the computer"
Assistant: "Do you want to shutdown? Requires 'wolf-logic' confirmation."
User: "wolf-logic"
Assistant: "Shutting down Windows..."

STORED IN MEM0:
- Command: shutdown
- Confirmed by: wolf-logic keyword
- Success: True
- Time of day: 5:30 PM
```

### Day 2: Similar Request
```
User: "Shut down the computer"

RETRIEVAL AGENT FINDS:
- Yesterday you shut down at 5:30 PM
- Command confirmed with wolf-logic
- 100% success rate

INJECTED INTO PROMPT:
"User previously shut down yesterday at 5:30 PM with confirmation.
This appears to be an intentional action."

ASSISTANT RESPONSE (Now Contextually Aware):
"I remember you shut down yesterday around this time. 
Ready to shut down again with confirmation. Say 'wolf-logic' to proceed."

USER: "wolf-logic"
ASSISTANT: "Shutting down..."

STORED IN MEM0:
- 2nd shutdown command
- User is building a pattern of shutdowns at 5:30 PM
- Neo4J links these as related events
```

### Day 3: Assistant Gets Smart

```
User: "Shut down"
[Only one word, but...]

RETRIEVAL AGENT FINDS:
- User has shut down computer 2x before
- Both times around 5:30 PM
- Both times confirmed with wolf-logic
- 100% success rate
- High confidence this is intentional

ASSISTANT (Now Predicting Intent):
"Based on your shutdown history at this time, I'm ready to shut down.
This will confirm and shut down immediately."

[Assistant has learned the pattern AND the proper confirmation method]
```

## The 7,800 Memories: What They Mean

Your mem0 has 7,800+ stored memories. These represent:

- **Device Commands**: "Open X", "Close Y", "Launch Z"
- **User Preferences**: Favorite settings, window positions, themes
- **Patterns**: Times you usually do things, sequences of commands
- **Failures**: What didn't work, so assistant learns to avoid
- **Successes**: What worked well, should repeat
- **Context**: Relationships between different actions
- **Learning**: How preferences changed over time

**Example Neo4J Knowledge Graph:**

```
[Interaction: "Open Calculator"] 
    ├─ Related_To: [Device Command: "Launch"]
    ├─ User_Prefers: [Window Position: "Top Right"]
    ├─ Success_Rate: 0.98
    ├─ Time_Pattern: [Afternoon, usually 2-4 PM]
    ├─ Followed_By: [Open Notepad]
    └─ Failed_When: [System under heavy load]

[User Preference: "Window Position: Top Right"]
    ├─ Applied_To: [Calculator, Notepad, Chrome]
    ├─ User_Confirmed: True
    └─ Consistency: 0.95
```

## Configuration

### Enable/Disable Persistent Memory

In `.env`:

```bash
# Enable persistent memory system
ENABLE_PERSISTENT_MEMORY=true

# mem0 REST API endpoint (your fixed version)
MEM0_API_URL=https://mem0-api.complexsimplicity.com
MEM0_API_KEY=your_api_key_here

# Retrieval agent (5-second loop)
MEM0_RETRIEVAL_AGENT_HOST=100.110.82.181
MEM0_RETRIEVAL_AGENT_PORT=8765
ENABLE_SSE_STREAMING=true

# How many memories to retrieve per query
MEMORY_CONTEXT_LIMIT=5
```

### Memory Context in Prompts

The assistant's system prompt includes:

```python
PERSISTENT_MEMORY_CONTEXT = """
You have access to persistent memory across 7,800+ interactions stored in Neo4J knowledge graph.
Before responding, relevant past memories are included below. Use them to:
- Reference past decisions and their outcomes
- Learn from mistakes
- Provide consistent, informed responses
- Build on previous knowledge about the user's preferences and patterns
"""
```

## Architecture: Under the Hood

### mem0_client.py

```python
class Mem0Client:
    """Async client for mem0 with SSE streaming + REST API"""
    
    async def retrieve_memories_by_query(query, limit=5):
        """Semantic search across all 7,800+ memories"""
        
    async def retrieve_memories_by_topic(topic, limit=5):
        """Find all memories about specific topic"""
        
    async def store_interaction(user_input, response, topic, metadata):
        """Store new interaction in Neo4J + Vector DB + Postgres"""
        
    async def get_knowledge_graph_context(entity, depth=2):
        """Explore Neo4J relationships and connections"""
        
    async def _subscribe_to_sse_stream():
        """Subscribe to retrieval agent's 5-second loop for real-time updates"""
```

### Integration in assistant.py

```python
# Before each LLM query:
memories = await mem0_client.retrieve_memories_by_query(user_input, limit=5)
context = format_memories_for_context(memories)
system_prompt += context

# After each interaction:
await mem0_client.store_interaction(
    user_input, 
    response,
    topic,
    metadata
)
```

## Performance & Scale

### Current System (Your Setup)
- **Memories**: 7,800+
- **Retrieval Time**: ~200ms (semantic search)
- **Storage Rate**: ~10 memories/second
- **Context Window**: 5 memories per query

### Scaling to 100,000+ Memories
- Neo4J query optimization via indexing
- Vector DB partitioning by date ranges
- LRU cache for frequent memories
- Pagination for bulk retrieval

## Security

✅ **Protected:**
- API key in `.env` (git-ignored)
- All queries through mem0 REST API
- Encryption in transit (Tailscale VPN)
- No raw memory exposure

⚠️ **Be Careful:**
- Don't expose MEM0_API_KEY
- Don't query memories over unencrypted networks
- Regular backups of PostgreSQL/Neo4J

## Troubleshooting

### Memory Not Being Retrieved
```python
# Check mem0 connection
status = assistant.get_status()
print(f"mem0 connected: {status['mem0_connected']}")
print(f"cached memories: {status['cached_memories']}")
```

### Memories Not Storing
```bash
# Check mem0 API
curl -H "Authorization: Bearer $MEM0_API_KEY" \
  https://mem0-api.complexsimplicity.com/health
  
# Check logs
docker logs mem0_api
```

### SSE Stream Not Working
```bash
# Verify retrieval agent is running
curl http://100.110.82.181:8765/health

# Check mem0 docker status
docker ps | grep mem0
```

## Next Steps

1. ✅ Deploy mem0 (6 containers)
2. ✅ Run voice assistant with memory integration
3. ✅ Make several voice commands (building up memory)
4. 📊 Observe learning: Assistant gets smarter over time
5. 🧠 Explore Neo4J UI to visualize knowledge graph
6. 🚀 Scale to 100,000+ memories with optimization

---

**Your Contribution:** You fixed the mem0 REST API stability issue, enabling the entire local memory system to work reliably. This fix should be pushed upstream so others can benefit!
