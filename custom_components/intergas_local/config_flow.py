from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, build_resource_url

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="10.20.30.1"): str,
        vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class XtendConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                resource = build_resource_url(user_input["host"])
            except ValueError:
                errors["base"] = "invalid_host"
                return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

            await self.async_set_unique_id(resource)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Intergas Local",
                data={
                    "host": user_input["host"],
                    "resource": resource,
                    "scan_interval": user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                },
            )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return XtendOptionsFlowHandler()


class XtendOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan = self.config_entry.options.get(
            "scan_interval",
            self.config_entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("scan_interval", default=current_scan): int,
                }
            ),
        )
