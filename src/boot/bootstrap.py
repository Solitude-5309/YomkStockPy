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

_INITIALIZED = False

def initialize() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
    YomkApi.new_service(VolumeRatioScanService, "/VolumeRatioScanService")
    YomkApi.new_service(TurnoverScanService, "/TurnoverScanService")
    YomkApi.new_service(InstitutionScanService, "/InstitutionScanService")
    YomkApi.new_service(ActivityScoreService, "/ActivityScoreService")
    _INITIALIZED = True

