from pathlib import Path

import pytest
from qgis.core import QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QToolBar

RASTER_PATH = Path(Path(__file__).parent, "data", "small_raster.tif")


@pytest.fixture(autouse=True)
def _setup(qgis_new_project: None) -> None:
    pass


def test_add_vector_layer():
    layer = QgsVectorLayer("Polygon", "dummy_polygon_layer", "memory")
    assert QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_add_vector_layer_via_iface(qgis_iface: "QgisInterface"):
    layer = qgis_iface.addVectorLayer("Polygon", "dummy_polygon_layer", "memory")
    assert layer.isValid()
    assert QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_add_raster_layer_via_iface(qgis_iface: "QgisInterface"):
    layer = qgis_iface.addRasterLayer(
        str(RASTER_PATH),
        "Raster",
    )
    assert QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_iface_active_layer(
    qgis_iface: "QgisInterface",
    layer_polygon: "QgsVectorLayer",
    layer_points: "QgsVectorLayer",
):
    QgsProject.instance().addMapLayer(layer_polygon)
    QgsProject.instance().addMapLayer(layer_points)

    assert qgis_iface.activeLayer() is None
    qgis_iface.setActiveLayer(layer_polygon)
    assert qgis_iface.activeLayer() == layer_polygon
    qgis_iface.setActiveLayer(layer_points)
    assert qgis_iface.activeLayer() == layer_points


def test_iface_toolbar_str(qgis_iface: "QgisInterface"):
    name = "test_bar"
    toolbar: QToolBar = qgis_iface.addToolBar(name)
    assert toolbar.windowTitle() == name
    assert qgis_iface._toolbars == {name: toolbar}


def test_iface_toolbar_qtoolbar(qgis_iface: "QgisInterface"):
    name = "test_bar"
    toolbar: QToolBar = QToolBar(name)
    qgis_iface.addToolBar(toolbar)
    assert toolbar.windowTitle() == name
    assert qgis_iface._toolbars == {name: toolbar}


def test_iface_has_all_qgis_interface_methods(qgis_iface: "QgisInterface"):
    for method_name in dir(QgisInterface):
        assert hasattr(qgis_iface, method_name)
