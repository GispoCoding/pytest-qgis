from qgis.core import Qgis, QgsProcessing, QgsProject, QgsVectorLayer


def test_add_layer():
    layer = QgsVectorLayer("Polygon", "dummy_polygon_layer", "memory")
    QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_new_project(new_project):
    QgsProject.instance().mapLayers() == {}


def test_msg_bar(qgis_iface):
    qgis_iface.messageBar().pushMessage("title", "text", Qgis.Info, 6)
    assert qgis_iface.messageBar().messages.get(Qgis.Info) == ["title:text"]


def test_processing(qgis_processing):
    from qgis import processing

    result = processing.run(
        "qgis:creategrid",
        {
            "TYPE": 0,  # Point
            "EXTENT": "0,2,0,2",
            "HSPACING": 1.0,
            "VSPACING": 1.0,
            "CRS": "EPSG:4326",
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
        },
    )

    assert "OUTPUT" in result
    assert isinstance(result["OUTPUT"], QgsVectorLayer)
    assert result["OUTPUT"].isValid()
    assert len(list(result["OUTPUT"].getFeatures())) > 0
