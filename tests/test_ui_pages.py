"""UI page regression tests using Streamlit's AppTest framework.

These actually run the Streamlit app and render both the home page and the
product detail page, asserting that no runtime exceptions occur. This is the
test that catches module-scope bugs like a ``formatters`` import that is only
visible inside one function.
"""
from __future__ import annotations

import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from config import settings

APP_PATH = str(settings.get_project_root() / "app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


def _trigger_search(app, keyword: str = "earbuds"):
    """Type a keyword into the search box and submit the form."""
    app.text_input[0].set_value(keyword)
    app.button  # noqa: B018 - ensure widgets hydrated
    # The submit button lives inside the form.
    submit = [b for b in app.button if b.label == "🔍 Search"]
    assert submit, "Search submit button not found"
    submit[0].click()
    app.run()
    assert not at_exception(app), at_exception(app)


def at_exception(app):
    return app.exception if hasattr(app, "exception") else None


def test_home_page_renders_without_error(app):
    app.run()
    assert not at_exception(app), at_exception(app)


def test_search_results_render_without_error(app):
    _trigger_search(app, "earbuds")
    # The results table should have populated session state.
    results = app.session_state["results"]
    assert isinstance(results, list)
    assert len(results) > 0
    assert not at_exception(app), at_exception(app)


def test_product_detail_page_renders_without_error(app):
    """Drives a search, then opens the first product's detail page.

    This exercises ``render_product_detail_page`` and would previously raise
    ``NameError: name 'formatters' is not defined``.
    """
    _trigger_search(app, "watch")

    # Open the detail view by setting session state directly (as navigation does)
    # and re-running.
    results = app.session_state["results"]
    assert results
    product_id = results[0]["id"]
    app.session_state["detail_product_id"] = product_id
    app.session_state["detail_triggered"] = True
    app.run()

    assert not at_exception(app), at_exception(app)
    # Detail page renders product title and estimate blocks.
    assert len(app.markdown) > 0
