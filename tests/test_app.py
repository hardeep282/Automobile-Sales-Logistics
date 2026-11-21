"""Smoke-test the Streamlit app headlessly (no browser needed)."""

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def _run(**sidebar):
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60)
    at.run()
    for label, value in sidebar.items():
        next(w for w in at.multiselect if w.label == label).set_value(value)
    if sidebar:
        at.run()
    return at


def test_app_runs_without_exceptions():
    at = _run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 6
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Orders"] == "298"
    assert metrics["Total revenue"] == "£9.76M"
    assert metrics["Fulfilment rate"] == "96.2%"


def test_filters_change_kpis():
    at = _run(Region=["APAC"])
    assert not at.exception, at.exception
    assert {m.label: m.value for m in at.metric}["Orders"] != "298"


def test_empty_filter_is_handled():
    at = _run(Year=[])
    assert not at.exception
    assert any("No data" in w.value for w in at.warning)
