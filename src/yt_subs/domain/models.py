"""Pydantic domain contracts for inspectable YouTube jobs and subtitle artifacts."""

from pathlib import Path
from typing import Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, field_validator

TargetKind = Literal["auto", "video", "playlist"]
SubtitleKind = Literal["manual", "automatic"]
SubtitleFormat = Literal["vtt", "srt", "txt"]


class TargetRequest(BaseModel):
    """User-submitted URL and optional target hint."""

    model_config = ConfigDict(frozen=True)

    url: AnyUrl
    kind: TargetKind = "auto"


class SubtitleTrack(BaseModel):
    """Normalized subtitle track discovered during inspection."""

    model_config = ConfigDict(frozen=True)

    language_code: str = Field(min_length=1)
    language_name: str | None = None
    kind: SubtitleKind
    source_format: str | None = None


class InspectItem(BaseModel):
    """Normalized inspect result for a video or playlist item."""

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(min_length=1)
    title: str | None = None
    webpage_url: AnyUrl
    playlist_index: int | None = Field(default=None, ge=1)
    subtitles: list[SubtitleTrack] = Field(default_factory=list)

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("video_id must not be empty")
        return value


class JobOptions(BaseModel):
    """Basic job options shared by CLI and future API entry points."""

    model_config = ConfigDict(frozen=True)
    output_dir: Path = Path("downloads")
    languages: list[str] = Field(default_factory=list)
    include_automatic: bool = True

    @field_validator("output_dir", mode="before")
    @classmethod
    def coerce_output_dir(cls, value: str | Path) -> Path:
        return Path(value)


class OutputIdentity(BaseModel):
    """Stable item identity and planned artifact namespace."""

    model_config = ConfigDict(frozen=True)
    video_id: str = Field(min_length=1)
    item_key: str = Field(min_length=1)
    title: str | None = None
    bundle_dir: Path
    metadata_path: Path
    subtitles_dir: Path
    logs_dir: Path
    media_dir: Path


class SubtitleProvenance(BaseModel):
    """Records the source track a converted artifact was derived from."""

    model_config = ConfigDict(frozen=True)

    source_path: Path
    source_format: SubtitleFormat
    source_language_code: str = Field(min_length=1)
    source_kind: SubtitleKind


class SubtitleArtifact(BaseModel):
    """A persisted subtitle file with format and provenance."""

    model_config = ConfigDict(frozen=True)

    language_code: str = Field(min_length=1)
    kind: SubtitleKind
    format: SubtitleFormat
    path: Path
    provenance: SubtitleProvenance


class MissingSubtitle(BaseModel):
    """A requested subtitle language that was unavailable."""

    model_config = ConfigDict(frozen=True)

    language_code: str = Field(min_length=1)
    reason: Literal["unavailable"]
    detail: str | None = None


class SubtitleDownloadOptions(BaseModel):
    """User-facing subtitle download options shared by CLI and future API."""

    model_config = ConfigDict(frozen=True)

    output_dir: Path = Path("downloads")
    languages: list[str] = Field(min_length=1)
    formats: list[SubtitleFormat] = Field(default=["vtt"])
    include_automatic: bool = True

    @field_validator("output_dir", mode="before")
    @classmethod
    def coerce_output_dir(cls, value: str | Path) -> Path:
        return Path(value)


class VideoMetadata(BaseModel):
    """Normalized metadata persisted alongside subtitle artifacts."""

    model_config = ConfigDict(frozen=True)

    video_id: str = Field(min_length=1)
    title: str | None = None
    webpage_url: AnyUrl
    requested_languages: list[str]
    requested_formats: list[SubtitleFormat]
    include_automatic: bool
    artifacts: list[SubtitleArtifact]
    missing_languages: list[MissingSubtitle]


class SubtitleDownloadResult(BaseModel):
    """Complete result of a single-video subtitle download."""

    model_config = ConfigDict(frozen=True)

    item: InspectItem
    identity: OutputIdentity
    artifacts: list[SubtitleArtifact]
    missing_subtitles: list[MissingSubtitle]
    metadata_path: Path
