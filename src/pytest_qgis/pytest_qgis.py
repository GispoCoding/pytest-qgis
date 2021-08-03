# -*- coding: utf-8 -*-

import pytest
from qgis.core import QgsApplication
from qgis.gui import QgisInterface as QgisInterfaceOrig
from qgis.gui import QgsMapCanvas
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QWidget

from pytest_qgis.mock_qgis_classes import MainWindow, MockMessageBar
from pytest_qgis.qgis_interface import QgisInterface


@pytest.fixture(autouse=True, scope="session")
def qgis_app() -> QgsApplication:
    """Initializes qgis session for all tests"""
    gui_flag = False
    app = QgsApplication([], gui_flag)
    app.initQgis()
    return app


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


@pytest.fixture(scope="function")
def new_project(qgis_iface: QgisInterface) -> None:  # noqa QGS105
    """
    Initializes new QGIS project by removing layers and relations etc.
    """
    qgis_iface.newProject()
