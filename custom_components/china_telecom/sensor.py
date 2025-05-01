import logging
import asyncio
import aiohttp
from datetime import timedelta
import uuid
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN, CONF_API_URL, CONF_PHONENUM, CONF_PASSWORD, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the China Telecom sensors."""
    api_url = entry.data[CONF_API_URL]
    phonenum = entry.data[CONF_PHONENUM]
    password = entry.data[CONF_PASSWORD]

    # 检查配置项中是否有 device_id，如果没有则生成并保存
    if CONF_DEVICE_ID not in entry.data:
        device_id = str(uuid.uuid4())
        new_data = {**entry.data, CONF_DEVICE_ID: device_id}
        hass.config_entries.async_update_entry(entry, data=new_data)
    else:
        device_id = entry.data[CONF_DEVICE_ID]

    coordinator = ChinaTelecomDataUpdateCoordinator(
        hass, api_url, phonenum, password
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        return

    masked_phonenum = f"{phonenum[:3]}****{phonenum[7:]}"

    sensors = []
    # 余额信息
    sensors.append(ChinaTelecomSensor(coordinator, "balance", f"{masked_phonenum} 电信账户余额", "¥", "mdi:cash", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "currentMonthCost", f"{masked_phonenum} 电信本月消费", "¥", "mdi:cash-clock", device_id))
    # 流量信息
    sensors.append(ChinaTelecomSensor(coordinator, "totalGB", f"{masked_phonenum} 流量总量", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "usedGB", f"{masked_phonenum} 流量已用", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "remainingGB", f"{masked_phonenum} 流量剩余", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "percentUsed", f"{masked_phonenum} 流量使用率", "%", "mdi:percent", device_id))
    # 通话信息
    sensors.append(ChinaTelecomSensor(coordinator, "totalMinutes", f"{masked_phonenum} 通话总量", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "usedMinutes", f"{masked_phonenum} 通话已用", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "remainingMinutes", f"{masked_phonenum} 通话剩余", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "voicePercentUsed", f"{masked_phonenum} 通话使用率", "%", "mdi:percent", device_id))
    # 积分信息
    sensors.append(ChinaTelecomSensor(coordinator, "points", f"{masked_phonenum} 电信积分", "", "mdi:star", device_id))

    async_add_entities(sensors)


class ChinaTelecomDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching China Telecom data."""

    def __init__(self, hass, api_url, phonenum, password):
        """Initialize."""
        self.api_url = api_url
        self.phonenum = phonenum
        self.password = password
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self):
        """Update data via API."""
        try:
            # 先登录
            login_url = f"{self.api_url}/login?phonenum={self.phonenum}&password={self.password}"
            async with aiohttp.ClientSession() as session:
                async with session.get(login_url) as response:
                    if response.status != 200:
                        _LOGGER.warning(f"Login request failed with status code {response.status}, but continuing...")
                        # 可以在这里添加一些处理逻辑，例如使用默认数据或跳过登录相关步骤
                        phone_nbr = None
                    else:
                        try:
                            login_data = await response.json()
                        except ValueError as e:
                            _LOGGER.error(f"Failed to parse login response as JSON: {e}")
                            raise UpdateFailed(f"Failed to parse login response as JSON: {e}")
                        if "responseData" not in login_data or "data" not in login_data["responseData"] or "loginSuccessResult" not in login_data["responseData"]["data"]:
                            _LOGGER.error("Login response does not contain expected data structure")
                            raise UpdateFailed("Login response does not contain expected data structure")
                        phone_nbr = login_data["responseData"]["data"]["loginSuccessResult"]["phoneNbr"]

            # 获取数据
            query_url = f"{self.api_url}/qryImportantData?phonenum={self.phonenum}&password={self.password}"
            async with aiohttp.ClientSession() as session:
                async with session.get(query_url) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Query request failed with status code {response.status}")
                        raise UpdateFailed(f"Query request failed with status code {response.status}")
                    try:
                        data = await response.json()
                    except ValueError as e:
                        _LOGGER.error(f"Failed to parse query response as JSON: {e}")
                        raise UpdateFailed(f"Failed to parse query response as JSON: {e}")
                    if "responseData" not in data or "data" not in data["responseData"]:
                        _LOGGER.error("Query response does not contain expected data structure")
                        raise UpdateFailed("Query response does not contain expected data structure")
                    data = data["responseData"]["data"]

                    # 话费余额信息
                    if "balanceInfo" not in data or "indexBalanceDataInfo" not in data["balanceInfo"] or "phoneBillRegion" not in data["balanceInfo"]:
                        _LOGGER.error("Balance information is missing in the query response")
                        raise UpdateFailed("Balance information is missing in the query response")
                    try:
                        balance_info = {
                            "balance": float(data["balanceInfo"]["indexBalanceDataInfo"]["balance"]),
                            "arrear": float(data["balanceInfo"]["indexBalanceDataInfo"]["arrear"]),
                            "currentMonthCost": float(data["balanceInfo"]["phoneBillRegion"]["subTitleHh"].replace('元', ''))
                        }
                    except ValueError as e:
                        _LOGGER.error(f"Failed to convert balance information to float: {e}")
                        balance_info = {
                            "balance": 0.0,
                            "arrear": 0.0,
                            "currentMonthCost": 0.0
                        }

                    # 流量数据处理
                    if "flowInfo" not in data or "totalAmount" not in data["flowInfo"]:
                        _LOGGER.error("Flow information is missing in the query response")
                        raise UpdateFailed("Flow information is missing in the query response")
                    try:
                        total_gb = float(
                            (int(data["flowInfo"]["totalAmount"]["total"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2))
                        used_gb = float(
                            (int(data["flowInfo"]["totalAmount"]["used"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2))
                        remaining_gb = float(
                            (int(data["flowInfo"]["totalAmount"]["balance"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2))
                    except ValueError as e:
                        _LOGGER.error(f"Failed to convert flow information to float: {e}")
                        total_gb = 0.0
                        used_gb = 0.0
                        remaining_gb = 0.0
                    # 避免 total_gb 为 0 时计算错误
                    if total_gb > 0:
                        flow_percent_used = 100 - (remaining_gb / total_gb * 100).__round__(1)
                    else:
                        flow_percent_used = 0
                    flow_info = {
                        "totalGB": total_gb,
                        "usedGB": used_gb,
                        "remainingGB": remaining_gb,
                        "percentUsed": flow_percent_used
                    }

                    # 语音信息
                    if "voiceInfo" not in data or "voiceDataInfo" not in data["voiceInfo"]:
                        _LOGGER.error("Voice information is missing in the query response")
                        raise UpdateFailed("Voice information is missing in the query response")
                    try:
                        total_minutes = int(data["voiceInfo"]["voiceDataInfo"]["total"])
                        used_minutes = int(data["voiceInfo"]["voiceDataInfo"]["used"])
                        remaining_minutes = int(data["voiceInfo"]["voiceDataInfo"]["balance"])
                    except ValueError as e:
                        _LOGGER.error(f"Failed to convert voice information to int: {e}")
                        total_minutes = 0
                        used_minutes = 0
                        remaining_minutes = 0
                    # 避免 total_minutes 为 0 时计算错误
                    if total_minutes > 0:
                        voice_percent_used = 100 - (remaining_minutes / total_minutes * 100).__round__(1)
                    else:
                        voice_percent_used = 0
                    voice_info = {
                        "totalMinutes": total_minutes,
                        "usedMinutes": used_minutes,
                        "remainingMinutes": remaining_minutes,
                        "voicePercentUsed": voice_percent_used
                    }

                    # 积分信息
                    if "integralInfo" not in data:
                        _LOGGER.error("Integral information is missing in the query response")
                        raise UpdateFailed("Integral information is missing in the query response")
                    try:
                        points = int(data["integralInfo"]["integral"])
                    except ValueError as e:
                        _LOGGER.error(f"Failed to convert points to int: {e}")
                        points = 0

                    return {
                        **balance_info,
                        **flow_info,
                        **voice_info,
                        "points": points
                    }
        except Exception as error:
            _LOGGER.error(f"Error fetching data: {error}")
            raise UpdateFailed(f"Error fetching data: {error}")


class ChinaTelecomSensor(Entity):
    """Representation of a China Telecom sensor."""

    def __init__(self, coordinator, key, name, unit, icon, device_id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.key = key
        self._name = name
        self._unit = unit
        self._icon = icon
        self._device_id = device_id
        self.masked_phonenum = name.split(" ")[0]  # 提取隐去中间四位的号码
        self._unique_id = f"{self.masked_phonenum}_{device_id}_{key}"  # 在实体 ID 中添加号码

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.key)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"{self.masked_phonenum} 套餐信息",
            "manufacturer": "中国电信",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()
