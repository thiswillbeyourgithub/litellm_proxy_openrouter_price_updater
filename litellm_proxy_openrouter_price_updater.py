#!/usr/bin/env python3
"""
LiteLLM Proxy OpenRouter Price Updater

This script compares local OpenRouter model pricing in a LiteLLM config file
with the actual pricing from OpenRouter's API. It identifies missing or
outdated pricing information to help maintain accurate cost tracking.

Generated with assistance from aider.chat
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import yaml
import click
from loguru import logger


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Parameters
    ----------
    config_path : str
        Path to the YAML configuration file

    Returns
    -------
    Dict[str, Any]
        Parsed configuration data

    Raises
    ------
    FileNotFoundError
        If config file doesn't exist
    yaml.YAMLError
        If config file is invalid YAML
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")


def fetch_openrouter_models() -> Dict[str, Dict[str, Any]]:
    """
    Fetch model pricing data from OpenRouter API.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Dictionary mapping model IDs to their full model data

    Raises
    ------
    requests.RequestException
        If API request fails
    """
    url = "https://openrouter.ai/api/v1/models"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Create a lookup dictionary by model ID
        models = {}
        for model in data.get("data", []):
            models[model["id"]] = model

        logger.info(f"Fetched {len(models)} models from OpenRouter API")
        return models

    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch OpenRouter models: {e}")


def extract_openrouter_models(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract models that use OpenRouter from the config.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration data

    Returns
    -------
    List[Dict[str, Any]]
        List of model configurations that use OpenRouter
    """
    openrouter_models = []

    for model in config.get("model_list", []):
        litellm_params = model.get("litellm_params", {})
        model_id = litellm_params.get("model", "")

        if model_id.startswith("openrouter/"):
            openrouter_models.append(model)

    logger.info(f"Found {len(openrouter_models)} OpenRouter models in config")
    return openrouter_models


def compare_pricing(
    local_model: Dict[str, Any], api_model: Dict[str, Any]
) -> List[str]:
    """
    Compare local model pricing with API pricing.

    Parameters
    ----------
    local_model : Dict[str, Any]
        Local model configuration
    api_model : Dict[str, Any]
        Model data from OpenRouter API

    Returns
    -------
    List[str]
        List of pricing discrepancies found
    """
    discrepancies = []
    litellm_params = local_model.get("litellm_params", {})
    api_pricing = api_model.get("pricing", {})

    # Mapping of local keys to API keys
    price_mappings = {
        "input_cost_per_token": "prompt",
        "output_cost_per_token": "completion",
        "cache_creation_input_token_cost": "input_cache_write",
        "cache_read_input_token_cost": "input_cache_read",
    }

    for local_key, api_key in price_mappings.items():
        local_value = litellm_params.get(local_key)
        api_value = api_pricing.get(api_key)

        if local_value is None:
            if api_value and float(api_value) > 0:
                discrepancies.append(f"Missing {local_key}: should be {api_value}")
        else:
            if api_value is None:
                discrepancies.append(
                    f"{local_key} set to {local_value} but API has no {api_key}"
                )
            else:
                local_float = float(local_value)
                api_float = float(api_value)

                # Compare with small tolerance for floating point precision
                if abs(local_float - api_float) > 1e-10:
                    discrepancies.append(
                        f"{local_key} mismatch: local={local_value}, API={api_value}"
                    )

    return discrepancies


def check_model_pricing(
    config: Dict[str, Any], api_models: Dict[str, Dict[str, Any]]
) -> None:
    """
    Check pricing for all OpenRouter models in config against API data.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration data
    api_models : Dict[str, Dict[str, Any]]
        Model data from OpenRouter API
    """
    openrouter_models = extract_openrouter_models(config)

    if not openrouter_models:
        logger.info("No OpenRouter models found in config")
        return

    total_issues = 0

    for model in openrouter_models:
        model_name = model.get("model_name", "Unknown")
        litellm_params = model.get("litellm_params", {})
        model_id = litellm_params.get("model", "")

        # Strip "openrouter/" prefix to match API model IDs
        api_model_id = model_id.replace("openrouter/", "", 1)

        logger.info(f"Checking model: {model_name} ({model_id})")

        if api_model_id not in api_models:
            logger.warning(f"Model {api_model_id} not found in OpenRouter API")
            total_issues += 1
            continue

        api_model = api_models[api_model_id]
        discrepancies = compare_pricing(model, api_model)

        if discrepancies:
            logger.warning(f"Pricing issues for {model_name}:")
            for discrepancy in discrepancies:
                logger.warning(f"  - {discrepancy}")
            total_issues += len(discrepancies)
        else:
            logger.success(f"Pricing is up to date for {model_name}")

    if total_issues > 0:
        logger.error(f"Found {total_issues} pricing issues total")
        sys.exit(1)
    else:
        logger.success("All OpenRouter model pricing is up to date!")


@click.command()
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="Path to the YAML configuration file",
)
def main(config: str) -> None:
    """
    Update OpenRouter model pricing in LiteLLM proxy configuration.

    This script compares local pricing configuration with OpenRouter API
    pricing and reports any discrepancies or missing values.
    """
    logger.info("Starting OpenRouter price updater")

    try:
        # Load configuration
        logger.info(f"Loading config from: {config}")
        config_data = load_config(config)

        # Fetch API data
        logger.info("Fetching models from OpenRouter API...")
        api_models = fetch_openrouter_models()

        # Check pricing
        logger.info("Comparing local pricing with API pricing...")
        check_model_pricing(config_data, api_models)

    except (FileNotFoundError, yaml.YAMLError, requests.RequestException) as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
