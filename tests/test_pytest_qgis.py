#  Copyright (C) 2021-2023 pytest-qgis Contributors.
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
from typing import TYPE_CHECKING

import pytest
from qgis.core import Qgis, QgsProcessing, QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QToolBar
from qgis.utils import iface

from .utils import QGIS_VERSION

if TYPE_CHECKING:
    pass

# DO not use this directly, this is only meant to be used with
# replace_iface_with_qgis_iface fixture
__iface = None


@pytest.fixture()
def replace_iface_with_qgis_iface(qgis_iface):
    global __iface
    __iface = qgis_iface


@pytest.mark.usefixtures("replace_iface_with_qgis_iface")
def test_a_teardown():
    """
    When replacing imported or passed QgisInterface inside a fixture,
    it might cause problems with pytest_qgis.qgis_interface.removeAllLayers
    when qgis_app is exiting.
    """
    pass


def test_add_layer():
    layer = QgsVectorLayer("Polygon", "dummy_polygon_layer", "memory")
    QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_qgis_new_project(qgis_new_project):
    assert QgsProject.instance().mapLayers() == {}


def test_msg_bar(qgis_iface):
    qgis_iface.messageBar().pushMessage("title", "text", Qgis.Info, 6)
    assert qgis_iface.messageBar().messages.get(Qgis.Info) == ["title:text"]


def test_processing_providers(qgis_app, qgis_processing):
    assert "qgis" in [
        provider.id() for provider in qgis_app.processingRegistry().providers()
    ]


def test_processing_run(qgis_processing):
    from qgis import processing

    # Use any algo that is available on all test platforms
    result = processing.run(
        "qgis:regularpoints",
        {
            "EXTENT": "0,1,0,1",
            "CRS": "EPSG:4326",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        },
    )

    assert "OUTPUT" in result
    assert isinstance(result["OUTPUT"], QgsVectorLayer)
    assert result["OUTPUT"].isValid()
    assert len(list(result["OUTPUT"].getFeatures())) > 0


@pytest.mark.skipif(
    QGIS_VERSION < 31800, reason="https://github.com/qgis/QGIS/issues/40564"
)
def test_setup_qgis_iface(qgis_iface):
    assert iface == qgis_iface


def test_iface_active_layer(qgis_iface, layer_polygon, layer_points):
    QgsProject.instance().addMapLayer(layer_polygon)
    QgsProject.instance().addMapLayer(layer_points)

    assert qgis_iface.activeLayer() is None
    qgis_iface.setActiveLayer(layer_polygon)
    assert qgis_iface.activeLayer() == layer_polygon
    qgis_iface.setActiveLayer(layer_points)
    assert qgis_iface.activeLayer() == layer_points


def test_iface_toolbar_str(qgis_iface):
    name = "test_bar"
    toolbar: QToolBar = qgis_iface.addToolBar(name)
    assert toolbar.windowTitle() == name
    assert qgis_iface._toolbars == {name: toolbar}


def test_iface_toolbar_qtoolbar(qgis_iface):
    name = "test_bar"
    toolbar: QToolBar = QToolBar(name)
    qgis_iface.addToolBar(toolbar)
    assert toolbar.windowTitle() == name
    assert qgis_iface._toolbars == {name: toolbar}


def test_canvas_should_be_released(qgis_canvas, layer_polygon, layer_points):
    """
    This test will not assert anything but calling zoom methods of qgis_canvas
    will cause segmentation faults after test session if
    the canvas is not released properly.
    """
    QgsProject.instance().addMapLayer(layer_polygon)
    QgsProject.instance().addMapLayer(layer_points)
    qgis_canvas.zoomToFullExtent()
