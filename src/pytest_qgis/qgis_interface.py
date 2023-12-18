# mypy: disable-error-code="empty-body"

"""QGIS plugin implementation.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

.. note:: This source code was copied from the 'postgis viewer' application
     with original authors:
     Copyright (c) 2010 by Ivan Mincik, ivan.mincik@gista.sk
     Copyright (c) 2011 German Carrillo, geotux_tuxman@linuxmail.org
     Copyright (c) 2014 Tim Sutton, tim@linfiniti.com
     Copyright (c) 2021 pytest-qgis Contributors

"""

__author__ = "tim@linfiniti.com"
__revision__ = "$Format:%H$"
__date__ = "10/01/2011"
__copyright__ = (
    "Copyright (c) 2010 by Ivan Mincik, ivan.mincik@gista.sk and "
    "Copyright (c) 2011 German Carrillo, geotux_tuxman@linuxmail.org"
    "Copyright (c) 2014 Tim Sutton, tim@linfiniti.com"
    "Copyright (c) 2021-2023 pytest-qgis Contributors"
)

import logging
import typing
from typing import Any, ClassVar, Optional, Union

from qgis import core as qgis_core
from qgis.core import (
    QgsLayerTree,
    QgsMapLayer,
    QgsProject,
    QgsRelationManager,
    QgsVectorLayer,
)
from qgis.gui import QgisInterface as QgisAbstractInterface
from qgis.gui import (
    QgsAbstractMapToolHandler,
    QgsAdvancedDigitizingDockWidget,
    QgsApplicationExitBlockerInterface,
    QgsAttributeDialog,
    QgsBrowserGuiModel,
    QgsCustomDropHandler,
    QgsCustomProjectOpenHandler,
    QgsDevToolWidgetFactory,
    QgsLayerTreeMapCanvasBridge,
    QgsLayerTreeView,
    QgsLayoutCustomDropHandler,
    QgsLayoutDesignerInterface,
    QgsMapCanvas,
    QgsMapLayerConfigWidgetFactory,
    QgsMessageBar,
    QgsOptionsWidgetFactory,
    QgsPluginManagerInterface,
    QgsStatusBar,
)
from qgis.PyQt import QtCore, QtGui, QtWidgets, sip
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

from pytest_qgis.mock_qgis_classes import MockMessageBar

LOGGER = logging.getLogger("QGIS")


@typing.no_type_check  # TODO: remove this when most of the methods are implemented
class QgisInterface(QgisAbstractInterface):
    """
    Class to expose QGIS objects and functions to plugins.

    This class is here for enabling us to run unit tests only,
    so some of the methods are simply stubs.

    Feel free to add more content.
    """

    currentLayerChanged = QtCore.pyqtSignal(QgsMapCanvas)
    newProjectCreated = pyqtSignal()

    layerSavedAs: ClassVar[QtCore.pyqtSignal]
    projectRead: ClassVar[QtCore.pyqtSignal]
    initializationCompleted: ClassVar[QtCore.pyqtSignal]
    layoutDesignerClosed: ClassVar[QtCore.pyqtSignal]
    layoutDesignerWillBeClosed: ClassVar[QtCore.pyqtSignal]
    layoutDesignerOpened: ClassVar[QtCore.pyqtSignal]
    currentThemeChanged: ClassVar[QtCore.pyqtSignal]

    # Simple fields
    gps_panel_connection: Optional[qgis_core.QgsGpsConnection] = None

    def __init__(
        self,
        canvas: QgsMapCanvas,
        messageBar: MockMessageBar,
        mainWindow: QtWidgets.QMainWindow,
    ) -> None:
        super().__init__()
        self.canvas = canvas
        self._messageBar = messageBar
        self._mainWindow = mainWindow
        self._active_layer_id: Optional[str] = None

        # Set up slots so we can mimic the behaviour of QGIS when layers
        # are added.
        LOGGER.debug("Initialising canvas...")
        QgsProject.instance().layersAdded.connect(self.addLayers)
        QgsProject.instance().removeAll.connect(self.removeAllLayers)

        # For processing module
        self.destCrs = None
        self._layers: list[QgsMapLayer] = []

        # Add the MenuBar
        menu_bar = QtWidgets.QMenuBar()
        self._mainWindow.setMenuBar(menu_bar)

        # Add the toolbar list
        self._toolbars: dict[str, QtWidgets.QToolBar] = {}

    @pyqtSlot("QList<QgsMapLayer*>")
    def addLayers(self, layers: list[QgsMapLayer]) -> None:
        """Handle layers being added to the registry so they show up in canvas.

        :param layers: list<QgsMapLayer> list of map layers that were added

        .. note:: The QgsInterface api does not include this method,
            it is added here as a helper to facilitate testing.
        """
        current_layers = self.canvas.layers()
        final_layers = []
        for layer in current_layers:
            final_layers.append(layer)
        for layer in layers:
            final_layers.append(layer)
        self._layers = final_layers

        self.canvas.setLayers(final_layers)

    @pyqtSlot()
    def removeAllLayers(self) -> None:
        """Remove layers from the canvas before they get deleted."""
        if not sip.isdeleted(self.canvas):
            self.canvas.setLayers([])
        self._layers = []

    def newProject(self, promptToSaveFlag: bool = False) -> bool:
        """Create new project."""
        # noinspection PyArgumentList
        instance = QgsProject.instance()
        instance.removeAllMapLayers()
        root: QgsLayerTree = instance.layerTreeRoot()
        root.removeAllChildren()
        relation_manager: QgsRelationManager = instance.relationManager()
        for relation in relation_manager.relations():
            relation_manager.removeRelation(relation)
        self._layers.clear()
        self._messageBar.clear_messages()
        self.newProjectCreated.emit()
        return True

    def setGpsPanelConnection(
        self, connection: Optional[qgis_core.QgsGpsConnection]
    ) -> None:
        self.gps_panel_connection = connection

    def browserModel(self) -> Optional["QgsBrowserGuiModel"]:
        pass

    def askForDatumTransform(
        self,
        sourceCrs: qgis_core.QgsCoordinateReferenceSystem,
        destinationCrs: qgis_core.QgsCoordinateReferenceSystem,
    ) -> bool:
        pass

    def invalidateLocatorResults(self) -> None:
        pass

    def deregisterLocatorFilter(
        self, filter: Optional[qgis_core.QgsLocatorFilter]
    ) -> None:
        pass

    def registerLocatorFilter(
        self, filter: Optional[qgis_core.QgsLocatorFilter]
    ) -> None:
        pass

    def locatorSearch(self, searchText: Optional[str]) -> None:
        pass

    def preloadForm(self, uifile: Optional[str]) -> None:
        pass

    def getFeatureForm(
        self, layer: Optional[qgis_core.QgsVectorLayer], f: qgis_core.QgsFeature
    ) -> Optional["QgsAttributeDialog"]:
        pass

    def openFeatureForm(
        self,
        l: Optional[qgis_core.QgsVectorLayer],  # noqa: E741
        f: qgis_core.QgsFeature,
        updateFeatureOnly: bool = ...,
        showModal: bool = ...,
    ) -> bool:
        pass

    def openURL(self, url: Optional[str], useQgisDocDirectory: bool = ...) -> None:
        pass

    def unregisterCustomLayoutDropHandler(
        self, handler: Optional["QgsLayoutCustomDropHandler"]
    ) -> None:
        pass

    def registerCustomLayoutDropHandler(
        self, handler: Optional["QgsLayoutCustomDropHandler"]
    ) -> None:
        pass

    def unregisterCustomProjectOpenHandler(
        self, handler: Optional["QgsCustomProjectOpenHandler"]
    ) -> None:
        pass

    def registerCustomProjectOpenHandler(
        self, handler: Optional["QgsCustomProjectOpenHandler"]
    ) -> None:
        pass

    def unregisterCustomDropHandler(
        self, handler: Optional["QgsCustomDropHandler"]
    ) -> None:
        pass

    def registerCustomDropHandler(
        self, handler: Optional["QgsCustomDropHandler"]
    ) -> None:
        pass

    def unregisterMapToolHandler(
        self, handler: Optional["QgsAbstractMapToolHandler"]
    ) -> None:
        pass

    def registerMapToolHandler(
        self, handler: Optional["QgsAbstractMapToolHandler"]
    ) -> None:
        pass

    def unregisterApplicationExitBlocker(
        self, blocker: Optional["QgsApplicationExitBlockerInterface"]
    ) -> None:
        pass

    def registerApplicationExitBlocker(
        self, blocker: Optional["QgsApplicationExitBlockerInterface"]
    ) -> None:
        pass

    def unregisterDevToolWidgetFactory(
        self, factory: Optional["QgsDevToolWidgetFactory"]
    ) -> None:
        pass

    def registerDevToolWidgetFactory(
        self, factory: Optional["QgsDevToolWidgetFactory"]
    ) -> None:
        pass

    def unregisterProjectPropertiesWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        pass

    def registerProjectPropertiesWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        pass

    def unregisterOptionsWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        pass

    def registerOptionsWidgetFactory(
        self, factory: Optional["QgsOptionsWidgetFactory"]
    ) -> None:
        pass

    def unregisterMapLayerConfigWidgetFactory(
        self, factory: Optional["QgsMapLayerConfigWidgetFactory"]
    ) -> None:
        pass

    def registerMapLayerConfigWidgetFactory(
        self, factory: Optional["QgsMapLayerConfigWidgetFactory"]
    ) -> None:
        pass

    def unregisterMainWindowAction(self, action: Optional[QtWidgets.QAction]) -> bool:
        pass

    def registerMainWindowAction(
        self, action: Optional[QtWidgets.QAction], defaultShortcut: Optional[str]
    ) -> bool:
        pass

    def removeWindow(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def addWindow(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def showAttributeTable(
        self,
        l: Optional[qgis_core.QgsVectorLayer],  # noqa: E741
        filterExpression: Optional[str] = ...,
    ) -> Optional[QtWidgets.QDialog]:
        pass

    def showLayerProperties(
        self, layer: Optional[qgis_core.QgsMapLayer], page: Optional[str] = ...
    ) -> None:
        pass

    def removeDockWidget(self, dockwidget: Optional[QtWidgets.QDockWidget]) -> None:
        pass

    def addTabifiedDockWidget(
        self,
        area: QtCore.Qt.DockWidgetArea,
        dockwidget: Optional[QtWidgets.QDockWidget],
        tabifyWith: typing.Iterable[Optional[str]] = ...,
        raiseTab: bool = ...,
    ) -> None:
        pass

    def addDockWidget(
        self,
        area: QtCore.Qt.DockWidgetArea,
        dockwidget: Optional[QtWidgets.QDockWidget],
    ) -> None:
        pass

    def removePluginMeshMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToMeshMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def removePluginWebMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToWebMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def removePluginVectorMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToVectorMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def removePluginRasterMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToRasterMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def removePluginDatabaseMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToDatabaseMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def removeAddLayerAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def insertAddLayerAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def removePluginMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def addPluginToMenu(
        self, name: Optional[str], action: Optional[QtWidgets.QAction]
    ) -> None:
        pass

    def saveStyleSheetOptions(self, opts: dict[Optional[str], Any]) -> None:
        pass

    def buildStyleSheet(self, opts: dict[Optional[str], Any]) -> None:
        pass

    def showProjectPropertiesDialog(self, currentPage: Optional[str] = ...) -> None:
        pass

    def showOptionsDialog(
        self,
        parent: Optional[QtWidgets.QWidget] = ...,
        currentPage: Optional[str] = ...,
    ) -> None:
        pass

    def openLayoutDesigner(
        self, layout: Optional[qgis_core.QgsMasterLayoutInterface]
    ) -> Optional["QgsLayoutDesignerInterface"]:
        pass

    def showLayoutManager(self) -> None:
        pass

    def addUserInputWidget(self, widget: Optional[QtWidgets.QWidget]) -> None:
        pass

    def openMessageLog(self) -> None:
        pass

    @typing.overload
    def addToolBar(self, name: Optional[str]) -> Optional[QtWidgets.QToolBar]:
        pass

    @typing.overload
    def addToolBar(
        self,
        toolbar: Optional[QtWidgets.QToolBar],
        area: Optional[QtCore.Qt.ToolBarArea] = None,
    ) -> None:
        pass

    def addToolBar(
        self,
        toolbar: Union[str, QtWidgets.QToolBar],
        area: Optional[QtCore.Qt.ToolBarArea] = None,
    ) -> Optional[QtWidgets.QToolBar]:
        if isinstance(toolbar, str):
            name = toolbar
            _toolbar = QtWidgets.QToolBar(name, parent=self._mainWindow)
        else:
            name = toolbar.windowTitle()
            _toolbar = toolbar
        self._toolbars[name] = _toolbar
        return _toolbar if isinstance(toolbar, str) else None

    def removeWebToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        pass

    def addWebToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        pass

    def addWebToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        pass

    def removeDatabaseToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        pass

    def addDatabaseToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        pass

    def addDatabaseToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        pass

    def removeVectorToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        pass

    def addVectorToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        pass

    def addVectorToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        pass

    def removeRasterToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        pass

    def addRasterToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        pass

    def addRasterToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        pass

    def removeToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> None:
        pass

    def addToolBarWidget(
        self, widget: Optional[QtWidgets.QWidget]
    ) -> Optional[QtWidgets.QAction]:
        pass

    def addToolBarIcon(self, qAction: Optional[QtWidgets.QAction]) -> int:
        pass

    def pasteFromClipboard(self, a0: Optional[qgis_core.QgsMapLayer]) -> None:
        pass

    def copySelectionToClipboard(self, a0: Optional[qgis_core.QgsMapLayer]) -> None:
        pass

    def setActiveLayer(self, layer: Optional[qgis_core.QgsMapLayer]) -> bool:
        """
        Set the active layer (layer gets selected in the legend)
        """
        if layer is not None and QgsProject.instance().mapLayer(layer.id()):
            self._active_layer_id = layer.id()
            return True
        return False

    def reloadConnections(self) -> None:
        pass

    def addProject(self, project: Optional[str]) -> bool:
        pass

    def addTiledSceneLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional["qgis_core.QgsTiledSceneLayer"]:
        pass

    def addPointCloudLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsPointCloudLayer]:
        pass

    def addVectorTileLayer(
        self, url: Optional[str], baseName: Optional[str]
    ) -> Optional[qgis_core.QgsVectorTileLayer]:
        pass

    def addMeshLayer(
        self, url: Optional[str], baseName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsMeshLayer]:
        pass

    @typing.overload
    def addRasterLayer(
        self, rasterLayerPath: Optional[str], baseName: Optional[str] = None
    ) -> Optional[qgis_core.QgsRasterLayer]:
        pass

    @typing.overload
    def addRasterLayer(
        self, url: Optional[str], layerName: Optional[str], providerKey: Optional[str]
    ) -> Optional[qgis_core.QgsRasterLayer]:
        pass

    def addRasterLayer(
        self, *args: str, **kwargs: dict[str, str]
    ) -> Optional[qgis_core.QgsRasterLayer]:
        layer = qgis_core.QgsRasterLayer(*args, **kwargs)
        self.addLayers([layer])
        return layer

    def addVectorLayer(
        self,
        vectorLayerPath: Optional[str],
        baseName: Optional[str],
        providerKey: Optional[str],
    ) -> Optional[qgis_core.QgsVectorLayer]:
        layer = QgsVectorLayer(vectorLayerPath, baseName, providerKey)
        self.addLayers([layer])
        return layer

    def zoomToActiveLayer(self) -> None:
        pass

    def zoomToNext(self) -> None:
        pass

    def zoomToPrevious(self) -> None:
        pass

    def zoomFull(self) -> None:
        pass

    def userProfileManager(self) -> Optional["qgis_core.QgsUserProfileManager"]:
        pass

    def layerTreeInsertionPoint(
        self,
    ) -> qgis_core.QgsLayerTreeRegistryBridge.InsertionPoint:
        pass

    def takeAppScreenShots(
        self, saveDirectory: Optional[str], categories: int = ...
    ) -> None:
        pass

    def statusBarIface(self) -> Optional["QgsStatusBar"]:
        pass

    def messageTimeout(self) -> int:
        pass

    def vectorLayerTools(self) -> Optional[qgis_core.QgsVectorLayerTools]:
        pass

    def actionRegularPolygonCenterCorner(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRegularPolygonCenterPoint(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRegularPolygon2Points(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRectangle3PointsProjected(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRectangle3PointsDistance(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRectangleExtent(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRectangleCenterPoint(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionEllipseFoci(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionEllipseExtent(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionEllipseCenterPoint(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionEllipseCenter2Points(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCircleCenterPoint(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCircle2TangentsPoint(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCircle3Tangents(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCircle3Points(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCircle2Points(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAbout(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCheckQgisVersion(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionQgisHomePage(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionHelpContents(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCustomProjection(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionOptions(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionToggleFullScreen(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionShowPythonDialog(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionPluginListSeparator(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionManagePlugins(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionShowSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionHideDeselectedLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionToggleSelectedLayersIndependently(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionToggleSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionHideSelectedLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionShowAllLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionHideAllLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRemoveAllFromOverview(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddAllToOverview(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddToOverview(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionLayerProperties(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionDuplicateLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionLayerSaveAs(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCancelAllEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCancelEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRollbackAllEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionRollbackEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveAllEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAllEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveActiveLayerEdits(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionToggleEditing(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionOpenStatisticalSummary(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionOpenFieldCalculator(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionOpenTable(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionPasteLayerStyle(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCopyLayerStyle(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddAmsLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddAfsLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddPointCloudLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddVectorTileLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddXyzLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddWmsLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddPgLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddRasterLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddOgrLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionNewVectorLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionDraw(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionShowBookmarks(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionNewBookmark(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionMapTips(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomActualSize(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomNext(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomLast(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomToSelected(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomToLayers(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomToLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomFullExtent(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionMeasureArea(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionMeasure(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionFeatureAction(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionIdentify(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSelectRadius(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSelectFreehand(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSelectPolygon(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSelectRectangle(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSelect(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomOut(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionZoomIn(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionPanToSelected(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionPan(self) -> Optional[QtWidgets.QAction]:
        pass

    def mapToolActionGroup(self) -> Optional[QtWidgets.QActionGroup]:
        pass

    def actionVertexToolActiveLayer(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionVertexTool(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionDeletePart(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionDeleteRing(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSimplifyFeature(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddPart(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddRing(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSplitParts(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSplitFeatures(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionMoveFeature(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionDeleteSelected(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionAddFeature(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionPasteFeatures(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCopyFeatures(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCutFeatures(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionExit(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionShowLayoutManager(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionCreatePrintLayout(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionProjectProperties(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveMapAsImage(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveProjectAs(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionSaveProject(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionOpenProject(self) -> Optional[QtWidgets.QAction]:
        pass

    def actionNewProject(self) -> Optional[QtWidgets.QAction]:
        pass

    def webToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def databaseToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def vectorToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def rasterToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def helpToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def pluginToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def selectionToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def attributesToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def shapeDigitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def advancedDigitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def digitizeToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def mapNavToolToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def openDataSourceManagerPage(self, pageName: Optional[str]) -> None:
        pass

    def dataSourceManagerToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def layerToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def fileToolBar(self) -> Optional[QtWidgets.QToolBar]:
        pass

    def helpMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def windowMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def firstRightStandardMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def webMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def vectorMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def databaseMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def rasterMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def pluginHelpMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def pluginMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def settingsMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def addLayerMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def newLayerMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def layerMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def viewMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def editMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def removeProjectExportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def addProjectExportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def removeProjectImportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def addProjectImportAction(self, action: Optional[QtWidgets.QAction]) -> None:
        pass

    def projectImportExportMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def projectMenu(self) -> Optional[QtWidgets.QMenu]:
        pass

    def cadDockWidget(self) -> Optional["QgsAdvancedDigitizingDockWidget"]:
        pass

    def defaultStyleSheetFont(self) -> QtGui.QFont:
        pass

    def defaultStyleSheetOptions(self) -> dict[str, Any]:
        pass

    def openLayoutDesigners(self) -> list["QgsLayoutDesignerInterface"]:
        pass

    def messageBar(self) -> Optional["QgsMessageBar"]:
        return self._messageBar

    def mainWindow(self) -> Optional[QtWidgets.QWidget]:
        return self._mainWindow

    def layerTreeCanvasBridge(self) -> Optional["QgsLayerTreeMapCanvasBridge"]:
        pass

    def activeDecorations(self) -> list[qgis_core.QgsMapDecoration]:
        pass

    def mapCanvas(self) -> "QgsMapCanvas":
        return self.canvas

    def activeLayer(self) -> Optional[qgis_core.QgsMapLayer]:
        return (
            QgsProject.instance().mapLayer(self._active_layer_id)
            if self._active_layer_id
            else None
        )

    def editableLayers(self, modified: bool = ...) -> list[qgis_core.QgsMapLayer]:
        pass

    def iconSize(self, dockedToolbar: bool = ...) -> QtCore.QSize:
        pass

    def closeMapCanvas(self, name: Optional[str]) -> None:
        pass

    def createNewMapCanvas(self, name: Optional[str]) -> Optional["QgsMapCanvas"]:
        pass

    def mapCanvases(self) -> list["QgsMapCanvas"]:
        return [self.mapCanvas()]

    def removeCustomActionForLayerType(
        self, action: Optional[QtWidgets.QAction]
    ) -> bool:
        pass

    def addCustomActionForLayer(
        self,
        action: Optional[QtWidgets.QAction],
        layer: Optional[qgis_core.QgsMapLayer],
    ) -> None:
        pass

    def addCustomActionForLayerType(
        self,
        action: Optional[QtWidgets.QAction],
        menu: Optional[str],
        type: "qgis_core.Qgis.LayerType",
        allLayers: bool,
    ) -> None:
        pass

    def layerTreeView(self) -> Optional["QgsLayerTreeView"]:
        pass

    def pluginManagerInterface(self) -> Optional["QgsPluginManagerInterface"]:
        pass
