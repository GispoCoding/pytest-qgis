#  Copyright (C) 2021-2022 pytest-qgis Contributors.
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
import time

from qgis.gui import QgsAttributeDialog
from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import QCoreApplication

from pytest_qgis.utils import get_qgs_attribute_dialog_widgets_by_name

from ..utils import IN_CI

TIMEOUT = 0.01 if IN_CI else 1


def test_attribute_dialog_change(qgis_iface, qgis_canvas, layer_points, qtbot):
    # The essential thing is QgsGui.editorWidgetRegistry().initEditors()
    layer = layer_points

    layer.startEditing()
    f = layer.getFeature(1)
    assert f

    dialog = QgsAttributeDialog(
        layer,
        f,
        False,
        qgis_iface.mainWindow(),
        True,
    )
    qtbot.add_widget(dialog)
    dialog.show()

    widgets_by_name = get_qgs_attribute_dialog_widgets_by_name(dialog)
    test_text = "New string"

    # Doubleclick and keys after that erase the old text
    qtbot.mouseDClick(widgets_by_name["text_field"], QtCore.Qt.LeftButton)
    qtbot.keyClicks(widgets_by_name["text_field"], test_text)

    t = time.time()
    while time.time() - t < TIMEOUT and dialog.isVisible():
        QCoreApplication.processEvents()
    dialog.accept()
    layer.commitChanges()

    assert layer.getFeature(1)["text_field"] == test_text
