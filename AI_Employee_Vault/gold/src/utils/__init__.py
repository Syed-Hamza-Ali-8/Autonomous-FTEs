"""
Utility Functions for Gold Tier

Common utilities used across the Gold Tier implementation.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "detailed"
) -> None:
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format style (simple, detailed, json)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format == "simple":
        format_str = "%(levelname)s - %(message)s"
    elif log_format == "json":
        format_str = '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
    else:  # detailed
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Args:
        env_file: Path to .env file (optional)

    Returns:
        Dictionary with configuration values
    """
    # Load .env file if specified
    if env_file:
        load_dotenv(env_file)
    else:
        # Try to find .env in gold directory
        gold_dir = Path(__file__).parent.parent.parent
        env_path = gold_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    return {
        # General
        "environment": os.getenv("ENVIRONMENT", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "vault_path": os.getenv("VAULT_PATH", "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"),

        # Xero
        "xero_client_id": os.getenv("XERO_CLIENT_ID"),
        "xero_client_secret": os.getenv("XERO_CLIENT_SECRET"),
        "xero_redirect_uri": os.getenv("XERO_REDIRECT_URI"),
        "xero_tenant_id": os.getenv("XERO_TENANT_ID"),

        # Facebook
        "facebook_access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
        "facebook_page_id": os.getenv("FACEBOOK_PAGE_ID"),

        # Instagram
        "instagram_business_account_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"),

        # Twitter
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "twitter_access_secret": os.getenv("TWITTER_ACCESS_SECRET"),
        "twitter_bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),

        # Error Recovery
        "max_retry_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
        "base_retry_delay": float(os.getenv("BASE_RETRY_DELAY", "1.0")),
        "max_retry_delay": float(os.getenv("MAX_RETRY_DELAY", "60.0")),

        # Audit Logging
        "audit_log_retention_days": int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "90")),
        "audit_log_path": os.getenv("AUDIT_LOG_PATH"),

        # Health Monitoring
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
        "mcp_timeout": int(os.getenv("MCP_TIMEOUT", "5")),

        # CEO Briefing
        "ceo_briefing_schedule": os.getenv("CEO_BRIEFING_SCHEDULE", "0 7 * * 0"),
        "ceo_briefing_path": os.getenv("CEO_BRIEFING_PATH"),
        "revenue_target_monthly": float(os.getenv("REVENUE_TARGET_MONTHLY", "10000")),

        # Mock Data
        "use_mock_xero": os.getenv("USE_MOCK_XERO", "true").lower() == "true",
    }


def get_vault_path() -> Path:
    """Get vault path from environment or default"""
    config = load_config()
    return Path(config["vault_path"])


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't"""
    path.mkdir(parents=True, exist_ok=True)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(value: float) -> str:
    """Format percentage value"""
    return f"{value:.1f}%"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
