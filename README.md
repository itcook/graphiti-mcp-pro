# Graphiti MCP Pro

**English** | [中文](README_CN.md)

> **About Graphiti**
> Graphiti is a framework for building and querying temporally-aware knowledge graphs, specifically tailored for AI agents operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti continuously integrates user interactions, structured and unstructured enterprise data, and external information into a coherent, queryable graph. The framework supports incremental data updates, efficient retrieval, and precise historical queries without requiring complete graph recomputation, making it suitable for developing interactive, context-aware AI applications.

This project is an enhanced memory repository MCP service and management platform based on [Graphiti](https://github.com/getzep/graphiti). Compared to the original project's [MCP service](https://github.com/getzep/graphiti/tree/main/mcp_server), it offers the following core advantages: enhanced core capabilities, broader AI model compatibility, and comprehensive visual management interface.

## Features

### Enhanced Core Capabilities

#### Asynchronous Parallel Processing

Adding memories is the core functionality of the MCP service. We have introduced an asynchronous parallel processing mechanism based on the original implementation. The same group ID (such as different development projects) can execute up to 5 adding memory tasks in parallel, significantly improving processing efficiency.

#### Task Management Tools

Four new MCP tools have been added for managing `add_memory` tasks:

- `list_add_memory_tasks` - List all `add_memory` tasks
- `get_add_memory_task_status` - Get `add_memory` task status
- `wait_for_add_memory_task` - Wait for `add_memory` task completion
- `cancel_add_memory_task` - Cancel `add_memory` task

#### Unified Configuration Management

Optimized configuration management to resolve inconsistencies between command-line parameters, environment variables, and management backend database configurations.

> [!NOTE]
> When the management backend is enabled, MCP service parameters in the .env environment configuration file only take effect during the initial startup. Subsequent configurations will be based on parameters in the management backend database.

### Broader AI Model Compatibility and Flexibility

#### Enhanced Model Compatibility

Through integration with the [instructor](https://github.com/567-labs/instructor) library, model compatibility has been significantly improved. Now supports various models such as DeepSeek, Qwen, and even locally run models through Ollama, vLLM, as long as they provide OpenAI API compatible interfaces.

#### Separated Model Configuration

The original unified LLM configuration has been split into three independent configurations, allowing flexible combinations based on actual needs:

- **Large Model (LLM)**: Responsible for entity and relationship extraction
- **Small Model (Small LLM)**: Handles entity attribute summarization, relationship deduplication, reranking, and other lightweight tasks
- **Embedding Model (Embedder)**: Dedicated to text vectorization

> [!NOTE]
> When configuring the embedding model, note that its API path differs from the two LLMs above. LLMs use the chat completion path `{base_url}/chat/completions`, while text embedding uses `{base_url}/embeddings`. If you select "Same as Large Model" in the management backend, ensure your configured large model supports text embedding.

### Comprehensive Management Platform

To provide better user experience and observability, we have developed a complete management backend and Web UI. Through the management interface, you can:

- **Service Control**: Start, stop, restart MCP service
- **Configuration Management**: Real-time configuration updates and adjustments
- **Usage Monitoring**: View detailed token usage statistics
- **Log Viewing**: Real-time and historical log queries

## Getting Started

### Running with Docker Compose (Recommended)

1. **Clone Project**

   ```bash
   git clone http://github.com/itcook/graphiti-mcp-pro
   cd graphiti-mcp-pro
   ```

2. **Configure Environment Variables** (Optional)

   ```bash
   # Copy example configuration file
   mv .env.example.en .env
   # Edit .env file according to the instructions
   ```

3. **Start Services**

   ```bash
   docker compose up -d
   ```

   > [!TIP]
   > If the project has updates and you need to rebuild the image, use `docker compose up -d --build`.
   > Rest assured, data will be persistently saved in the external database and will not be lost.

4. **Access Management Interface**
   Default address: http://localhost:6062

### Manual Installation

> [!NOTE]
> Prerequisites:
>
> 1. Python 3.10+ and uv project manager
> 2. Node.js 20+
> 3. Accessible Neo4j 5.26+ database service
> 4. AI model service

1. **Clone Project**

   ```bash
   git clone http://github.com/itcook/graphiti-mcp-pro
   cd graphiti-mcp-pro
   ```

2. **Install Dependencies**

   ```bash
   uv sync
   ```

3. **Configure Environment Variables**

   ```bash
   # Copy example configuration file
   mv .env.example.cn .env
   # Edit .env file according to the instructions
   ```

4. **Run MCP Service**

   ```bash
   # Run service with management backend
   uv run main.py -m
   # Or run MCP service only
   # uv run main.py
   ```

5. **Build and Run Management Frontend**

   Enter frontend directory and install dependencies:

   ```bash
   cd manager/frontend
   pnpm install  # or npm install / yarn
   ```

   Build and run frontend:

   ```bash
   pnpm run build   # or npm run build / yarn build
   pnpm run preview # or npm run preview / yarn preview
   ```

   Access management interface: http://localhost:6062

## Important Notes

### Known Limitations

- **🔒 Security Notice**: The management backend does not implement authorization access mechanisms. DO NOT expose the service on public servers.
- **🧪 Test Coverage**: Due to resource constraints, the project has not been thoroughly tested. Recommended for personal use only.
- **📡 Transport Protocol**: Only supports streamable-http transport protocol. Removed stdio and sse support from the original project.
- **⚙️ Code Optimization**: Some architectural designs (dependency injection, exception handling, client decoupling, etc.) still have room for optimization.

### Usage Recommendations

- **Configuration Instructions**: Please carefully read the setup instructions and comments in `.env.example.en`
- **Model Selection**: If using natively supported models like GPT/Gemini/Claude and don't need detailed runtime information, consider using the original [Graphiti MCP](https://github.com/getzep/graphiti/tree/main/mcp_server)
- **Issue Feedback**: Welcome to submit Issues or Pull Requests for any usage problems

---

Developed with assistance from 🤖 [Augment Code](https://augmentcode.com)
