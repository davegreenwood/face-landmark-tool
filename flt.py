"""A simple aplication to label images of faces."""
import sys
import json
import numpy as np
from pkg_resources import resource_filename
from PyQt5 import QtCore, QtGui, QtWidgets


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


class Marker(QtWidgets.QGraphicsPathItem):

    cross = QtGui.QPainterPath()
    cross.addRect(QtCore.QRectF(0, -5, 0, 10))
    cross.addRect(QtCore.QRectF(-5, 0, 10, 0))

    square = QtGui.QPainterPath()
    square.addRect(QtCore.QRectF(-5, -5, 10, 10))
    square.addRect(QtCore.QRectF(0, -5, 0, 10))
    square.addRect(QtCore.QRectF(-5, 0, 10, 0))

    red_pen = QtGui.QPen(QtGui.QColor("red"), 0.5)
    grn_pen = QtGui.QPen(QtGui.QColor("green"), 0.5)

    def __init__(self, annotation_item, index):
        super(Marker, self).__init__()
        self.m_annotation_item = annotation_item
        self.m_index = index

        self.setPath(Marker.cross)
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setPen(self.grn_pen)

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(11)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def hoverEnterEvent(self, event):
        self.setPath(Marker.square)
        self.setPen(self.red_pen)
        self.setBrush(QtGui.QColor(255, 0, 0, 32))
        super(Marker, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPath(Marker.cross)
        self.setPen(self.grn_pen)
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        super(Marker, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setSelected(False)
        super(Marker, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if (change == QtWidgets.QGraphicsItem.ItemPositionChange and
                self.isEnabled()):
            self.m_annotation_item.movePoint(self.m_index, value)
        return super(Marker, self).itemChange(change, value)


class LineGroup(QtWidgets.QGraphicsPathItem):

    red_pen = QtGui.QPen(QtGui.QColor("red"), 0.5)
    grn_pen = QtGui.QPen(QtGui.QColor("green"), 0.5)

    def __init__(self, parent=None):
        super(LineGroup, self).__init__(parent)
        self.setPen(self.grn_pen)
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.m_points = []
        self.m_items = []

    def set_path(self):
        painter_path = QtGui.QPainterPath()
        painter_path.addPolygon(QtGui.QPolygonF(self.m_points))
        self.setPath(painter_path)

    def addPoint(self, p):
        self.m_points.append(p)
        self.set_path()
        item = Marker(self, len(self.m_points) - 1)
        self.scene().addItem(item)
        self.m_items.append(item)
        item.setPos(p)

    def movePoint(self, index, pos):
        if 0 <= index < len(self.m_points):
            self.m_points[index] = self.mapFromScene(pos)
            self.set_path()

    def move_item(self, index, pos):
        if 0 <= index < len(self.m_items):
            item = self.m_items[index]
            item.setEnabled(False)
            item.setPos(pos)
            item.setEnabled(True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for i, point in enumerate(self.m_points):
                self.move_item(i, self.mapToScene(point))
        return super(LineGroup, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        self.setPen(self.red_pen)
        super(LineGroup, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self.grn_pen)
        super(LineGroup, self).hoverLeaveEvent(event)


# -----------------------------------------------------------------------------
# Graphics Scene
# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class ImageView(QtWidgets.QGraphicsView):

    def __init__(self, parent):
        super(ImageView, self).__init__(parent)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.image)
        self.line = LineGroup()
        self.scene.addItem(self.line)
        for x, y in [[10, 20], [20, 30], [30, 40]]:
            self.line.addPoint(QtCore.QPointF(x, y))
        self.setScene(self.scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self.image.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
        self.resetTransform()
        self.scale(1.0, 1.0)

    def setPhoto(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.image.setPixmap(pixmap)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.image.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self.image.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)


# -----------------------------------------------------------------------------
# Window Class
# -----------------------------------------------------------------------------


class imageLabelerWindow(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(imageLabelerWindow, self).__init__()
        self.viewer = ImageView(self)
        self.setCentralWidget(self.viewer)
        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(800, 800)
        self.show()

    def about(self):
        msg = """Face Label Tool Help:"""
        QtWidgets.QMessageBox.about(self, "About Image Viewer", msg)

    def createMenus(self):
        self.openAct = QtWidgets.QAction(
            "Open...", self, shortcut="Ctrl+O", triggered=self.open_image)
        self.exitAct = QtWidgets.QAction(
            "Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QtWidgets.QAction(
            "About", self, triggered=self.about)
        self.fitAct = QtWidgets.QAction(
            "Fit to view", self, shortcut="Ctrl+F",
            triggered=self.viewer.fitInView)

        self.fileMenu = QtWidgets.QMenu("File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtWidgets.QMenu("View", self)
        self.viewMenu.addAction(self.fitAct)

        self.helpMenu = QtWidgets.QMenu("Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().setNativeMenuBar(True)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def open_landmarks(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Landmark FIle", QtCore.QDir.currentPath())
        if not fname:
            return
        self.landmarks = read_json(fname)

    def open_image(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image", QtCore.QDir.currentPath())
        if not fname:
            return

        image = QtGui.QImage(fname)
        if image.isNull():
            QtWidgets.QMessageBox.information(
                self, "Image Viewer", "Cannot load %s." % fname)
            return
        self.viewer.setPhoto(QtGui.QPixmap.fromImage(image))


if __name__ == '__main__':
    app = QtWidgets.QApplication(["Face Label Tool"])
    path = resource_filename(__name__, "icon.png")
    app.setWindowIcon(QtGui.QIcon(path))
    ui = imageLabelerWindow()
    sys.exit(app.exec_())
