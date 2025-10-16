# Warning: read this first:

As litellm [just merged something to always get the pricing from openrouter's usage answer](https://github.com/BerriAI/litellm/issues/13653#event-20238386551) I don't think this project is useful anymore and will archive it.

# Warning: read this
As of early october 2025, I noticed a few problematic things with openrouter's pricing API:
1. The [load balancing](https://openrouter.ai/docs/features/provider-routing) is based on the "cost" of a model but openrouter does not explain how they turn the prompt cost + completion cost + caching cost + image cost into a single "cost" value.
2. The `throughput` and `latency` are not retuned in the endpoint API call (see `curl https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-4.5/endpoints | jq`).
That means that I can't have the information needed to know which provider would be used. Similarly, if you use `anthropic/claude-sonnet-4.5:nitro` then your query will go to the highest throughput provider but the API does not provide the means to know which one that would be.
So yeah, the script works but as long as openrouter does not fix the above it can be imprecise. By just a bit or by a lot depending on how you use openrouter.

I reached out to openrouter about this to see if they're willing to address this. If you happen to be someone of inluence, don't hesitate to reach out!

Edit: after seeing with the team by emaim they seem to be working on a fix. Will update when they update me.

# LiteLLM Proxy OpenRouter Price Updater

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A CLI tool that compares local OpenRouter model pricing in LiteLLM proxy configuration files with the actual pricing from OpenRouter's API. This helps maintain accurate cost tracking by identifying missing or outdated pricing information.

This script assumes that in your [openrouter preferences](https://openrouter.ai/settings/preferences) you set `Default Provider Sort` to `Price (cheapest first)`.

You might also be interested in my other script: [OpenRouter to Langfuse Model Pricing Sync](https://github.com/thiswillbeyourgithub/openrouter_cost_into_langfuse).

## Features

- Fetches current pricing data from OpenRouter API
- Compares local configuration pricing with API pricing
- Identifies missing pricing fields in your configuration
- Detects price mismatches between local config and API
- Supports all OpenRouter pricing fields:
  - Input cost per token (prompt pricing)
  - Output cost per token (completion pricing)  
  - Cache creation input token cost
  - Cache read input token cost
  - Input cost per image
  - Output cost per reasoning token
- Detailed logging with color-coded output
- Exit codes for CI/CD integration

## Installation

### Prerequisites

- Python 3.7+
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python litellm_proxy_openrouter_price_updater.py --config path/to/your/litellm_config.yaml
```

### Command-Line Options

- `--config`: (Required) Path to the YAML configuration file
- `--cache-as-warnings`: (Optional) Treat cache-related pricing differences (cache creation and cache read costs) as informational warnings instead of errors. This is useful when you want to be notified about cache pricing differences without failing your CI/CD pipeline.

Example with cache warnings:
```bash
python litellm_proxy_openrouter_price_updater.py --config path/to/your/litellm_config.yaml --cache-as-warnings
```

### Example Output

```
2024-01-15 10:30:12.345 | INFO     | Fetched 150 models from OpenRouter API
2024-01-15 10:30:12.456 | INFO     | Found 5 OpenRouter models in config
2024-01-15 10:30:12.567 | INFO     | Checking model: GPT-4 Turbo (openrouter/openai/gpt-4-turbo)
2024-01-15 10:30:12.678 | SUCCESS  | Pricing is up to date for GPT-4 Turbo
2024-01-15 10:30:12.789 | WARNING  | Pricing discrepancies for Claude 3:
2024-01-15 10:30:12.890 |          |   - Missing cache_read_input_token_cost: API has input_cache_read=0.000001
2024-01-15 10:30:12.991 |          |   - output_cost_per_token mismatch: local=0.000015, API=0.000016
2024-01-15 10:30:13.100 | INFO     | Pricing warnings for Mixtral:
2024-01-15 10:30:13.200 |          |   - API has pricing for 'web_search' (0.003) - not tracked by LiteLLM
2024-01-15 10:30:13.300 | INFO     | ============================================================
2024-01-15 10:30:13.400 | INFO     | PRICING CHECK RECAP
2024-01-15 10:30:13.500 | INFO     | ============================================================
2024-01-15 10:30:13.600 | INFO     | Total models checked: 5
2024-01-15 10:30:13.700 | INFO     | Models with pricing issues: 1
2024-01-15 10:30:13.800 | INFO     | Models with warnings: 1
2024-01-15 10:30:13.900 | INFO     | Total pricing issues: 2
2024-01-15 10:31:14.000 | INFO     | Total warnings: 1
```

### Configuration File Format

The tool expects a LiteLLM proxy configuration file with OpenRouter models defined like this:

```yaml
model_list:
  - model_name: "gpt-4-turbo"
    litellm_params:
      model: "openrouter/openai/gpt-4-turbo"
      input_cost_per_token: 0.00001
      output_cost_per_token: 0.00003
      cache_creation_input_token_cost: 0.0000125
      cache_read_input_token_cost: 0.0000025
      input_cost_per_image: 0.001445
      output_cost_per_reasoning_token: 0.00006
```

### Exit Codes

- `0`: All pricing is up to date (warnings are allowed)
- `1`: Pricing discrepancies found or error occurred

This makes the tool suitable for use in CI/CD pipelines to catch pricing configuration drift. Note that informational warnings (like unsupported API pricing fields) do not cause a non-zero exit code.

## Development


## Error Handling

The tool handles various error conditions gracefully:

- **Missing config file**: Clear error message with file path
- **Invalid YAML**: Detailed parsing error information  
- **API failures**: Network timeout and HTTP error handling
- **Missing models**: Warning when local models aren't found in API
- **Model modifiers**: Automatically strips modifiers (e.g., `:nitro`) from model IDs when comparing with API
- **Unsupported pricing fields**: Some API pricing fields (like `web_search`) generate informational warnings rather than errors

## Output Types

The tool distinguishes between two types of issues:

- **Discrepancies**: Missing or mismatched pricing that should be fixed (causes exit code 1)
- **Warnings**: Informational messages about API pricing fields not tracked by LiteLLM (exit code 0)

At the end of each run, a detailed recap summary shows:
- Total models checked
- Models with pricing issues vs warnings
- Counts of total issues and warnings
- Lists of affected models

## Pricing Fields Supported

| Local Config Field | OpenRouter API Field | Description |
|-------------------|---------------------|-------------|
| `input_cost_per_token` | `prompt` | Cost per input token |
| `output_cost_per_token` | `completion` | Cost per output token |
| `cache_creation_input_token_cost` | `input_cache_write` | Cost to write to cache |
| `cache_read_input_token_cost` | `input_cache_read` | Cost to read from cache |
| `input_cost_per_image` | `image` | Cost per input image |
| `output_cost_per_reasoning_token` | `internal_reasoning` | Cost per reasoning token |

### Informational Fields

Some OpenRouter API pricing fields generate warnings but don't require configuration updates:

| OpenRouter API Field | Status | Description |
|---------------------|--------|-------------|
| `web_search` | Warning only | Web search cost - not tracked by LiteLLM |

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Generated with assistance from [aider.chat](https://github.com/Aider-AI/aider/)
- Uses the [OpenRouter API](https://openrouter.ai/docs#models) for pricing data
- Built for use with [LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start)
