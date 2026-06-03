# LatentSense Python SDK

## Overview

The LatentSense Python SDK provides a convenient and developer-friendly client for accessing the LatentSense Interactive APIs. Designed for enterprise environments, it streamlines authentication, file handling, and API interactions, enabling organizations to transform unbounded corpora of unstructured language-as-data into reasoning-ready semantic structures (through rxMaps) and privacy-preserving data assets (through DeiD).

Through capabilities such as semantic spaces mapping, saliency detection, relationship discovery, and data de-identification, the SDK helps convert language data into interoperable semantic infrastructure that can power analytics, agentic automation, knowledge systems, business workflows, and decision-making at enterprise scale. No RAG. No re-platforming. No ETL required.

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

See `https://docs.latentsense.com`

Here's a basic example of how to initialize the client and use it to create rxMaps (readining ready data) or redact Personally Identifiable Information (PII) from a document.

```python
import os
from latentsense_sdk import LatentSenseClient

# The client is configured via environment variables.
# Ensure they are set before running, for example:
# os.environ["LST_PROJECT_ID"] = "your-project-id"
# os.environ["LST_API_KEY"] = "your-api-key"

client = LatentSenseClient()

# Example 1: Create RxMap
in_memory_file = ("report.txt", "This is a report about Jane Smith.")
rx_map_results = client.create_rx_map(files=[in_memory_file])

for result in rx_map_results:
    print(f"--- Results for {result.original_file_name} ---")
    print(f"Nodes in graph: {result.graph.nodes}")


# Example 2: Redact PII
in_memory_file = ("report.txt", "This is a report about Jane Smith.")
redacted_results = client.redact_pii(files=[in_memory_file])

for result in redacted_results:
    print(f"--- Results for {result.original_file_name} ---")
    print(f"Redacted text: {result.redacted_text}")

```
