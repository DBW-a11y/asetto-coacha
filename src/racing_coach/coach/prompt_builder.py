"""Build LLM prompts from analysis results using Jinja2 templates."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..analysis.comparator import LapComparison
from ..analysis.metrics import CornerMetrics, LapMetrics
from ..analysis.scoring import DrivingScore

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptBuilder:
    """Builds structured prompts for the AI coach from analysis results."""

    def __init__(self, templates_dir: Path | None = None):
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir or _TEMPLATES_DIR)),
            keep_trailing_newline=True,
        )

    def build_lap_analysis_prompt(
        self,
        track: str,
        car: str,
        lap_number: int,
        lap_time_ms: float,
        metrics: LapMetrics,
        score: DrivingScore,
        corners: list[CornerMetrics] | None = None,
        comparison: LapComparison | None = None,
        best_lap_time_ms: float | None = None,
    ) -> str:
        """Build a prompt for single-lap analysis."""
        template = self._env.get_template("lap_analysis.j2")
        return template.render(
            track=track,
            car=car,
            lap_number=lap_number,
            lap_time_ms=lap_time_ms,
            metrics=metrics,
            score=score,
            corners=corners or [],
            comparison=comparison,
            best_lap_time_ms=best_lap_time_ms,
        )

    @staticmethod
    def system_prompt() -> str:
        return (
            "你是 Racing Coach，一位专业的虚拟赛车教练。"
            "你的任务是根据遥测数据分析结果，为模拟赛车玩家提供具体、可操作的中文驾驶改进建议。"
            "请用简洁专业的语言，避免空泛的建议。每条建议都应指向具体的弯道和操作。"
            "使用赛车术语时请附带简短解释。"
        )
