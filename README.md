# LiteLLM Proxy OpenRouter Price Updater

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A CLI tool that compares local OpenRouter model pricing in LiteLLM proxy configuration files with the actual pricing from OpenRouter's API. This helps maintain accurate cost tracking by identifying missing or outdated pricing information.

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

### Example Output

```
2024-01-15 10:30:12.345 | INFO     | Fetched 150 models from OpenRouter API
2024-01-15 10:30:12.456 | INFO     | Found 5 OpenRouter models in config
2024-01-15 10:30:12.567 | INFO     | Checking model: GPT-4 Turbo (openrouter/openai/gpt-4-turbo)
2024-01-15 10:30:12.678 | SUCCESS  | Pricing is up to date for GPT-4 Turbo
2024-01-15 10:30:12.789 | WARNING  | Pricing issues for Claude 3:
2024-01-15 10:30:12.890 |          |   - Missing cache_read_input_token_cost: should be 0.000001
2024-01-15 10:30:12.991 |          |   - output_cost_per_token mismatch: local=0.000015, API=0.000016
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
```

### Exit Codes

- `0`: All pricing is up to date
- `1`: Pricing discrepancies found or error occurred

This makes the tool suitable for use in CI/CD pipelines to catch pricing configuration drift.

## Development

### Running Tests

```bash
# TODO: Add test framework and commands
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Error Handling

The tool handles various error conditions gracefully:

- **Missing config file**: Clear error message with file path
- **Invalid YAML**: Detailed parsing error information  
- **API failures**: Network timeout and HTTP error handling
- **Missing models**: Warning when local models aren't found in API

## Pricing Fields Supported

| Local Config Field | OpenRouter API Field | Description |
|-------------------|---------------------|-------------|
| `input_cost_per_token` | `prompt` | Cost per input token |
| `output_cost_per_token` | `completion` | Cost per output token |
| `cache_creation_input_token_cost` | `input_cache_write` | Cost to write to cache |
| `cache_read_input_token_cost` | `input_cache_read` | Cost to read from cache |

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Generated with assistance from [aider.chat](https://github.com/Aider-AI/aider/)
- Uses the [OpenRouter API](https://openrouter.ai/docs#models) for pricing data
- Built for use with [LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start)
