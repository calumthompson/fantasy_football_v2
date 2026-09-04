import pandas as pd
import streamlit as st

from prediction.models.ensemble_model import ensemble_model
from prediction.models.in_season_model import in_season_model
from prediction.models.pre_season_model import pre_season_model


def render_model_features() -> None:
    """List the input features from each loaded model's artifact."""
    st.subheader("Model feature columns")
    st.caption("Features are shown in the order used by each loaded model.")

    for label, model in (
        ("Pre-season model", pre_season_model),
        ("In-season model", in_season_model),
        ("Ensemble model", ensemble_model),
    ):
        with st.expander(f"{label} · {len(model.feature_columns)} features"):
            categorical = set(model.categorical_columns)
            st.dataframe(
                pd.DataFrame(
                    {
                        "Order": range(1, len(model.feature_columns) + 1),
                        "Feature": model.feature_columns,
                        "Categorical": [
                            feature in categorical for feature in model.feature_columns
                        ],
                    }
                ),
                hide_index=True,
                width="stretch",
            )
