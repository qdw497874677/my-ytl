"""Application service for inspect-first YouTube target workflows."""

from typing import Protocol

from pydantic import BaseModel, ConfigDict

from yt_subs.domain.models import InspectItem, JobOptions, OutputIdentity, TargetRequest
from yt_subs.domain.policies import build_output_identity, plan_item_paths
from yt_subs.domain.url import parse_target_url
from yt_subs.infrastructure.yt_dlp_adapter import YtDlpInspector


class Inspector(Protocol):
    def inspect(self, url: str) -> list[InspectItem]: ...


class InspectedPlanItem(BaseModel):
    """Inspected item paired with its planned output identity."""

    model_config = ConfigDict(frozen=True)
    item: InspectItem
    identity: OutputIdentity


class InspectReport(BaseModel):
    """Complete inspect result for a submitted target."""

    model_config = ConfigDict(frozen=True)
    target: TargetRequest
    items: list[InspectedPlanItem]


def inspect_target(
    url: str,
    options: JobOptions,
    *,
    inspector: Inspector | None = None,
) -> InspectReport:
    """Inspect a YouTube target and attach deterministic output path plans."""

    target = parse_target_url(url)
    inspector = inspector or YtDlpInspector()
    items = inspector.inspect(str(target.url))
    planned_items = []
    for item in items:
        identity = build_output_identity(item, options)
        planned_items.append(
            InspectedPlanItem(item=item, identity=plan_item_paths(identity, options))
        )
    return InspectReport(target=target, items=planned_items)
