from __future__ import annotations

import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from services.strategy.ActivityScoreService import ActivityScoreService
from services.indicator.InstitutionScanService import InstitutionScanService
from services.indicator.TurnoverScanService import TurnoverScanService
from services.indicator.VolumeRatioScanService import VolumeRatioScanService
from services.data.StockDataService import StockDataService
from services.data.DataBaseService import DataBaseService

_INITIALIZED = False

def initialize(srvs) -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    YomkApi.init()
    
    cur_srvs = {
        "StockDataService": StockDataService,
        "DataBaseService": DataBaseService,
        "VolumeRatioScanService": VolumeRatioScanService,
        "TurnoverScanService": TurnoverScanService,
        "InstitutionScanService": InstitutionScanService,
        "ActivityScoreService": ActivityScoreService,
    }
    
    for srv_name in srvs:
        if srv_name in cur_srvs:
            YomkApi.new_service(cur_srvs[srv_name], f"/{srv_name}")
        
    _INITIALIZED = True

