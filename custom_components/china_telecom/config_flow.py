import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_API_URL, CONF_PHONENUM, CONF_PASSWORD, DOMAIN
import re

# 验证 API URL 的格式
def validate_api_url(url):
    pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    if not pattern.match(url):
        raise vol.Invalid("无效的 API URL，请输入有效的 URL 地址")
    return url

# 验证手机号码的格式
def validate_phone_number(phone):
    pattern = re.compile(r'^\d{11}$')
    if not pattern.match(phone):
        raise vol.Invalid("无效的手机号码，请输入 11 位数字的手机号码")
    return phone

class ChinaTelecomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                # 验证用户输入
                user_input[CONF_API_URL] = validate_api_url(user_input[CONF_API_URL])
                user_input[CONF_PHONENUM] = validate_phone_number(user_input[CONF_PHONENUM])

                # 检查是否已经配置过该手机号码
                await self.async_set_unique_id(user_input[CONF_PHONENUM])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="中国电信", data=user_input
                )
            except vol.Invalid as e:
                errors["base"] = str(e)
            except Exception as e:
                errors["base"] = "配置过程中出现未知错误，请重试"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_URL): str,
                    vol.Required(CONF_PHONENUM): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={"name": "中国电信"}
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        try:
            # 验证导入的配置
            import_config[CONF_API_URL] = validate_api_url(import_config[CONF_API_URL])
            import_config[CONF_PHONENUM] = validate_phone_number(import_config[CONF_PHONENUM])

            await self.async_set_unique_id(import_config[CONF_PHONENUM])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="中国电信 (导入)", data=import_config
            )
        except vol.Invalid as e:
            _LOGGER.error(f"从配置文件导入时出现错误: {str(e)}")
        except Exception as e:
            _LOGGER.error(f"从配置文件导入时出现未知错误: {str(e)}")
        return self.async_abort(reason="import_failed")
    
