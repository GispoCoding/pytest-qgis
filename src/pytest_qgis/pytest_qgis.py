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
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from qgis.core import QgsApplication
from qgis.gui import QgisInterface as QgisInterfaceOrig
from qgis.gui import QgsMapCanvas
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QWidget

from pytest_qgis.mock_qgis_classes import MainWindow, MockMessageBar
from pytest_qgis.qgis_interface import QgisInterface

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory


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
def qgis_iface(qgis_canvas: QgsMapCanvas) -> QgisInterfaceOrig:
    # QgisInterface is a stub implementation of the QGIS plugin interface
    iface = QgisInterface(qgis_canvas, MockMessageBar(), MainWindow())
    return iface


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
    python_plugins_path = os.path.join(qgis_app.pkgDataPath(), "python", "plugins")
    if python_plugins_path not in sys.path:
        sys.path.append(python_plugins_path)
    from processing.core.Processing import Processing

    Processing.initialize()
