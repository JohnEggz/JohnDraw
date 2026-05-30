import time
import base64
import math
from collections import deque
from enum import Enum
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QLabel, QGraphicsPathItem, QGraphicsItem, QStyle, QGraphicsPixmapItem
from PySide6.QtGui import (QPainter, QPen, QColor, QFont, 
                           QPainterPath, QPixmap, QBrush, QSurfaceFormat, QPolygonF, QImage)
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF, QBuffer, QIODevice, QEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# --- CONFIGURATION ---
VISUAL_GRID_SIZE = 40
SIMPLIFY_TOLERANCE = 0.5  # Reverted back to 0.5 for massive rendering performance gains
FRAME_BUDGET_MS = 16.67 

# --- COMMAND PATTERN (DELTA UNDO/REDO) ---
class Command:
    def undo(self): pass
    def redo(self): pass

class AddItemCommand(Command):
    def __init__(self, scene, item):
        self.scene = scene
        self.item = item
    def undo(self): 
        self.scene.removeItem(self.item)
    def redo(self): 
        self.scene.addItem(self.item)

class RemoveItemCommand(Command):
    def __init__(self, scene, items):
        self.scene = scene
        self.items = items
    def undo(self):
        for item in self.items: 
            self.scene.addItem(item)
    def redo(self):
        for item in self.items: 
            self.scene.removeItem(item)

class TransformCommand(Command):
    def __init__(self, start_states, end_states):
        self.start_states = start_states # list of dicts: {'item': item, 'pos': QPointF, 'scale': float}
        self.end_states = end_states
    def undo(self):
        for state in self.start_states:
            state['item'].setPos(state['pos'])
            state['item'].setScale(state['scale'])
    def redo(self):
        for state in self.end_states:
            state['item'].setPos(state['pos'])
            state['item'].setScale(state['scale'])

# --- GRAPHICS ITEMS ---
class StrokeItem(QGraphicsPathItem):
    """Custom path item that renders a glow when selected."""
    def __init__(self, path, pen, tool_type="stroke", parent=None):
        super().__init__(path, parent)
        self.setPen(pen)
        self.tool_type = tool_type
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        
    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        if self.isSelected():
            painter.save()
            glow_pen = QPen(QColor(155, 89, 182, 100), self.pen().width() + 6)
            glow_pen.setCapStyle(Qt.RoundCap)
            glow_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawPath(self.path())
            painter.restore()
        super().paint(painter, option, widget)

class IndependentProfiler:
    def __init__(self):
        self.rolling_window = deque(maxlen=60) 
        self.all_time_samples = []
        self.total_frames = 0
        self.missed_frames_total = 0
        self.pipeline_times = {}
        self.last_tick = time.perf_counter()
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.on_update = None 

    def tick(self):
        now = time.perf_counter()
        dt_ms = (now - self.last_tick) * 1000.0
        self.last_tick = now
        if dt_ms > 1000: return
        self.total_frames += 1
        self.rolling_window.append(dt_ms)
        self.all_time_samples.append(dt_ms)
        if dt_ms > FRAME_BUDGET_MS + 2.0:
            self.missed_frames_total += 1
        if self.on_update: self.on_update()

    def get_stats(self):
        rolling = list(self.rolling_window)
        return {
            "current": rolling[-1] if rolling else 0,
            "avg_1s": sum(rolling)/len(rolling) if rolling else 0,
            "stutter_perc": (self.missed_frames_total / self.total_frames * 100) if self.total_frames else 0,
        }

    def set_pipeline_time(self, label, duration_ms):
        self.pipeline_times[label] = duration_ms

def simplify_points(pts, tolerance):
    if len(pts) < 3: return pts
    sq_tol = tolerance**2
    def get_sq_dist(p, p1, p2):
        x, y, dx, dy = p1.x(), p1.y(), p2.x()-p1.x(), p2.y()-p1.y()
        if dx != 0 or dy != 0:
            t = ((p.x()-x)*dx + (p.y()-y)*dy) / (dx*dx+dy*dy)
            if t > 1: x, y = p2.x(), p2.y()
            elif t > 0: x, y = x+dx*t, y+dy*t
        return (p.x()-x)**2 + (p.y()-y)**2
    def step(first, last, simplified):
        max_sq, idx = sq_tol, 0
        for i in range(first + 1, last):
            d = get_sq_dist(pts[i], pts[first], pts[last])
            if d > max_sq: idx, max_sq = i, d
        if max_sq > sq_tol:
            step(first, idx, simplified)
            simplified.append(pts[idx])
            step(idx, last, simplified)
    simplified = [pts[0]]
    step(0, len(pts)-1, simplified)
    simplified.append(pts[-1])
    return simplified

class Tool(Enum):
    PEN = "PEN"
    TRAVEL = "TRAVEL"
    ERASER = "ERASER"
    LASSO = "LASSO"
    MOVE = "MOVE"
    RESIZE = "RESIZE"
    LINE = "LINE"
    CIRCLE = "CIRCLE"
    RECTANGLE = "RECTANGLE"

class Anchor(Enum):
    CENTER = "CENTER"
    VERTEX = "VERTEX"
    EDGE = "EDGE"

class InfiniteCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        gl_widget = QOpenGLWidget()
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        gl_widget.setFormat(fmt)
        self.setViewport(gl_widget)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setSceneRect(-100000, -100000, 200000, 200000)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        
        self.debug_label = QLabel(self)
        self.debug_label.setStyleSheet("background-color: rgba(0,0,0,210); color: white; padding: 10px; font-family: Monospace;")
        self.debug_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.debug_label.move(10, 10)
        self.debug_label.hide()
        
        self.profiler = IndependentProfiler()
        self.profiler.on_update = self.update_debug_text
        self.show_debug = False
        self.grid_texture = None
        self.current_tool = Tool.PEN
        self.current_anchor = Anchor.VERTEX
        self.tool_stack = []
        
        # Stacks for Delta Command tracking
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.current_erased_items = []
        self.transform_start_states = []
        
        self.pen_color = QColor(Qt.black)
        self.device_blacklist = []
        self.last_device_name = "None"
        self.lasso_path_item = None
        self.lasso_points = []
        
        self.resize_anchor = QPointF()
        self.resize_initial_dist = 1.0
        self.resize_items_start_state = []

        self.reset_canvas()
        QTimer.singleShot(0, self._create_grid_texture)

    def go_home(self):
        v_size = self.viewport().size()
        target_center = QPointF(v_size.width() / 2, v_size.height() / 2)
        self.centerOn(target_center)

    def push_tool(self, tool):
        self.tool_stack.append(self.current_tool)
        self.current_tool = tool

    def pop_tool(self):
        if self.tool_stack:
            self.current_tool = self.tool_stack.pop()
        else:
            self.current_tool = Tool.PEN
        return self.current_tool

    def save_history(self):
        """Maintains API compatibility with the main application. 
        History is now automatically handled via delta commands."""
        pass

    def push_command(self, command):
        """Pushes a delta command to the stack."""
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)

    def redo(self):
        if not self.redo_stack: return
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)

    def _create_grid_texture(self):
        s = VISUAL_GRID_SIZE
        pix = QPixmap(s, s)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setPen(QPen(QColor("#ddd"), 1))
        p.drawLine(0, 0, s, 0)
        p.drawLine(0, 0, 0, s)
        p.end()
        self.grid_texture = QBrush(pix)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#f5f5f5"))
        if self.grid_texture:
            painter.fillRect(rect, self.grid_texture)
        painter.save()
        axis_pen = QPen(QColor("#e74c3c"), 1.5)
        axis_pen.setCosmetic(True) 
        painter.setPen(axis_pen)
        if rect.left() <= 0 <= rect.right():
            painter.drawLine(QPointF(0, rect.top()), QPointF(0, rect.bottom()))
        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), 0), QPointF(rect.right(), 0))
        painter.restore()

    def reset_canvas(self):
        self.scene.clear()
        self.current_stroke_pts = []
        self.current_stroke_item = None
        self.last_mouse_pos = QPointF()
        self.is_panning = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_erased_items = []
        self.transform_start_states = []

    def serialize(self, items=None):
        data = []
        target_items = items if items is not None else self.scene.items()
        for item in target_items:
            if item == self.lasso_path_item: continue
            if isinstance(item, StrokeItem):
                path = item.path()
                pts = []
                for i in range(path.elementCount()):
                    el = path.elementAt(i)
                    p = item.mapToScene(QPointF(el.x, el.y))
                    pts.append([round(p.x(), 2), round(p.y(), 2)])
                data.append({'t': 'stroke', 'p': pts, 'c': item.pen().color().name(), 'tool': item.tool_type})
            elif isinstance(item, QGraphicsPathItem):
                path = item.path()
                pts = []
                for i in range(path.elementCount()):
                    el = path.elementAt(i)
                    p = item.mapToScene(QPointF(el.x, el.y))
                    pts.append([round(p.x(), 2), round(p.y(), 2)])
                data.append({'t': 'stroke', 'p': pts, 'c': item.pen().color().name(), 'tool': 'stroke'})
            elif isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()
                ba = QBuffer()
                ba.open(QIODevice.WriteOnly)
                pixmap.save(ba, "PNG")
                b64 = base64.b64encode(ba.data().data()).decode()
                data.append({'t': 'image', 'data': b64, 'x': item.scenePos().x(), 'y': item.scenePos().y(), 's': item.scale()})
        return data

    def render_items_to_image(self, items):
        if not items: return QImage()
        selected_items = self.scene.selectedItems()
        self.scene.clearSelection()
        
        rect = QRectF()
        for it in items: rect = rect.united(it.sceneBoundingRect())
        rect.adjust(-5, -5, 5, 5)
        
        img = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter, target=QRectF(img.rect()), source=rect)
        painter.end()
        
        for it in selected_items:
            it.setSelected(True)
        return img

    def add_serialized_data(self, data, offset=QPointF(20, 20)):
        new_items = []
        for entry in data:
            if entry.get('t', 'stroke') == 'stroke':
                pts = [QPointF(p[0], p[1]) + offset for p in entry['p']]
                if not pts: continue
                tool_type = entry.get('tool', 'stroke')
                
                if tool_type == "stroke":
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    for p in pts[1:]: path.lineTo(p)
                elif tool_type == "line":
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    path.lineTo(pts[-1])
                elif tool_type == "circle":
                    path = QPainterPath()
                    path.addEllipse(QRectF(pts[0], pts[-1]).normalized())
                elif tool_type == "rectangle":
                    path = QPainterPath()
                    path.addRect(QRectF(pts[0], pts[-1]).normalized())
                else:
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    for p in pts[1:]: path.lineTo(p)
                
                pen = QPen(QColor(entry['c']), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                item = StrokeItem(path, pen, tool_type=tool_type)
                self.scene.addItem(item)
                new_items.append(item)
                self.push_command(AddItemCommand(self.scene, item))
            elif entry.get('t') == 'image':
                img_data = base64.b64decode(entry['data'])
                pix = QPixmap()
                pix.loadFromData(img_data)
                item = QGraphicsPixmapItem(pix)
                item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
                item.setPos(entry['x'] + offset.x(), entry['y'] + offset.y())
                item.setScale(entry.get('s', 1.0))
                self.scene.addItem(item)
                new_items.append(item)
                self.push_command(AddItemCommand(self.scene, item))
        return new_items

    def deserialize(self, data):
        self.reset_canvas()
        for entry in data:
            if entry.get('t', 'stroke') == 'stroke':
                pts = [QPointF(p[0], p[1]) for p in entry['p']]
                if not pts: continue
                tool_type = entry.get('tool', 'stroke')
                
                if tool_type == "stroke":
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    for p in pts[1:]: path.lineTo(p)
                elif tool_type == "line":
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    path.lineTo(pts[-1])
                elif tool_type == "circle":
                    path = QPainterPath()
                    path.addEllipse(QRectF(pts[0], pts[-1]).normalized())
                elif tool_type == "rectangle":
                    path = QPainterPath()
                    path.addRect(QRectF(pts[0], pts[-1]).normalized())
                else:
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    for p in pts[1:]: path.lineTo(p)
                
                pen = QPen(QColor(entry['c']), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                item = StrokeItem(path, pen, tool_type=tool_type)
                self.scene.addItem(item)
            elif entry.get('t') == 'image':
                img_data = base64.b64decode(entry['data'])
                pix = QPixmap()
                pix.loadFromData(img_data)
                item = QGraphicsPixmapItem(pix)
                item.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
                item.setPos(entry['x'], entry['y'])
                item.setScale(entry.get('s', 1.0))
                self.scene.addItem(item)
        self.viewport().update()

    def viewportEvent(self, event):
        if event.type() in [QEvent.TabletPress, QEvent.TabletMove, QEvent.TabletRelease, QEvent.TabletEnterProximity, QEvent.TabletLeaveProximity]:
            return super().viewportEvent(event)
        return super().viewportEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.position().toPoint()
        scene_pos = self.mapToScene(self.last_mouse_pos)
        
        if event.button() == Qt.RightButton or (event.button() == Qt.LeftButton and self.current_tool == Tool.TRAVEL):
            self.is_panning = True
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            
            if self.current_tool == Tool.ERASER:
                self.current_erased_items = [] # Reset tracking array for this swipe
                self._apply_eraser(scene_pos)
                
            elif self.current_tool in [Tool.MOVE, Tool.RESIZE]:
                selected = self.scene.selectedItems()
                if selected:
                    # Record the start state of all selected items for undo
                    self.transform_start_states = [{'item': it, 'pos': it.pos(), 'scale': it.scale()} for it in selected]
                    
                if self.current_tool == Tool.RESIZE and selected:
                    rect = QRectF()
                    for it in selected: rect = rect.united(it.sceneBoundingRect())
                    corners = {"tl": rect.topLeft(), "tr": rect.topRight(), "bl": rect.bottomLeft(), "br": rect.bottomRight()}
                    grabbed = min(corners, key=lambda k: (corners[k] - scene_pos).manhattanLength())
                    self.resize_anchor = corners[{"tl": "br", "tr": "bl", "bl": "tr", "br": "tl"}[grabbed]]
                    self.resize_initial_dist = max(1.0, (scene_pos - self.resize_anchor).manhattanLength())
                    self.resize_items_start_state = [{'item': it, 's': it.scale(), 'rel': it.pos() - self.resize_anchor} for it in selected]

            elif self.current_tool == Tool.PEN:
                self.scene.clearSelection()
                self.current_stroke_pts = [scene_pos]
                path = QPainterPath()
                path.moveTo(scene_pos)
                self.current_stroke_item = StrokeItem(path, QPen(self.pen_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin), tool_type="stroke")
                self.scene.addItem(self.current_stroke_item)
                
            elif self.current_tool == Tool.LASSO:
                self.scene.clearSelection()
                self.lasso_points = [scene_pos]
                self.lasso_path_item = self.scene.addPath(QPainterPath(scene_pos), QPen(QColor("#3498db"), 1, Qt.DashLine))
                
            elif self.current_tool == Tool.LINE:
                self.scene.clearSelection()
                self.current_stroke_pts = [scene_pos, scene_pos]
                path = QPainterPath()
                path.moveTo(scene_pos)
                path.lineTo(scene_pos)
                self.current_stroke_item = StrokeItem(path, QPen(self.pen_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin), tool_type="line")
                self.scene.addItem(self.current_stroke_item)
                
            elif self.current_tool in [Tool.CIRCLE, Tool.RECTANGLE]:
                self.scene.clearSelection()
                self.current_stroke_pts = [scene_pos, scene_pos]
                path = QPainterPath()
                tool_name = "circle" if self.current_tool == Tool.CIRCLE else "rectangle"
                if self.current_tool == Tool.CIRCLE:
                    path.addEllipse(QRectF(scene_pos, scene_pos))
                else:
                    path.addRect(QRectF(scene_pos, scene_pos))
                self.current_stroke_item = StrokeItem(path, QPen(self.pen_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin), tool_type=tool_name)
                self.scene.addItem(self.current_stroke_item)
        event.accept()

    def mouseMoveEvent(self, event):
        curr_pos_pixel = event.position().toPoint()
        scene_pos = self.mapToScene(curr_pos_pixel)
        if self.is_panning:
            delta = curr_pos_pixel - self.last_mouse_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = curr_pos_pixel
        elif (event.buttons() & Qt.LeftButton):
            if self.current_tool == Tool.ERASER:
                self._apply_eraser(scene_pos)
            elif self.current_tool == Tool.PEN and self.current_stroke_item:
                self.current_stroke_pts.append(scene_pos)
                path = QPainterPath()
                path.moveTo(self.current_stroke_pts[0])
                for pt in self.current_stroke_pts[1:]: path.lineTo(pt)
                self.current_stroke_item.setPath(path)
            elif self.current_tool == Tool.LASSO and self.lasso_path_item:
                self.lasso_points.append(scene_pos)
                path = QPainterPath()
                path.moveTo(self.lasso_points[0])
                for pt in self.lasso_points[1:]: path.lineTo(pt)
                self.lasso_path_item.setPath(path)
            elif self.current_tool == Tool.MOVE:
                delta = scene_pos - self.mapToScene(self.last_mouse_pos)
                for item in self.scene.selectedItems(): item.moveBy(delta.x(), delta.y())
                self.last_mouse_pos = curr_pos_pixel
            elif self.current_tool == Tool.RESIZE:
                factor = (scene_pos - self.resize_anchor).manhattanLength() / self.resize_initial_dist
                for s in self.resize_items_start_state:
                    s['item'].setScale(s['s'] * factor)
                    s['item'].setPos(self.resize_anchor + s['rel'] * factor)
                self.last_mouse_pos = curr_pos_pixel
            elif self.current_tool == Tool.LINE and self.current_stroke_item:
                p1 = self.current_stroke_pts[0]
                self.current_stroke_pts[1] = scene_pos
                path = QPainterPath()
                if self.current_anchor == Anchor.CENTER:
                    path.moveTo(p1 - (scene_pos - p1))
                else:
                    path.moveTo(p1)
                path.lineTo(scene_pos)
                self.current_stroke_item.setPath(path)
            elif self.current_tool in [Tool.CIRCLE, Tool.RECTANGLE] and self.current_stroke_item:
                p1 = self.current_stroke_pts[0]
                p2 = scene_pos
                self.current_stroke_pts[1] = p2
                
                if self.current_anchor == Anchor.CENTER:
                    rect = QRectF(p1 - (p2 - p1), p2).normalized()
                elif self.current_anchor == Anchor.EDGE:
                    dx = abs(p2.x() - p1.x())
                    dy = abs(p2.y() - p1.y())
                    if dx > dy:
                        rect = QRectF(p1.x(), p1.y() - dy, p2.x() - p1.x(), 2 * dy).normalized()
                    else:
                        rect = QRectF(p1.x() - dx, p1.y(), 2 * dx, p2.y() - p1.y()).normalized()
                else:
                    rect = QRectF(p1, p2).normalized()
                
                path = QPainterPath()
                if self.current_tool == Tool.CIRCLE:
                    path.addEllipse(rect)
                else:
                    path.addRect(rect)
                self.current_stroke_item.setPath(path)
        event.accept()

    def _apply_eraser(self, scene_pos):
        """Internal helper for hit-detection and removal of items."""
        hit_rect = QRectF(scene_pos.x() - 8, scene_pos.y() - 8, 16, 16)
        for item in self.scene.items(hit_rect):
            if item != self.lasso_path_item:
                # Track what we erased for the delta undo system
                if item not in self.current_erased_items:
                    self.current_erased_items.append(item)
                self.scene.removeItem(item)

    def mouseReleaseEvent(self, event):
        if self.is_panning: 
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            
        elif event.button() == Qt.LeftButton:
            
            if self.current_tool == Tool.PEN: 
                self.commit_stroke()
                
            elif self.current_tool in [Tool.LINE, Tool.CIRCLE, Tool.RECTANGLE]:
                if self.current_stroke_item:
                    # Finalize shape and save to history stack
                    self.push_command(AddItemCommand(self.scene, self.current_stroke_item))
                self.current_stroke_item = None
                self.current_stroke_pts = []
                
            elif self.current_tool == Tool.ERASER:
                # Commit everything we erased in this single swipe to the history
                if self.current_erased_items:
                    self.push_command(RemoveItemCommand(self.scene, self.current_erased_items))
                    self.current_erased_items = []
                    
            elif self.current_tool in [Tool.MOVE, Tool.RESIZE]:
                if hasattr(self, 'transform_start_states') and self.transform_start_states:
                    end_states = [{'item': s['item'], 'pos': s['item'].pos(), 'scale': s['item'].scale()} for s in self.transform_start_states]
                    # Only push an undo action if something actually moved/scaled
                    changed = any(s['pos'] != e['pos'] or s['scale'] != e['scale'] for s, e in zip(self.transform_start_states, end_states))
                    if changed:
                        self.push_command(TransformCommand(self.transform_start_states, end_states))
                    self.transform_start_states = []
                    
            elif self.current_tool == Tool.LASSO and self.lasso_path_item:
                path = QPainterPath()
                path.addPolygon(QPolygonF(self.lasso_points))
                self.scene.setSelectionArea(path)
                self.scene.removeItem(self.lasso_path_item)
                self.lasso_path_item = None
                
        event.accept()

    def commit_stroke(self):
        if not self.current_stroke_item or not self.current_stroke_pts: return
        pts = simplify_points(self.current_stroke_pts, SIMPLIFY_TOLERANCE)
        path = QPainterPath()
        path.moveTo(pts[0])
        for p in pts[1:]: path.lineTo(p)
        self.current_stroke_item.setPath(path)
        
        # Save the finalized stroke to the delta undo history stack
        self.push_command(AddItemCommand(self.scene, self.current_stroke_item))
        
        self.current_stroke_item = None
        self.current_stroke_pts = []

    def update_debug_text(self):
        if not self.show_debug: self.debug_label.hide(); return
        self.debug_label.show()
        stats = self.profiler.get_stats()
        self.debug_label.setText(f"Ping: {stats['current']:.1f}ms | Avg: {stats['avg_1s']:.1f}ms\nItems: {len(self.scene.items())}")
        self.debug_label.adjustSize()
