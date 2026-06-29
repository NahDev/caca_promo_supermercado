import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_metric_row(metrics: list[tuple[str, str]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def render_dataframe_with_export(
    frame: pd.DataFrame,
    file_name: str,
    caption: str | None = None,
) -> None:
    if frame.empty:
        st.info("No data available for this view.")
        return

    if caption:
        st.caption(caption)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    csv_buffer = io.StringIO()
    frame.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=file_name,
        mime="text/csv",
    )


def render_chart_with_export(figure: go.Figure, file_name: str) -> None:
    st.plotly_chart(figure, use_container_width=True)
    try:
        image_bytes = figure.to_image(format="png", width=1280, height=720, scale=2)
        st.download_button(
            label="Download PNG",
            data=image_bytes,
            file_name=file_name,
            mime="image/png",
        )
    except Exception:
        st.caption("PNG export requires kaleido. CSV exports remain available.")
