from typing import TYPE_CHECKING

import pytest
from qgis.core import Qgis

if TYPE_CHECKING:
    from qgis.gui import QgisInterface


@pytest.mark.parametrize(
    ("args", "kwargs", "expected_level", "expected_message"),
    [
        (["text"], {}, Qgis.Info, "no-title:text"),
        (["title"], {"text": "text"}, Qgis.MessageLevel.Info, "title:text"),
        (
            ["text", Qgis.MessageLevel.Success],
            {},
            Qgis.MessageLevel.Success,
            "no-title:text",
        ),
        (
            ["title", "text", Qgis.MessageLevel.Warning, 20],
            {},
            Qgis.Warning,
            "title:text",
        ),
        (
            ["title", "text", "showMore", Qgis.MessageLevel.Warning, 20],
            {},
            Qgis.Warning,
            "title:text",
        ),
        (
            [],
            {
                "title": "title",
                "text": "text",
                "showMore": "showMore",
                "level": Qgis.MessageLevel.Warning,
                "duration": 20,
            },
            Qgis.Warning,
            "title:text",
        ),
    ],
)
def test_message_bar(  # noqa: PLR0913
    qgis_new_project: None,
    qgis_iface: "QgisInterface",
    args: list,
    kwargs: dict,
    expected_level: Qgis.MessageLevel,
    expected_message: str,
):
    qgis_iface.messageBar().pushMessage(*args, **kwargs)
    assert qgis_iface.messageBar().messages.get(expected_level) == [expected_message]
