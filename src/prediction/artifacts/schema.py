from catboost import CatBoost
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from datetime import datetime

from typing import Self


class CatBoostArtifactSchema(BaseModel):
    """Validated contents shared by all persisted CatBoost artifacts."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    model: CatBoost
    feature_columns:list[str]
    categorical_columns: list[str] = []
    model_name: str | None = None
    model_version: str | None = None
    saved_at: datetime

    @field_validator("feature_columns")
    @classmethod
    def validate_feature_columns(cls, columns: tuple[str, ...]) -> tuple[str, ...]:
        if not columns:
            raise ValueError("Artifact has no feature columns")
        if len(columns) != len(set(columns)):
            raise ValueError("Artifact feature columns must be unique")
        return columns

    @field_validator("categorical_columns")
    @classmethod
    def validate_categorical_columns(cls, columns: tuple[str, ...]) -> tuple[str, ...]:
        if len(columns) != len(set(columns)):
            raise ValueError("Artifact categorical columns must be unique")
        return columns

    @model_validator(mode="after")
    def validate_categorical_features(self) -> Self:
        unknown_columns = set(self.categorical_columns) - set(self.feature_columns)
        if unknown_columns:
            raise ValueError(
                "Categorical columns are missing from feature_columns: "
                f"{sorted(unknown_columns)}"
            )
        return self