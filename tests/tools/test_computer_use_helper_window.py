"""A Chrome helper surface must not hide a usable browser on another Space."""
import json
from unittest.mock import MagicMock, patch

import pytest

from tools.computer_use.cua_backend import CuaDriverBackend
from tools.computer_use.tool import handle_computer_use


@pytest.mark.parametrize("helper_bounds", [{"width": 1.0, "height": 1.0}, {"width": 0, "height": 900}])
@pytest.mark.parametrize("on_screen", [True, False])
def test_capture_chooses_browser_over_nonrenderable_helper(helper_bounds, on_screen):
    backend = CuaDriverBackend()
    backend._session = MagicMock()
    backend._session.call_tool.return_value = {"structuredContent": {"windows": [
        {"app_name": "Google Chrome", "pid": 42, "window_id": 7,
         "z_index": 10, "is_on_screen": on_screen, "bounds": helper_bounds},
        {"app_name": "Google Chrome", "pid": 42, "window_id": 8,
         "z_index": 9, "is_on_screen": False, "bounds": {"width": 1298, "height": 900}},
    ]}}
    with patch("tools.computer_use.tool._get_backend", return_value=backend), \
         patch.object(backend, "_capture_window_state", return_value=(None, None, [], "")):
        json.loads(handle_computer_use({"action": "capture", "mode": "ax", "app": "Google Chrome"},
                                      session_id="helper-window-test"))
    assert (backend._active_pid, backend._active_window_id) == (42, 8)


def test_explicit_capture_does_not_substitute_a_different_window():
    backend = CuaDriverBackend()
    backend._session = MagicMock()
    with patch("tools.computer_use.tool._get_backend", return_value=backend), \
         patch.object(backend, "list_windows") as discover, \
         patch.object(backend, "_capture_window_state", return_value=(None, None, [], "")):
        json.loads(handle_computer_use({"action": "capture", "mode": "ax", "app": "Google Chrome",
                                      "pid": 42, "window_id": 7}, session_id="exact-window-test"))
    assert (backend._active_pid, backend._active_window_id) == (42, 7)
    discover.assert_not_called()


@pytest.mark.parametrize("bounds", [None, {}, {"width": None, "height": None},
    {"width": True, "height": False}, {"width": "1", "height": "1"},
    {"width": -1, "height": -1}, {"width": 2, "height": 2},
    {"width": 1298, "height": 900}])
def test_discovery_preserves_windows_without_known_helper_geometry(bounds):
    from tools.computer_use.cua_backend_parse import _ingest_windows

    window = {"app_name": "Example", "pid": 42, "window_id": 8, "bounds": bounds}
    assert [(w["pid"], w["window_id"]) for w in _ingest_windows([window])] == [(42, 8)]
