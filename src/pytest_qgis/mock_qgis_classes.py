from typing import Any, Dict, List

from qgis.core import Qgis
from qgis.PyQt.QtCore import QObject


class MockMessageBar(QObject):
    """Mocked message bar to hold the messages."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: Dict[int, List[str]] = {
            Qgis.Info: [],
            Qgis.Warning: [],
            Qgis.Critical: [],
            Qgis.Success: [],
        }

    def get_messages(self, level: int) -> List[str]:
        """Used to test which messages have been logged."""
        return self.messages[level]

    def pushMessage(  # noqa N802
        self, title: str, text: str, level: int, duration: int
    ) -> None:
        """A mocked method for pushing a message to the bar."""
        msg = f"{title}:{text}"
        self.messages[level].append(msg)


class MainWindow(QObject):
    def blockSignals(self, *args: Any) -> None:  # noqa N802
        """Mocked blockSignals"""
        pass
