"""A simple application to label images of faces."""
import sys
import os
from pkg_resources import resource_filename
from PyQt5 import QtCore, QtGui, QtWidgets

from .model import model, read_json, write_json

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


WIDTH = 800
HEIGHT = 800
MARGIN = 10


class Pen:
    line = 1.0
    red_pen = QtGui.QPen(QtGui.QColor("red"), line)
    grn_pen = QtGui.QPen(QtGui.QColor("green"), line)
    yel_pen = QtGui.QPen(QtGui.QColor("yellow"), line)

    @classmethod
    def set_line(cls, line_width):
        cls.line = line_width
        cls.red_pen = QtGui.QPen(QtGui.QColor("red"), cls.line)
        cls.grn_pen = QtGui.QPen(QtGui.QColor("green"), cls.line)
        cls.yel_pen = QtGui.QPen(QtGui.QColor("yellow"), cls.line)

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


class Marker(QtWidgets.QGraphicsPathItem):
    """This class is the point we move to indicate a landmark position."""
    cross = QtGui.QPainterPath()
    cross.addRect(QtCore.QRectF(0, -5, 0, 10))
    cross.addRect(QtCore.QRectF(-5, 0, 10, 0))

    square = QtGui.QPainterPath()
    square.addRect(QtCore.QRectF(-5, -5, 10, 10))
    square.addRect(QtCore.QRectF(0, -5, 0, 10))
    square.addRect(QtCore.QRectF(-5, 0, 10, 0))

    def __init__(self, group_item, index):
        super(Marker, self).__init__()
        self.m_group_item = group_item
        self.m_index = index
        self.setPath(Marker.cross)
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setPen(self.default_pen())

        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(20)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def default_pen(self):
        """return yellow pen for first Marker, else green. """
        return Pen.yel_pen if self.m_index == 0 else Pen.grn_pen

    def hoverEnterEvent(self, event):
        """Override super."""
        self.setPath(Marker.square)
        self.setPen(Pen.red_pen)
        self.setBrush(QtGui.QColor(255, 0, 0, 32))
        super(Marker, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Override super."""
        self.setPath(Marker.cross)
        self.setPen(self.default_pen())
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        super(Marker, self).hoverLeaveEvent(event)

    def mouseReleaseEvent(self, event):
        """Override super."""
        self.setSelected(False)
        super(Marker, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """Override super."""
        if (change == QtWidgets.QGraphicsItem.ItemPositionChange and
                self.isEnabled()):
            self.m_group_item.move_point(self.m_index, value)
        return super(Marker, self).itemChange(change, value)

    def shape(self):
        """Override super."""
        qp = QtGui.QPainterPathStroker()
        qp.setWidth(MARGIN)
        qp.setCapStyle(QtCore.Qt.SquareCap)
        shape = qp.createStroke(self.path())
        return shape

    def update(self):
        """Override super."""
        self.setPen(self.default_pen())
        super(Marker, self).update()


class LineGroup(QtWidgets.QGraphicsPathItem):
    """This class groups the points to semantic regions, eg: right eye... """

    def __init__(self, parent=None):
        super(LineGroup, self).__init__(parent)
        self.setPen(Pen.grn_pen)
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
        """Set the painter path from the stored points."""
        painter_path = QtGui.QPainterPath()
        painter_path.addPolygon(QtGui.QPolygonF(self.m_points))
        self.setPath(painter_path)

    def add_point(self, p):
        """Add a single point. """
        self.m_points.append(p)
        self.set_path()
        item = Marker(self, len(self.m_points) - 1)
        self.scene().addItem(item)
        self.m_items.append(item)
        item.setPos(p)

    def delete_markers(self):
        """Fully delete the group markers."""
        while self.m_items:
            item = self.m_items.pop(0)
            self.scene().removeItem(item)
            del item

    def add_points(self, pts):
        """Add points from a list of (x, y) tuples."""
        for x, y in pts:
            self.add_point(QtCore.QPointF(x, y))

    def move_point(self, index, pos):
        """Move a point and update the painter path."""
        if 0 <= index < len(self.m_points):
            self.m_points[index] = self.mapFromScene(pos)
            self.set_path()

    def move_item(self, index, pos):
        """Move the marker item """
        if 0 <= index < len(self.m_items):
            item = self.m_items[index]
            item.setEnabled(False)
            item.setPos(pos)
            item.setEnabled(True)

    def shape(self):
        """Override super."""
        qp = QtGui.QPainterPathStroker()
        qp.setWidth(MARGIN)
        qp.setCapStyle(QtCore.Qt.SquareCap)
        shape = qp.createStroke(self.path())
        return shape

    def itemChange(self, change, value):
        """Override super."""
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for i, point in enumerate(self.m_points):
                self.move_item(i, self.mapToScene(point))
        return super(LineGroup, self).itemChange(change, value)

    def hoverEnterEvent(self, event):
        """Override super."""
        self.setPen(Pen.red_pen)
        super(LineGroup, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Override super."""
        self.setPen(Pen.grn_pen)
        super(LineGroup, self).hoverLeaveEvent(event)

    def update(self):
        """Override super"""
        self.setPen(Pen.grn_pen)
        for item in self.m_items:
            item.update()
        super(LineGroup, self).update()


class Model:
    """Landmarking model"""

    def __init__(self, scene=None):
        super(Model, self).__init__()
        self.scene = scene
        self.groups = []
        self.positions = []
        self.load_model()

    def load_model(self, model_dict=model):
        """Load a model from a dictionary."""
        self.delete_model()
        self.index = model_dict["index"]
        self.positions = model_dict["pos"]
        self.keys = model_dict["keys"]
        for key in self.keys:
            self.add_group([self.positions[i] for i in self.index[key]], key)

    def delete_model(self):
        """Fully delete a model."""
        while self.groups:
            group = self.groups.pop(0)
            group.delete_markers()
            self.scene.removeItem(group)
            del group

    def select_model(self):
        """Select all the groups in the model."""
        for group in self.groups:
            group.setSelected(True)

    def deselect_model(self):
        """Deselect all the groups in the model."""
        for group in self.groups:
            group.setSelected(False)

    def scale_model(self, factor):
        """Scale the model by a factor."""
        pos = [[factor * p[0], factor * p[1]] for p in self.get_positions()]
        self.load_model(dict(index=self.index, keys=self.keys, pos=pos))

    def add_group(self, pts, label=None):
        """Add a new group to the model."""
        group = LineGroup()
        if label:
            group.setToolTip(label)
        self.scene.addItem(group)
        group.add_points(pts)
        self.groups.append(group)
        return group

    def get_positions(self):
        """Get the positions of all the markers in all the groups."""
        self.positions = []
        for group in self.groups:
            for item in group.m_items:
                self.positions.append([item.pos().x(), item.pos().y()])
        return self.positions

    def to_dict(self):
        """Return a dictionary of the model."""
        return dict(index=self.index, keys=self.keys,
                    pos=self.get_positions())

    def update(self):
        """Redraw the model as soon as possilble."""
        for group in self.groups:
            group.update()


# -----------------------------------------------------------------------------
# Graphics Scene
# -----------------------------------------------------------------------------


class LabelerScene(QtWidgets.QGraphicsScene):
    """Inherit Graphics Scene to allow adding of LineGroup objects."""

    def __init__(self, parent):
        super(LabelerScene, self).__init__(parent)
        self.image = QtWidgets.QGraphicsPixmapItem()
        self.image_fname = "no_image"
        self.model = Model(scene=self)
        self.addItem(self.image)
        self.setSceneRect(QtCore.QRectF(0, 0, WIDTH, HEIGHT))

    def print_pos(self):
        """Print the image file name and (x, y) positions of the markers."""
        self.model.get_positions()
        pos = ", ".join(
            [f"[{x:0.2f}, {y:0.2f}]" for x, y in self.model.positions])
        print(f'"{self.image_fname:}" : [{pos}]')

    def set_image(self, fname):
        """Set the image in the scene from a filename."""
        self.image.setPixmap(QtGui.QPixmap(fname))
        self.setSceneRect(self.image.boundingRect())
        _, self.image_fname = os.path.split(fname)

    def update(self):
        """Override super"""
        self.model.update()
        super(LabelerScene, self).update()


# -----------------------------------------------------------------------------
# Graphics View
# -----------------------------------------------------------------------------


class LabelerView(QtWidgets.QGraphicsView):
    """The view on the model. """
    factor = 1.25

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
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+="),
                            self, activated=self.zoomIn)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+-"),
                            self, activated=self.zoomOut)

        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+="),
                            self, activated=self.scale_up)
        QtWidgets.QShortcut(QtGui.QKeySequence("Alt+-"),
                            self, activated=self.scale_down)

        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+1"),
                            self, activated=self.line_s)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+2"),
                            self, activated=self.line_m)
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+3"),
                            self, activated=self.line_l)

    def update(self):
        """update the view"""
        self.scene().update()
        super(LabelerView, self).update()

    @QtCore.pyqtSlot()
    def line_s(self):
        """Line width 0.5 """
        line_width = 0.5
        Pen.set_line(line_width)
        self.update()

    @QtCore.pyqtSlot()
    def line_m(self):
        """Line width 1.0 """
        line_width = 1.0
        Pen.set_line(line_width)
        self.update()

    @QtCore.pyqtSlot()
    def line_l(self):
        """Line width 2.0 """
        line_width = 2.0
        Pen.set_line(line_width)
        self.update()

    @QtCore.pyqtSlot()
    def scale_up(self):
        """Zoom in."""
        f = LabelerView.factor
        self.scene().model.scale_model(f)

    @QtCore.pyqtSlot()
    def scale_down(self):
        """Zoom out."""
        f = 1. / LabelerView.factor
        self.scene().model.scale_model(f)

    @QtCore.pyqtSlot()
    def zoomIn(self):
        """Zoom in."""
        self.zoom(LabelerView.factor)

    @QtCore.pyqtSlot()
    def zoomOut(self):
        """Zoom out."""
        self.zoom(1. / LabelerView.factor)

    def zoom(self, factor):
        """Zoom by factor."""
        self.scale(factor, factor)
        if self.scene() is not None:
            self.centerOn(self.scene().image)

    def fitInView(self):
        """Fit to 100 %"""
        self.resetTransform()
        self.scale(1.0, 1.0)

    def wheelEvent(self, event):
        """scroll to zoom"""
        if event.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()


# -----------------------------------------------------------------------------
# Main Window
# -----------------------------------------------------------------------------


class ImageLabelerWindow(QtWidgets.QMainWindow):
    """The main application window with menu items."""

    def __init__(self):
        super(ImageLabelerWindow, self).__init__()
        self.scene = LabelerScene(self)
        self.viewer = LabelerView()
        self.viewer.setScene(self.scene)
        self.setCentralWidget(self.viewer)
        self.createMenus()
        self.setWindowTitle("Face Label Tool (FLT)")
        self.resize(WIDTH, HEIGHT)
        self.show()

    def about(self):
        """Show help. """
        msg = (
            'Zoom using "Ctrl +" and "Ctrl -" or scroll\n' +
            'Select all with "Ctrl A", deslect with "Ctrl D"\n' +
            '"Ctrl" click to add to selection\n' +
            'Scale model using "Alt +" and "Alt -"\n' +
            'Set line width with "Ctrl 1", "Ctrl 2", "Ctrl 3"\n')

        QtWidgets.QMessageBox.about(self, "Hotkeys", msg)

    def createMenus(self):
        """Build the menus."""
        open_act = QtWidgets.QAction(
            "Open Image...", self, shortcut="Ctrl+O", triggered=self.open_img)
        model_act = QtWidgets.QAction(
            "Open Model...", self, shortcut="Ctrl+M", triggered=self.open_mdl)
        save_act = QtWidgets.QAction(
            "Save Model...", self, shortcut="Ctrl+S", triggered=self.save_mdl)
        exit_act = QtWidgets.QAction(
            "Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        about_act = QtWidgets.QAction(
            "Hotkeys", self, triggered=self.about)
        select_act = QtWidgets.QAction(
            "Select Model", self, shortcut="Ctrl+A",
            triggered=self.scene.model.select_model)
        deselect_act = QtWidgets.QAction(
            "Deselect Model", self, shortcut="Ctrl+D",
            triggered=self.scene.model.deselect_model)
        fitAct = QtWidgets.QAction(
            "View 100%", self, shortcut="Ctrl+F",
            triggered=self.viewer.fitInView)
        printAct = QtWidgets.QAction(
            "Print Positions", self, shortcut="Ctrl+P",
            triggered=self.scene.print_pos)

        self.fileMenu = QtWidgets.QMenu("File", self)
        self.fileMenu.addAction(open_act)
        self.fileMenu.addAction(model_act)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(save_act)
        self.fileMenu.addAction(printAct)
        self.fileMenu.addAction(exit_act)

        self.editMenu = QtWidgets.QMenu("Edit", self)
        self.editMenu.addAction(select_act)
        self.editMenu.addAction(deselect_act)

        self.viewMenu = QtWidgets.QMenu("View", self)
        self.viewMenu.addAction(fitAct)
        self.viewMenu.addSeparator()

        self.helpMenu = QtWidgets.QMenu("Help", self)
        self.helpMenu.addAction(about_act)

        self.menuBar().setNativeMenuBar(False)
        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def open_mdl(self):
        """Open a model using the file dialogue."""
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Model File", QtCore.QDir.currentPath())
        if not fname:
            return
        model_in = read_json(fname)
        self.scene.model.load_model(model_in)

    def save_mdl(self):
        """Save a model using the file dialogue."""
        img = self.scene.image_fname.split(".")[0]
        default_name = os.path.join(QtCore.QDir.currentPath(), f"{img}.json")
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Model File", default_name)
        if not fname:
            return
        model_out = self.scene.model.to_dict()
        write_json(model_out, fname)

    def open_img(self):
        """Open an image using the file dialogue."""
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image", QtCore.QDir.currentPath())
        if not fname:
            return
        image = QtGui.QImage(fname)
        if image.isNull():
            QtWidgets.QMessageBox.information(
                self, "Face Label Tool", "Cannot load %s." % fname)
            return
        self.scene.set_image(fname)


def main():
    """Run the application."""
    app = QtWidgets.QApplication(["Face Label Tool"] + sys.argv[1:])
    path = resource_filename(__name__, "data/icon.png")
    app.setWindowIcon(QtGui.QIcon(path))
    _ = ImageLabelerWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
