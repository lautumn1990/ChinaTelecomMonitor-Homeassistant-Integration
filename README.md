# 这是一个基于[ChinaTelecomMonitor](https://github.com/Cp0204/ChinaTelecomMonitor)接口返回数据制作的homeassistant电信话费集成
## 本集成由AI参与生成
在使用前你需要通过docker部署其API：
<br/>
效果展示：
<br/>
UI配置框：

![image](https://github.com/user-attachments/assets/172ec865-5385-49d7-8733-e7cb6649aea7)

实际效果：

![image](https://github.com/user-attachments/assets/8f37a781-aaaa-4029-9b3d-c4b87e74674d)

API部署方式在此贴一个例子：

> ### 命令行部署：
```shell
docker run -d \
  --name china-telecom-monitor \
  -p 10000:10000 \
  -v /mnt/data/supervisor/homeassistant/china-telecom-monitor/:/app/config \
  -v /etc/localtime:/etc/localtime \
  -e WHITELIST_NUM=189xxxxxxxx \
  --network bridge \
  --restart unless-stopped \
  cp0204/chinatelecommonitor:main
```
> ### compose部署:
```shell
services:
  china-telecom-monitor:
    image: cp0204/chinatelecommonitor:main
    container_name: china-telecom-monitor
    restart: unless-stopped
    ports:
      - "10000:10000"
    volumes:
      - ./config:/app/config
      - /etc/localtime:/etc/localtime
    environment:
      - WHITELIST_NUM=189xxxxxxxx
    network_mode: bridge
```
WHITELIST_NUM为号码白名单，填写对应要查询的
号码，多个以,分隔

## 接下来是如何食用本集成：

安装步骤

✅ 方法一：通过 HACS 安装（推荐）
打开 Home Assistant 左侧菜单，点击 HACS

进入右上角菜单 → 选择 “自定义存储库”

填入仓库地址：https://github.com/lautumn1990/ChinaTelecomMonitor-Homeassistant-Integration


类型选择 集成 (Integration)，点击添加

返回 HACS 主界面，搜索并安装 “CTM电信”

安装完成后，前往 “设置 → 设备与服务 → 添加集成”

搜索 CTM电信，点击添加并完成配置

[![快速通过 HACS 链接安装](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hlhk2017&repository=ChinaTelecomMonitor-Homeassistant-Integration&category=integration)

 方法二：手动安装
下载项目源代码或 Release 包

将目录整体复制到 Home Assistant 的路径：

config/custom_components/china_telecom

重启 Home Assistant
<br/>
前往 “设置 → 设备与服务 → 添加集成”
<br/>
搜索 CTM电信，点击添加并完成配置

## 原始仓库地址

[ChinaTelecomMonitor-Homeassistant-Integration](https://github.com/hlhk2017/ChinaTelecomMonitor-Homeassistant-Integration)
