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
from typing import TYPE_CHECKING, Optional
from unittest import mock

import pytest
from _pytest.tmpdir import TempPathFactory
from qgis.core import Qgis, QgsApplication
from qgis.gui import QgisInterface as QgisInterfaceOrig
from qgis.gui import QgsMapCanvas
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QWidget

from pytest_qgis.mock_qgis_classes import MockMessageBar
from pytest_qgis.qgis_interface import QgisInterface

if TYPE_CHECKING:
    from _pytest.config import Config

try:
    QGIS_VERSION = Qgis.versionInt()
except AttributeError:
    QGIS_VERSION = Qgis.QGIS_VERSION_INT

_APP: Optional[QgsApplication] = None
_CANVAS: Optional[QgsMapCanvas] = None
_IFACE: Optional[QgisInterface] = None
_PARENT: Optional[QtWidgets.QWidget] = None


@pytest.fixture(autouse=True, scope="session")
def qgis_app() -> QgsApplication:
    yield _APP
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
    python_plugins_path = os.path.join(qgis_app.pkgDataPath(), "python", "plugins")
    if python_plugins_path not in sys.path:
        sys.path.append(python_plugins_path)
    from processing.core.Processing import Processing

    Processing.initialize()


def pytest_configure(config: "Config") -> None:
    """Initializes qgis session for all tests"""
    global _APP, _CANVAS, _IFACE, _PARENT

    # Use temporary path for QGIS config
    tmp_path_factory = TempPathFactory.from_config(config, _ispytest=True)
    config_path = tmp_path_factory.mktemp("qgis-test")
    os.environ["QGIS_CUSTOM_CONFIG_PATH"] = str(config_path)

    _APP = QgsApplication([], GUIenabled=False)
    _APP.initQgis()

    _PARENT = QtWidgets.QWidget()
    _CANVAS = QgsMapCanvas(_PARENT)

    _CANVAS.resize(QtCore.QSize(400, 400))

    # QgisInterface is a stub implementation of the QGIS plugin interface
    _IFACE = QgisInterface(_CANVAS, MockMessageBar(), _PARENT)

    # Patching imported iface (evaluated as None in tests) with iface.
    # This only works with QGIS >= 3.18 since before that
    # importing qgis.utils causes RecursionErrors. See this issue for details
    # https://github.com/qgis/QGIS/issues/40564
    if QGIS_VERSION >= 31800:
        from qgis.utils import iface  # noqa # This import is required

        mock.patch("qgis.utils.iface", _IFACE).start()
