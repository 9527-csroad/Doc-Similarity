import json
import logging
from pathlib import Path

from datetime import datetime
from .client import NacosClient, NacosException, DEFAULTS, DEFAULT_GROUP_NAME
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_cfg = Path(__file__).resolve().parents[3] / "nacosConfig.json"
if not _cfg.is_file():
    _cfg = Path(__file__).resolve().parent / "nacosConfig.json"
with open(_cfg, "r", encoding="utf-8") as nacosConfigJsonFile:
    nacosConfigJson = json.load(nacosConfigJsonFile)
logger.info("nacos config: %s", _cfg)

# 初始化nacos客户端
client = NacosClient(nacosConfigJson['server_addresses']
                           , namespace=nacosConfigJson['namespace']
                           , username=nacosConfigJson['username']
                           , password=nacosConfigJson['password'])

metadata = json.dumps(nacosConfigJson["metadata"])
metadataDict = {"aiServerInfo": metadata}


def registerService():
    metadataDict["startTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client.add_naming_instance(
        nacosConfigJson['ai_server_name']
        , nacosConfigJson['ai_server_ip']
        , nacosConfigJson['ai_server_port']
        , metadata=metadataDict
        , group_name=nacosConfigJson['group_name'])

_scheduler = None


def sendHeartbeatJob():
    global _scheduler
    if _scheduler is not None:
        return

    def sendHeartbeat():
        client.add_naming_instance(
            nacosConfigJson['ai_server_name']
            , nacosConfigJson['ai_server_ip']
            , nacosConfigJson['ai_server_port']
            , metadata=metadataDict
            , group_name=nacosConfigJson['group_name'])

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    _scheduler.add_job(sendHeartbeat, 'interval', seconds=5)
    _scheduler.start()


def shutdown_heartbeat():
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    finally:
        _scheduler = None
