# -*- coding: utf-8 -*-

#  Copyright (C) 2021 pytest-qgis Contributors.
#
#
#  This file is part of pytest-qgis.
#
#  pytest-qgis is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  pytest-qgis is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with pytest-qgis.  If not, see <https://www.gnu.org/licenses/>.


import os.path
import sys
import time
import warnings
from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from unittest import mock

import pytest
from _pytest.tmpdir import TempPathFactory
from qgis.core import Qgis, QgsApplication, QgsProject, QgsRectangle, QgsVectorLayer
from qgis.gui import QgisInterface as QgisInterfaceOrig
from qgis.gui import QgsMapCanvas
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox, QWidget

from pytest_qgis.mock_qgis_classes import MockMessageBar
from pytest_qgis.qgis_interface import QgisInterface
from pytest_qgis.utils import (
    clean_qgis_layer,
    get_common_extent_from_all_layers,
    get_layers_with_different_crs,
    replace_layers_with_reprojected_clones,
    set_map_crs_based_on_layers,
)

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import SubRequest
    from _pytest.mark import Mark

DISABLE_GUI_KEY = "qgis_disable_gui"
DISABLE_QGIS_INIT_KEY = "qgis_disable_init"
GUI_ENABLED_KEY = "qgis_qui_enabled"
CANVAS_HEIGHT_KEY = "qgis_canvas_height"
CANVAS_WIDTH_KEY = "qgis_canvas_width"
SHOW_MAP_MARKER = "qgis_show_map"

GUI_DESCRIPTION = "Set whether the graphical user interface is wanted or not."
DISABLE_QGIS_DESCRIPTION = "Prevent QGIS (QgsApllication) from initializing."
CANVAS_DESCRIPTION = "Set canvas height and width."

DEFAULT_GUI_ENABLED = True
DEFAULT_AUTOUSE_QGIS = True
DEFAULT_CANVAS_SIZE = (600, 600)
DEFAULT_MAP_VISIBILITY_TIMEOUT = 30

Settings = namedtuple(
    "Settings", ["gui_enabled", "qgis_init_disabled", "canvas_width", "canvas_height"]
)
ShowMapSettings = namedtuple(
    "ShowMapSettings", ["timeout", "add_basemap", "zoom_to_common_extent", "extent"]
)

try:
    _QGIS_VERSION = Qgis.versionInt()
except AttributeError:
    _QGIS_VERSION = Qgis.QGIS_VERSION_INT

_APP: Optional[QgsApplication] = None
_CANVAS: Optional[QgsMapCanvas] = None
_IFACE: Optional[QgisInterface] = None
_PARENT: Optional[QtWidgets.QWidget] = None
_AUTOUSE_QGIS: Optional[bool] = None


@pytest.hookimpl()
def pytest_addoption(parser: "Parser") -> None:
    group = parser.getgroup(
        "qgis",
        "Utilities for testing QGIS plugins",
    )
    group.addoption(f"--{DISABLE_GUI_KEY}", action="store_true", help=GUI_DESCRIPTION)
    group.addoption(
        f"--{DISABLE_QGIS_INIT_KEY}", action="store_true", help=DISABLE_QGIS_DESCRIPTION
    )

    parser.addini(
        GUI_ENABLED_KEY, GUI_DESCRIPTION, type="bool", default=DEFAULT_GUI_ENABLED
    )

    parser.addini(
        CANVAS_WIDTH_KEY,
        CANVAS_DESCRIPTION,
        type="string",
        default=DEFAULT_CANVAS_SIZE[0],
    )
    parser.addini(
        CANVAS_HEIGHT_KEY,
        CANVAS_DESCRIPTION,
        type="string",
        default=DEFAULT_CANVAS_SIZE[1],
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: "Config") -> None:
    """Configure and initialize qgis session for all tests."""
    config.addinivalue_line(
        "markers",
        f"{SHOW_MAP_MARKER}(timeout={DEFAULT_MAP_VISIBILITY_TIMEOUT}, add_basemap=False, zoom_to_common_extent=True, extent=None): "  # noqa E501
        "Show QGIS map for a short amount of time. "
        "The first keyword, *timeout*, is the timeout in seconds until "
        "the map closes. The second keyword *add_basemap*, when set to True, "
        "adds Natural Earth countries layer as the basemap for the map. "
        "The third keyword *zoom_to_common_extent*, "
        "when set to True, centers the map around all layers in the project.  "
        "Alternatively the fourth keyword *extent* can be provided as QgsRectangle.",
    )

    settings = _parse_settings(config)
    config._plugin_settings = settings

    if not settings.gui_enabled:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    _start_and_configure_qgis_app(config)


@pytest.fixture(autouse=True, scope="session")
def qgis_app(request: "SubRequest") -> QgsApplication:
    yield _APP if not request.config._plugin_settings.qgis_init_disabled else None

    if not request.config._plugin_settings.qgis_init_disabled:
        assert _APP
        _APP.exitQgis()


@pytest.fixture(scope="session")
def qgis_parent(qgis_app: QgsApplication) -> QWidget:
    return _PARENT


@pytest.fixture(scope="session")
def qgis_canvas() -> QgsMapCanvas:
    return _CANVAS


@pytest.fixture(scope="session")
def qgis_iface() -> QgisInterfaceOrig:
    return _IFACE


@pytest.fixture()
def new_project(qgis_iface: QgisInterface) -> None:  # noqa QGS105
    """
    Initializes new QGIS project by removing layers and relations etc.
    """
    qgis_iface.newProject()


@pytest.fixture(scope="session")
def qgis_processing(qgis_app: QgsApplication) -> None:
    """
    Initializes QGIS processing framework
    """
    _initialize_processing(qgis_app)


@pytest.fixture()
@clean_qgis_layer
def qgis_natural_earth_countries() -> QgsVectorLayer:
    """
    Natural Earth countries in 50m resolution as QgsVectorLayer

    Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com
    """
    path_to_data = Path(__file__).parent / "data" / "ne_50m_admin_0_countries.geojson"
    assert path_to_data.exists(), path_to_data
    ne_countries = QgsVectorLayer(str(path_to_data), "Natural Earth Countries", "ogr")
    assert ne_countries.isValid()
    return ne_countries


@pytest.fixture(autouse=True)
def qgis_show_map(
    qgis_app: QgsApplication,
    qgis_iface: QgisInterface,
    qgis_parent: QWidget,
    qgis_natural_earth_countries: QgsVectorLayer,
    tmp_path: Path,
    request: "SubRequest",
) -> None:
    """
    Shows QGIS map if qgis_show_map marker is used.
    """
    show_map_marker = request.node.get_closest_marker(SHOW_MAP_MARKER)
    common_settings: Settings = request.config._plugin_settings  # type: ignore

    if (
        show_map_marker
        and common_settings.gui_enabled
        and not common_settings.qgis_init_disabled
    ):
        qgis_parent.setWindowTitle("Test QGIS dialog opened by Pytest-qgis")

        qgis_parent.show()
    elif show_map_marker and not common_settings.gui_enabled:
        warnings.warn(
            "Cannot show QGIS map because the GUI is not enabled. "
            "Set qgis_qui_enabled=True in pytest.ini."
        )
    elif show_map_marker and common_settings.qgis_init_disabled:
        warnings.warn(
            "Cannot show QGIS map because QGIS is not initialized. "
            "Run the tests without --qgis_disable_init to enable QGIS map."
        )

    yield

    if (
        show_map_marker
        and common_settings.gui_enabled
        and not common_settings.qgis_init_disabled
    ):
        _configure_qgis_map(
            qgis_app,
            qgis_iface,
            qgis_parent,
            _parse_show_map_marker(show_map_marker),
            tmp_path,
            qgis_natural_earth_countries,
        )


@pytest.fixture(scope="session")
def qgis_version() -> int:
    """QGIS version number as integer."""
    return _QGIS_VERSION


def _start_and_configure_qgis_app(config: "Config") -> None:
    global _APP, _CANVAS, _IFACE, _PARENT
    settings: Settings = config._plugin_settings  # type: ignore

    # Use temporary path for QGIS config
    tmp_path_factory = TempPathFactory.from_config(config, _ispytest=True)
    config_path = tmp_path_factory.mktemp("qgis-test")
    os.environ["QGIS_CUSTOM_CONFIG_PATH"] = str(config_path)

    if not settings.qgis_init_disabled:
        _APP = QgsApplication([], GUIenabled=settings.gui_enabled)
        _APP.initQgis()
    _PARENT = QWidget()
    _CANVAS = QgsMapCanvas(_PARENT)
    _CANVAS.resize(QtCore.QSize(settings.canvas_width, settings.canvas_height))

    # QgisInterface is a stub implementation of the QGIS plugin interface
    _IFACE = QgisInterface(_CANVAS, MockMessageBar(), _PARENT)

    # Patching imported iface (evaluated as None in tests) with iface.
    # This only works with QGIS >= 3.18 since before that
    # importing qgis.utils causes RecursionErrors. See this issue for details
    # https://github.com/qgis/QGIS/issues/40564
    if _QGIS_VERSION >= 31800:
        from qgis.utils import iface  # noqa # This import is required

        mock.patch("qgis.utils.iface", _IFACE).start()


def _initialize_processing(qgis_app: QgsApplication) -> None:
    python_plugins_path = os.path.join(qgis_app.pkgDataPath(), "python", "plugins")
    if python_plugins_path not in sys.path:
        sys.path.append(python_plugins_path)
    from processing.core.Processing import Processing

    Processing.initialize()


def _configure_qgis_map(
    qgis_app: QgsApplication,
    qgis_iface: QgisInterface,
    qgis_parent: QWidget,
    settings: ShowMapSettings,
    tmp_path: Path,
    qgis_natural_earth_countries: QgsVectorLayer,
) -> None:
    message_box = QMessageBox(qgis_parent)
    try:
        # Change project CRS to most common CRS if it is not set
        if not QgsProject.instance().crs().isValid():
            set_map_crs_based_on_layers()

        extent = settings.extent
        if settings.zoom_to_common_extent and extent is None:
            extent = get_common_extent_from_all_layers()
        if extent is not None:
            qgis_iface.mapCanvas().setExtent(extent)

        # Replace layers with different CRS
        layers_with_different_crs = get_layers_with_different_crs()
        if layers_with_different_crs:
            _initialize_processing(qgis_app)
            replace_layers_with_reprojected_clones(layers_with_different_crs, tmp_path)

        if settings.add_basemap:
            # Add Natural Earth Countries
            QgsProject.instance().addMapLayer(qgis_natural_earth_countries)
            if qgis_natural_earth_countries.crs() != QgsProject.instance().crs():
                _initialize_processing(qgis_app)
                replace_layers_with_reprojected_clones(
                    [qgis_natural_earth_countries], tmp_path
                )

        QgsProject.instance().reloadAllLayers()
        qgis_iface.mapCanvas().refreshAllLayers()

        message_box.setWindowTitle("pytest-qgis")
        message_box.setText(
            "Click close to close the map and to end the test.\n"
            f"It will close automatically in {settings.timeout} seconds."
        )
        message_box.addButton(QMessageBox.Close)
        message_box.move(
            message_box.mapToGlobal(qgis_parent.rect().topLeft())
            - QtCore.QPoint(message_box.width(), 0)
        )
        message_box.setWindowModality(QtCore.Qt.NonModal)
        message_box.show()

        t = time.time()
        while time.time() - t < settings.timeout and message_box.isVisible():
            QCoreApplication.processEvents()
    finally:
        message_box.close()
        qgis_parent.close()


def _parse_settings(config: "Config") -> Settings:
    gui_disabled = config.getoption(DISABLE_GUI_KEY)
    if not gui_disabled:
        gui_enabled = config.getini(GUI_ENABLED_KEY)
    else:
        gui_enabled = not gui_disabled

    qgis_init_disabled = config.getoption(DISABLE_QGIS_INIT_KEY)
    canvas_width = int(config.getini(CANVAS_WIDTH_KEY))
    canvas_height = int(config.getini(CANVAS_HEIGHT_KEY))

    return Settings(gui_enabled, qgis_init_disabled, canvas_width, canvas_height)


def _parse_show_map_marker(marker: "Mark") -> ShowMapSettings:
    timeout = add_basemap = zoom_to_common_extent = extent = notset = object()

    for kwarg, value in marker.kwargs.items():
        if kwarg == "timeout":
            timeout = value
        elif kwarg == "add_basemap":
            add_basemap = value
        elif kwarg == "zoom_to_common_extent":
            zoom_to_common_extent = value
        elif kwarg == "extent":
            extent = value
        else:
            raise TypeError(
                f"Invalid keyword argument for qgis_show_map marker: {kwarg}"
            )

    if len(marker.args) >= 1 and timeout is not notset:
        raise TypeError("Multiple values for timeout argument of qgis_show_map marker")
    elif len(marker.args) >= 1:
        timeout = marker.args[0]
    if len(marker.args) >= 2 and add_basemap is not notset:
        raise TypeError(
            "Multiple values for add_basemap argument of qgis_show_map marker"
        )
    elif len(marker.args) >= 2:
        add_basemap = marker.args[1]
    if len(marker.args) >= 3 and zoom_to_common_extent is not notset:
        raise TypeError(
            "Multiple values for zoom_to_common_extent argument of qgis_show_map marker"
        )
    elif len(marker.args) >= 3:
        zoom_to_common_extent = marker.args[2]
    if len(marker.args) >= 4 and extent is not notset:
        raise TypeError("Multiple values for extent argument of qgis_show_map marker")
    elif len(marker.args) >= 4:
        extent = marker.args[3]
    if len(marker.args) > 4:
        raise TypeError("Too many arguments for qgis_show_map marker")

    if timeout is notset:
        timeout = DEFAULT_MAP_VISIBILITY_TIMEOUT
    if add_basemap is notset:
        add_basemap = False
    if zoom_to_common_extent is notset:
        zoom_to_common_extent = True
    if extent is notset:
        extent = None
    elif not isinstance(extent, QgsRectangle):
        raise TypeError("Extent has to be of type QgsRectangle")
    return ShowMapSettings(timeout, add_basemap, zoom_to_common_extent, extent)
