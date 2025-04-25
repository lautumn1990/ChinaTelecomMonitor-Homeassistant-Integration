import logging
import asyncio
import aiohttp
from datetime import timedelta
import uuid
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN, CONF_API_URL, CONF_PHONENUM, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the China Telecom sensors."""
    api_url = entry.data[CONF_API_URL]
    phonenum = entry.data[CONF_PHONENUM]
    password = entry.data[CONF_PASSWORD]

    coordinator = ChinaTelecomDataUpdateCoordinator(
        hass, api_url, phonenum, password
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        return

    device_id = str(uuid.uuid4())
    sensors = []
    # 余额信息
    sensors.append(ChinaTelecomSensor(coordinator, "balance", "电信账户余额", "¥", "mdi:cash", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "currentMonthCost", "电信本月消费", "¥", "mdi:cash-clock", device_id))
    # 流量信息
    sensors.append(ChinaTelecomSensor(coordinator, "totalGB", "流量总量", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "usedGB", "流量已用", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "remainingGB", "流量剩余", "GB", "mdi:network", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "percentUsed", "流量使用率", "%", "mdi:percent", device_id))
    # 通话信息
    sensors.append(ChinaTelecomSensor(coordinator, "totalMinutes", "通话总量", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "usedMinutes", "通话已用", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "remainingMinutes", "通话剩余", "分钟", "mdi:phone", device_id))
    sensors.append(ChinaTelecomSensor(coordinator, "voicePercentUsed", "通话使用率", "%", "mdi:percent", device_id))
    # 积分信息
    sensors.append(ChinaTelecomSensor(coordinator, "points", "电信积分", "", "mdi:star", device_id))

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
                    login_data = await response.json()
                    phone_nbr = login_data["responseData"]["data"]["loginSuccessResult"]["phoneNbr"]

            # 获取数据
            query_url = f"{self.api_url}/qryImportantData?phonenum={self.phonenum}&password={self.password}"
            async with aiohttp.ClientSession() as session:
                async with session.get(query_url) as response:
                    data = await response.json()
                    data = data["responseData"]["data"]

                    # 话费余额信息
                    balance_info = {
                        "balance": float(data["balanceInfo"]["indexBalanceDataInfo"]["balance"]),
                        "arrear": float(data["balanceInfo"]["indexBalanceDataInfo"]["arrear"]),
                        "currentMonthCost": float(data["balanceInfo"]["phoneBillRegion"]["subTitleHh"].replace('元', ''))
                    }

                    # 流量数据处理
                    flow_info = {
                        "totalGB": float(
                            (int(data["flowInfo"]["totalAmount"]["total"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2)),
                        "usedGB": float(
                            (int(data["flowInfo"]["totalAmount"]["used"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2)),
                        "remainingGB": float(
                            (int(data["flowInfo"]["totalAmount"]["balance"].replace(r'[^0-9]', '')) / 1024 / 1024).__round__(2)),
                        "percentUsed": int(data["flowInfo"]["flowList"][0]["barPercent"].replace('%', ''))
                    }

                    # 语音信息
                    voice_info = {
                        "totalMinutes": int(data["voiceInfo"]["voiceDataInfo"]["total"]),
                        "usedMinutes": int(data["voiceInfo"]["voiceDataInfo"]["used"]),
                        "remainingMinutes": int(data["voiceInfo"]["voiceDataInfo"]["balance"]),
                        "percentUsed": data["voiceInfo"]["voiceBars"][0]["barPercent"]
                    }
                    voice_info["voicePercentUsed"] = 100 - (
                            voice_info["remainingMinutes"] / voice_info["totalMinutes"] * 100).__round__(1)

                    # 积分信息
                    points = int(data["integralInfo"]["integral"])

                    return {
                        **balance_info,
                        **flow_info,
                        **voice_info,
                        "points": points
                    }
        except Exception as error:
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
        self._unique_id = f"{device_id}_{key}"

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
            "name": "中国电信设备",
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
    
