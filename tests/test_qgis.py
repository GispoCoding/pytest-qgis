from qgis.core import Qgis, QgsProject, QgsVectorLayer


def test_add_layer():
    layer = QgsVectorLayer("Polygon", "dummy_polygon_layer", "memory")
    QgsProject.instance().addMapLayer(layer)
    assert set(QgsProject.instance().mapLayers().values()) == {layer}


def test_new_project(new_project):
    QgsProject.instance().mapLayers() == {}


def test_msg_bar(qgis_iface):
    qgis_iface.messageBar().pushMessage("title", "text", Qgis.Info, 6)
    assert qgis_iface.messageBar().messages.get(Qgis.Info) == ["title:text"]
