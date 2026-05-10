"""Application service for runtime preflight readiness."""

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["required", "recommended"]


class PreflightCheck(BaseModel):
    """Single runtime capability check."""

    name: str
    available: bool
    severity: Severity
    version: str | None = None
    path: str | None = None
    remediation: str | None = None
    detail: str | None = None


class PreflightReport(BaseModel):
    """Complete preflight report with readiness helpers."""

    checks: list[PreflightCheck] = Field(default_factory=list)

    @property
    def required_passed(self) -> bool:
        return all(check.available for check in self.checks if check.severity == "required")

    def by_name(self, name: str) -> PreflightCheck:
        for check in self.checks:
            if check.name == name:
                return check
        raise KeyError(name)


def run_preflight() -> PreflightReport:
    """Run downloader runtime checks and return a structured report."""

    from yt_subs.infrastructure.preflight import collect_preflight_checks

    return PreflightReport(checks=collect_preflight_checks())
