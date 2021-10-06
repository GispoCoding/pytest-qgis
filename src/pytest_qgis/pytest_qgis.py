# -*- coding: utf-8 -*-

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from qgis.core import QgsApplication
from qgis.gui import QgsMapCanvas
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QWidget

from pytest_qgis.mock_qgis_classes import MainWindow, MockMessageBar
from pytest_qgis.qgis_interface import QgisInterface

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory
    from qgis.gui import QgisInterface as QgisInterfaceOrig


@pytest.fixture(scope="session")
def tmp_qgis_config_path(tmp_path_factory: "TempPathFactory") -> Path:
    config_path = tmp_path_factory.mktemp("qgis-test")
    with patch.dict("os.environ", {"QGIS_CUSTOM_CONFIG_PATH": str(config_path)}):
        yield config_path


@pytest.fixture(autouse=True, scope="session")
def qgis_app(tmp_qgis_config_path: "Path") -> QgsApplication:
    """Initializes qgis session for all tests"""
    app = QgsApplication([], GUIenabled=False)
    app.initQgis()

    yield app

    app.exitQgis()


@pytest.fixture(scope="session")
def qgis_parent(qgis_app: QgsApplication) -> QWidget:
    return QtWidgets.QWidget()


@pytest.fixture(scope="session")
def qgis_canvas(qgis_parent: QWidget) -> QgsMapCanvas:
    canvas = QgsMapCanvas(qgis_parent)
    canvas.resize(QtCore.QSize(400, 400))
    return canvas


@pytest.fixture(scope="session")
def qgis_iface(qgis_canvas: QgsMapCanvas) -> "QgisInterfaceOrig":
    # QgisInterface is a stub implementation of the QGIS plugin interface
    iface = QgisInterface(qgis_canvas, MockMessageBar(), MainWindow())
    return iface


@pytest.fixture(scope="function")
def new_project(qgis_iface: QgisInterface) -> None:  # noqa QGS105
    """
    Initializes new QGIS project by removing layers and relations etc.
    """
    qgis_iface.newProject()
