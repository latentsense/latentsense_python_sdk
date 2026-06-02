# LatentSense Python SDK

## Overview

The LatentSense Python SDK provides a convenient client for interacting with the Latentsense Interactive API. It simplifies authentication, file uploads, and requests to various API endpoints for text analysis and manipulation.

## Installation

`pip install latentsense-sdk`

## Configuration

The client can be configured by passing parameters to its constructor or by using environment variables.

### Constructor Arguments
You can initialize the client directly with your credentials:
```python
from latentsense_sdk import LatentSenseClient

client = LatentSenseClient(
    project_id="your-project-id",
    api_key="your-api-key",
)
```

### Environment Variables
If constructor arguments are not provided, the client will fall back to reading from environment variables:

- `LST_PROJECT_ID`: Your LatentSense project ID.
- `LST_API_KEY`: Your LatentSense API key.

For example, in your shell:
```bash
export LST_PROJECT_ID="your-project-id"
export LST_API_KEY="your-api-key"
```

## Usage

See public methods of LatentSenseClient.

For API documentation, see `https://docs.latentsense.com`

```python
import asyncio
from latentsense_sdk import LatentSenseClient

# The client is configured via environment variables.
# Ensure they are set before running, for example:
# os.environ["LST_PROJECT_ID"] = "your-project-id"
# os.environ["LST_API_KEY"] = "your-api-key"

client = LatentSenseClient()

async def rx_map_example():
    in_memory_file = ("report.txt", "This is a report about Jane Smith.")
    rx_map_results = await client.create_rx_map(files=[in_memory_file])
    
    for result in rx_map_results:
        print(f"--- Results for {result.file.name} ---")
        print(f"Nodes in graph: {result.graph.nodes}")


async def redaction_example():
    in_memory_file = ("report.txt", "This is a report about Jane Smith.")
    redacted_results = await client.redact_pii(files=[in_memory_file])
    
    for result in redacted_results:
        print(f"--- Results for {result.file.name} ---")
        print(f"Redacted text: {result.redacted}")
        
if __name__ == '__main__':
    asyncio.run(rx_map_example())
    asyncio.run(redaction_example())

```
