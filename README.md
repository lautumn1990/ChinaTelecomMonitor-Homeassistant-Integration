# 这是一个基于[ChinaTelecomMonitor](https://github.com/Cp0204/ChinaTelecomMonitor)接口返回数据制作的homeassistant电信话费集成
在使用前你需要通过docker部署其API：

其部属方式在此贴一个例子：

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
下载集成文件，解压后丢到你homeassistant的/config/custom_components/  路径下。
重启ha，然后在添加集成搜索电信即可看见
按提示输入API地址，号码和密码即可
UI配置框：
![image](https://github.com/user-attachments/assets/172ec865-5385-49d7-8733-e7cb6649aea7)
实际效果：
![image](https://github.com/user-attachments/assets/8f37a781-aaaa-4029-9b3d-c4b87e74674d)

