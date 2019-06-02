"""A simple application to label images of faces."""
import sys
import json
from pkg_resources import resource_filename
from PyQt5 import QtCore, QtGui, QtWidgets


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

WIDTH = 800
HEIGHT = 800


def read_json(fname):
    with open(fname) as fid:
        data = json.load(fid)
    return data


class Marker(QtWidgets.QGraphicsPathItem):
    """This class is the point we move to indicate a landmark position."""
    cross = QtGui.QPainterPath()
    cross.addRect(QtCore.QRectF(0, -5, 0, 10))
    cross.addRect(QtCore.QRectF(-5, 0, 10, 0))

    square = QtGui.QPainterPath()
    square.addRect(QtCore.QRectF(-5, -5, 10, 10))
    square.addRect(QtCore.QRectF(0, -5, 0, 10))
    square.addRect(QtCore.QRectF(-5, 0, 10, 0))

    red_pen = QtGui.QPen(QtGui.QColor("red"), 0.5)
    grn_pen = QtGui.QPen(QtGui.QColor("green"), 0.5)

    def __init__(self, group_item, index):
        super(Marker, self).__init__()
        self.m_group_item = group_item
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
            self.m_group_item.movePoint(self.m_index, value)
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

    def add_points(self, pts):
        for x, y in pts:
            self.addPoint(QtCore.QPointF(x, y))

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


class LabelerScene(QtWidgets.QGraphicsScene):
    """Inherit Graphics Scene to allow adding of LineGroup objects."""
    def __init__(self, parent):
        super(LabelerScene, self).__init__(parent)
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.addItem(self.image)
        self.setSceneRect(QtCore.QRectF(0, 0, WIDTH, HEIGHT))
        self.groups = []

    def add_group(self, pts, label=None):
        group = LineGroup()
        if label:
            group.setToolTip(label)
        self.addItem(group)
        group.add_points(pts)
        self.groups.append(group)
        return group

    def add_model(self, model):
        pass

    def print_pos(self):
        pos = []
        for group in self.groups:
            for item in group.m_items:
                pos.append([item.pos().x(), item.pos().x()])
        print(pos)

    def set_image(self, pixmap=None):
        if pixmap and not pixmap.isNull():
            self.image.setPixmap(pixmap)
            self.setSceneRect(QtCore.QRectF(self.image.pixmap().rect()))
        else:
            self.image.setPixmap(QtGui.QPixmap())

# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class LabelerView(QtWidgets.QGraphicsView):

    def __init__(self, parent=None):
        super(LabelerView, self).__init__(parent)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setRenderHints(QtGui.QPainter.Antialiasing |
                            QtGui.QPainter.SmoothPixmapTransform)
        self.setMouseTracking(True)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def fitInView(self):
        self.resetTransform()
        self.scale(1.0, 1.0)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)


# -----------------------------------------------------------------------------
# Main Window
# -----------------------------------------------------------------------------


class imageLabelerWindow(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(imageLabelerWindow, self).__init__()

        self.scene = LabelerScene(self)
        self.scene.add_group([[10, 20], [20, 30], [30, 40]], "left_eye")
        self.scene.add_group([[50, 60], [70, 80], [90, 100]], "right_eye")

        self.viewer = LabelerView()
        self.viewer.setScene(self.scene)
        self.setCentralWidget(self.viewer)

        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(WIDTH, HEIGHT)
        self.show()

    def about(self):
        msg = """Face Label Tool Help:"""
        QtWidgets.QMessageBox.about(self, "About Image Viewer", msg)

    def createMenus(self):
        self.openAct = QtWidgets.QAction(
            "Open...", self, shortcut="Ctrl+O", triggered=self.open_img)
        self.modelAct = QtWidgets.QAction(
            "Open Model...", self, shortcut="Ctrl+M", triggered=self.open_mdl)
        self.exitAct = QtWidgets.QAction(
            "Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.aboutAct = QtWidgets.QAction(
            "About", self, triggered=self.about)
        self.fitAct = QtWidgets.QAction(
            "View 100%", self, shortcut="Ctrl+F",
            triggered=self.viewer.fitInView)
        self.printAct = QtWidgets.QAction(
            "Print Positions", self, shortcut="Ctrl+P",
            triggered=self.scene.print_pos)

        self.fileMenu = QtWidgets.QMenu("File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.modelAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtWidgets.QMenu("View", self)
        self.viewMenu.addAction(self.fitAct)
        self.fileMenu.addSeparator()

        self.helpMenu = QtWidgets.QMenu("Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().setNativeMenuBar(True)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def open_mdl(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Model File", QtCore.QDir.currentPath())
        if not fname:
            return
        model = read_json(fname)
        self.scene.add_model(model)

    def open_img(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image", QtCore.QDir.currentPath())
        if not fname:
            return
        image = QtGui.QImage(fname)
        if image.isNull():
            QtWidgets.QMessageBox.information(
                self, "Image Viewer", "Cannot load %s." % fname)
            return
        self.scene.set_image(QtGui.QPixmap.fromImage(image))


if __name__ == '__main__':
    app = QtWidgets.QApplication(["Face Label Tool"] + sys.argv[1:])
    path = resource_filename(__name__, "icon.png")
    app.setWindowIcon(QtGui.QIcon(path))
    ui = imageLabelerWindow()
    sys.exit(app.exec_())
