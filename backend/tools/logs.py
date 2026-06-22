import re
from collections import Counter
from pathlib import Path

from backend.models import SeverityLevel, ToolResult
from backend.models.logs import ErrorPattern, LogAnalysisResult, LogErrorEntry
from backend.tools.base import run_tool

ERROR_LEVELS = {"ERROR", "CRITICAL", "FATAL", "EXCEPTION"}
LOG_LEVEL_RE = re.compile(
    r"\b(ERROR|CRITICAL|FATAL|WARN|WARNING|INFO|DEBUG|EXCEPTION)\b",
    re.IGNORECASE,
)
TIMESTAMP_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
)


def analyze_logs(path: str, lines: int = 500) -> ToolResult[LogAnalysisResult]:
    def _collect() -> LogAnalysisResult:
        log_path = Path(path)
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {path}")
        if not log_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        raw_lines = _read_tail(log_path, lines)
        errors: list[LogErrorEntry] = []
        pattern_counter: Counter[str] = Counter()

        for idx, line in enumerate(raw_lines, start=1):
            level = _extract_level(line)
            if level and level.upper() in ERROR_LEVELS:
                timestamp = _extract_timestamp(line)
                errors.append(
                    LogErrorEntry(
                        line=idx,
                        timestamp=timestamp,
                        message=line.strip()[:500],
                        level=level.upper(),
                    )
                )
                pattern = _normalize_pattern(line)
                pattern_counter[pattern] += 1

        patterns = [
            ErrorPattern(
                pattern=pattern,
                count=count,
                severity=SeverityLevel.CRITICAL if count >= 10 else SeverityLevel.WARNING,
            )
            for pattern, count in pattern_counter.most_common(10)
        ]

        summary = (
            f"{len(errors)} error-level entries in last {len(raw_lines)} lines"
            if errors
            else f"No errors detected in last {len(raw_lines)} lines"
        )

        return LogAnalysisResult(
            path=str(log_path),
            lines_analyzed=len(raw_lines),
            errors=errors[:50],
            patterns=patterns,
            summary=summary,
        )

    return run_tool("analyze_logs", _collect)


def _read_tail(path: Path, max_lines: int) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.readlines()[-max_lines:]
    except OSError as exc:
        raise OSError(f"Failed to read log file: {exc}") from exc


def _extract_level(line: str) -> str | None:
    match = LOG_LEVEL_RE.search(line)
    return match.group(1).upper() if match else None


def _extract_timestamp(line: str) -> str | None:
    match = TIMESTAMP_RE.search(line)
    return match.group(1) if match else None


def _normalize_pattern(line: str) -> str:
    normalized = re.sub(r"\d+", "N", line.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized[:120]
