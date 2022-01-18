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
#
import pytest
from qgis.core import QgsGeometry
from qgis.gui import QgsAttributeDialog


@pytest.mark.parametrize("bot", ["qgis_bot", "module_qgis_bot"])
def test_create_feature_with_attribute_dialog(layer_points, bot, request):
    bot = request.getfixturevalue(bot)
    layer = layer_points
    count = layer.featureCount()

    layer.startEditing()
    feat = bot.create_feature_with_attribute_dialog(
        layer, QgsGeometry.fromWkt("POINT(0,0)")
    )
    assert layer.featureCount() == count + 1
    assert feat["bool_field"] is False  # With normal way of creating, it would be NULL.


def test_get_qgs_attribute_dialog_widgets_by_name(qgis_iface, layer_points, qgis_bot):
    dialog = QgsAttributeDialog(
        layer_points,
        layer_points.getFeature(1),
        False,
        qgis_iface.mainWindow(),
        True,
    )
    widgets_by_name = qgis_bot.get_qgs_attribute_dialog_widgets_by_name(dialog)
    assert {
        name: widget.__class__.__name__ for name, widget in widgets_by_name.items()
    } == {
        "bool_field": "QCheckBox",
        "date_field": "QDateTimeEdit",
        "datetime_field": "QDateTimeEdit",
        "decimal_field": "QgsFilterLineEdit",
        "fid": "QgsFilterLineEdit",
        "text_field": "QgsFilterLineEdit",
    }
