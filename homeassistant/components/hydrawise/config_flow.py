"""Config flow for the Hydrawise integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aiohttp import ClientError
from pydrawise import legacy
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.data_entry_flow import AbortFlow, FlowResultType
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from .const import DOMAIN, LOGGER


class HydrawiseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hydrawise."""

    VERSION = 1

    async def _create_entry(
        self, api_key: str, *, on_failure: Callable[[str], ConfigFlowResult]
    ) -> ConfigFlowResult:
        """Create the config entry."""
        api = legacy.LegacyHydrawiseAsync(api_key)
        try:
            # Skip fetching zones to save on metered API calls.
            user = await api.get_user(fetch_zones=False)
        except TimeoutError:
            return on_failure("timeout_connect")
        except ClientError as ex:
            LOGGER.error("Unable to connect to Hydrawise cloud service: %s", ex)
            return on_failure("cannot_connect")

        await self.async_set_unique_id(f"hydrawise-{user.customer_id}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="Hydrawise", data={CONF_API_KEY: api_key})

    def _import_issue(self, error_type: str) -> ConfigFlowResult:
        """Create an issue about a YAML import failure."""
        async_create_issue(
            self.hass,
            DOMAIN,
            f"deprecated_yaml_import_issue_{error_type}",
            breaks_in_ha_version="2024.4.0",
            is_fixable=False,
            severity=IssueSeverity.ERROR,
            translation_key="deprecated_yaml_import_issue",
            translation_placeholders={
                "error_type": error_type,
                "url": "/config/integrations/dashboard/add?domain=hydrawise",
            },
        )
        return self.async_abort(reason=error_type)

    def _deprecated_yaml_issue(self) -> None:
        """Create an issue about YAML deprecation."""
        async_create_issue(
            self.hass,
            HOMEASSISTANT_DOMAIN,
            f"deprecated_yaml_{DOMAIN}",
            breaks_in_ha_version="2024.4.0",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=IssueSeverity.WARNING,
            translation_key="deprecated_yaml",
            translation_placeholders={
                "domain": DOMAIN,
                "integration_title": "Hydrawise",
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup."""
        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            return await self._create_entry(api_key, on_failure=self._show_form)
        return self._show_form()

    def _show_form(self, error_type: str | None = None) -> ConfigFlowResult:
        errors = {}
        if error_type is not None:
            errors["base"] = error_type
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import data from YAML."""
        try:
            result = await self._create_entry(
                import_data.get(CONF_API_KEY, ""),
                on_failure=self._import_issue,
            )
        except AbortFlow:
            self._deprecated_yaml_issue()
            raise

        if result["type"] == FlowResultType.CREATE_ENTRY:
            self._deprecated_yaml_issue()
        return result
