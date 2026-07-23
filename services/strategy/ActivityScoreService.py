from __future__ import annotations

from typing import Any

import YomkApi

from utils.utils import error, extract_config, extract_dataframe, invalid, ok


class ActivityScoreService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/ActivityScoreService")

    def init(self):
        self.install_func("/scan", self.scan)

    def scan(self, pkg: Any) -> YomkApi.YomkResponse:
        try:
            df = extract_dataframe(pkg)
            config = extract_config(pkg)
            weights = self._weights(config)
            active_score_threshold = float(config.get("active_score_threshold", 70.0))
            inactive_score_threshold = float(config.get("inactive_score_threshold", 45.0))
            inactive_days = max(1, int(config.get("inactive_days", 5)))
            cooldown_days = max(0, int(config.get("cooldown_days", 10)))

            indicator_results = self._scan_indicators(df, config)
            if not indicator_results:
                return invalid("no indicator result")

            daily_scores = self._merge_indicator_scores(indicator_results, weights)
            events = self._find_active_events(
                daily_scores,
                active_score_threshold,
                inactive_score_threshold,
                inactive_days,
                cooldown_days,
            )

            return ok(
                "activity score scanned",
                {
                    "count": len(events),
                    "events": events,
                    "daily_scores": daily_scores,
                    "indicators": indicator_results,
                    "config": {
                        "weights": weights,
                        "active_score_threshold": active_score_threshold,
                        "inactive_score_threshold": inactive_score_threshold,
                        "inactive_days": inactive_days,
                        "cooldown_days": cooldown_days,
                    },
                },
            )
        except ValueError as exc:
            return invalid(str(exc))
        except Exception as exc:
            return error(f"activity scan failed: {exc}")

    def _weights(self, config: dict[str, Any]) -> dict[str, float]:
        configured = dict(config.get("weights") or {})
        weights = {
            "volume_ratio": float(configured.get("volume_ratio", 0.45)),
            "turnover": float(configured.get("turnover", 0.35)),
            "institution": float(configured.get("institution", 0.20)),
        }
        return {name: max(0.0, value) for name, value in weights.items()}

    def _scan_indicators(
        self,
        df: Any,
        config: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        requests = {
            "volume_ratio": "/VolumeRatioScanService/scan",
            "turnover": "/TurnoverScanService/scan",
            "institution": "/InstitutionScanService/scan",
        }
        results = {}
        for name, url in requests.items():
            resp = YomkApi.request(url, {"df": df, "config": config})
            if resp.status != YomkApi.ResStatus.eOk:
                raise ValueError(f"{name} scan failed: {resp.msg}")
            results[name] = resp.data
        return results

    def _merge_indicator_scores(
        self,
        indicator_results: dict[str, dict[str, Any]],
        weights: dict[str, float],
    ) -> list[dict[str, Any]]:
        by_date: dict[str, dict[str, Any]] = {}
        for indicator_name, result in indicator_results.items():
            for row in result.get("rows", []):
                date = row["date"]
                item = by_date.setdefault(
                    date,
                    {
                        "date": date,
                        "score": 0.0,
                        "indicator_scores": {},
                        "details": {},
                        "breakout_indicators": [],
                    },
                )
                item["indicator_scores"][indicator_name] = float(row.get("score", 0.0))
                item["details"][indicator_name] = row
                if row.get("is_breakout"):
                    item["breakout_indicators"].append(indicator_name)

        total_weight = sum(weights.values())
        if total_weight <= 0:
            total_weight = 1.0

        rows = []
        for date in sorted(by_date):
            item = by_date[date]
            score = 0.0
            for indicator_name, weight in weights.items():
                score += item["indicator_scores"].get(indicator_name, 0.0) * weight
            item["score"] = round(score / total_weight, 2)
            rows.append(item)
        return rows

    def _find_active_events(
        self,
        daily_scores: list[dict[str, Any]],
        active_score_threshold: float,
        inactive_score_threshold: float,
        inactive_days: int,
        cooldown_days: int,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        last_event_index: int | None = None

        for index, row in enumerate(daily_scores):
            if index < inactive_days:
                continue

            previous_scores = [
                daily_scores[pos]["score"]
                for pos in range(index - inactive_days, index)
            ]
            was_inactive = max(previous_scores) <= inactive_score_threshold
            is_active = row["score"] >= active_score_threshold
            has_breakout = bool(row["breakout_indicators"])

            if not (was_inactive and is_active and has_breakout):
                continue
            if last_event_index is not None and index - last_event_index <= cooldown_days:
                continue

            events.append(
                {
                    "date": row["date"],
                    "score": row["score"],
                    "trend_status": "开始活跃",
                    "breakout_indicators": row["breakout_indicators"],
                    "indicator_scores": row["indicator_scores"],
                    "details": row["details"],
                }
            )
            last_event_index = index
        return events
