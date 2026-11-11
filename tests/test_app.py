from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_loads_and_supports_backtest_controls():
    app = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert "Understand the uncertainty" in app.title[0].value
    app.sidebar.radio[0].set_value("Backtest explorer").run()
    app.sidebar.selectbox[0].set_value("Random Forest").run()
    app.sidebar.select_slider[0].set_value(1).run()
    assert not app.exception
    assert app.metric[1].label == "1-WEEK TEST MAE"
