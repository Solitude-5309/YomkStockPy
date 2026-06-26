from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import YomkApi


@dataclass(frozen=True)
class ScanConfig:
    lookback_days: int = 20
    inactive_days: int = 5
    volume_ratio_threshold: float = 1.8
    turnover_threshold: float = 3.0
    inactive_volume_ratio_max: float = 1.0
    inactive_turnover_max: float = 1.5
    volume_weight: float = 0.6
    turnover_weight: float = 0.4
    min_score: float = 70.0
    cooldown_days: int = 10

    @classmethod
    def from_pkg(cls, pkg: Any) -> "ScanConfig":
        config = {}
        if isinstance(pkg, dict):
            config = dict(pkg.get("config") or {})

        values = {}
        for field_name in cls.__dataclass_fields__:
            if field_name in config:
                values[field_name] = config[field_name]

        parsed = cls(**values)
        return ScanConfig(
            lookback_days=max(1, int(parsed.lookback_days)),
            inactive_days=max(1, int(parsed.inactive_days)),
            volume_ratio_threshold=max(0.01, float(parsed.volume_ratio_threshold)),
            turnover_threshold=max(0.01, float(parsed.turnover_threshold)),
            inactive_volume_ratio_max=max(0.0, float(parsed.inactive_volume_ratio_max)),
            inactive_turnover_max=max(0.0, float(parsed.inactive_turnover_max)),
            volume_weight=max(0.0, float(parsed.volume_weight)),
            turnover_weight=max(0.0, float(parsed.turnover_weight)),
            min_score=max(0.0, float(parsed.min_score)),
            cooldown_days=max(0, int(parsed.cooldown_days)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "lookback_days": self.lookback_days,
            "inactive_days": self.inactive_days,
            "volume_ratio_threshold": self.volume_ratio_threshold,
            "turnover_threshold": self.turnover_threshold,
            "inactive_volume_ratio_max": self.inactive_volume_ratio_max,
            "inactive_turnover_max": self.inactive_turnover_max,
            "volume_weight": self.volume_weight,
            "turnover_weight": self.turnover_weight,
            "min_score": self.min_score,
            "cooldown_days": self.cooldown_days,
        }


class ActiveDateScanService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/ActiveDateScanService")

    def init(self):
        self.install_func("/scan", self.scan)

    def scan(self, pkg: Any) -> YomkApi.YomkResponse:
        try:
            df = self._extract_dataframe(pkg)
            config = ScanConfig.from_pkg(pkg)
            prepared = self._prepare_dataframe(df)
            events = self._find_active_starts(prepared, config)
            return YomkApi.YomkResponse(
                YomkApi.ResStatus.eOk,
                "active dates scanned",
                {
                    "count": len(events),
                    "events": events,
                    "input_rows": len(prepared),
                    "config": config.as_dict(),
                },
            )
        except ValueError as exc:
            return YomkApi.YomkResponse(YomkApi.ResStatus.eInvalid, str(exc), None)
        except Exception as exc:
            return YomkApi.YomkResponse(YomkApi.ResStatus.eErr, f"scan failed: {exc}", None)

    def _extract_dataframe(self, pkg: Any) -> pd.DataFrame:
        if isinstance(pkg, pd.DataFrame):
            return pkg
        if isinstance(pkg, dict):
            for key in ("df", "data", "table"):
                value = pkg.get(key)
                if isinstance(value, pd.DataFrame):
                    return value
                if isinstance(value, list):
                    return pd.DataFrame(value)
        raise ValueError("pkg must be a DataFrame or a dict containing df/data/table")

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            raise ValueError("input DataFrame is empty")

        required = {"date", "volume", "turn"}
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(f"input DataFrame missing columns: {', '.join(missing)}")

        prepared = df.copy()
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
        prepared["volume"] = pd.to_numeric(prepared["volume"], errors="coerce")
        prepared["turn"] = pd.to_numeric(prepared["turn"], errors="coerce")
        prepared = prepared.dropna(subset=["date", "volume", "turn"])
        prepared = prepared.sort_values("date").reset_index(drop=True)
        if prepared.empty:
            raise ValueError("input DataFrame has no valid date/volume/turn rows")
        return prepared

    def _find_active_starts(self, df: pd.DataFrame, config: ScanConfig) -> list[dict[str, Any]]:
        data = df.copy()
        previous_volume_avg = (
            data["volume"]
            .shift(1)
            .rolling(config.lookback_days, min_periods=config.lookback_days)
            .mean()
        )
        data["volume_ratio"] = data["volume"] / previous_volume_avg
        data["volume_ratio"] = data["volume_ratio"].replace([float("inf"), -float("inf")], pd.NA)

        prior_volume_ratio_max = (
            data["volume_ratio"]
            .shift(1)
            .rolling(config.inactive_days, min_periods=config.inactive_days)
            .max()
        )
        prior_turnover_max = (
            data["turn"]
            .shift(1)
            .rolling(config.inactive_days, min_periods=config.inactive_days)
            .max()
        )

        events: list[dict[str, Any]] = []
        last_event_position: int | None = None
        total_weight = config.volume_weight + config.turnover_weight
        if total_weight <= 0:
            total_weight = 1.0

        for position, row in data.iterrows():
            volume_ratio = row["volume_ratio"]
            if pd.isna(volume_ratio):
                continue

            previous_ratio_max = prior_volume_ratio_max.iloc[position]
            previous_turn_max = prior_turnover_max.iloc[position]
            if pd.isna(previous_ratio_max) or pd.isna(previous_turn_max):
                continue

            was_inactive = (
                float(previous_ratio_max) <= config.inactive_volume_ratio_max
                and float(previous_turn_max) <= config.inactive_turnover_max
            )
            volume_breakout = float(volume_ratio) >= config.volume_ratio_threshold
            turnover_breakout = float(row["turn"]) >= config.turnover_threshold
            volume_score = min(float(volume_ratio) / config.volume_ratio_threshold * 100.0, 100.0)
            turnover_score = min(float(row["turn"]) / config.turnover_threshold * 100.0, 100.0)
            score = (
                volume_score * config.volume_weight
                + turnover_score * config.turnover_weight
            ) / total_weight

            if not was_inactive or score < config.min_score:
                continue
            if not (volume_breakout or turnover_breakout):
                continue
            if last_event_position is not None and position - last_event_position <= config.cooldown_days:
                continue

            reasons = []
            if volume_breakout:
                reasons.append("量比突破")
            if turnover_breakout:
                reasons.append("换手率突破")

            events.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "position": int(position),
                    "volume": float(row["volume"]),
                    "turnover": round(float(row["turn"]), 4),
                    "volume_ratio": round(float(volume_ratio), 4),
                    "previous_volume_ratio_max": round(float(previous_ratio_max), 4),
                    "previous_turnover_max": round(float(previous_turn_max), 4),
                    "score": round(float(score), 2),
                    "trend_status": "开始活跃",
                    "reason": "、".join(reasons),
                }
            )
            last_event_position = int(position)

        return events
