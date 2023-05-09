#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    FrameLess.py
@Time  :    2023/04/15 14:20:28
@Author:    daidai_up
@Desc  :
'''
import wx
from enum import Enum, unique


@unique
class ResizeMode(Enum):
    '''Resize模式'''
    OUTSIDE = 0
    TOPLEFT = 1
    TOP = 2
    TOPRIGHT = 3
    LEFT = 4
    RIGHT = 5
    BOTTOMLEFT = 6
    BOTTOM = 7
    BOTTOMRIGHT = 8
    CENTER = 9


# Resize模式对应的鼠标样式
RESIZEMODE_CURSOR = {
    ResizeMode.TOPLEFT: wx.CURSOR_SIZENWSE,
    ResizeMode.TOP: wx.CURSOR_SIZENS,
    ResizeMode.TOPRIGHT: wx.CURSOR_SIZENESW,
    ResizeMode.LEFT: wx.CURSOR_SIZEWE,
    ResizeMode.RIGHT: wx.CURSOR_SIZEWE,
    ResizeMode.BOTTOMLEFT: wx.CURSOR_SIZENESW,
    ResizeMode.BOTTOM: wx.CURSOR_SIZENS,
    ResizeMode.BOTTOMRIGHT: wx.CURSOR_SIZENWSE,
}


class ResizeMixin():
    '''为无边框框架增加resize功能的mixin类

    1. 启动定时器，定时检测鼠标位置
    2. 如果处于resize区域，修改鼠标样式
    3. 开始检测事件， 响应单击&移动等事件
    '''
    def __init__(self):
        self.__OnInit()
        self.__Bind()

    def __OnInit(self):
        self.frame = self.GetTopLevelParent()
        self._defaultCursor = self.frame.GetCursor()
        self._resizeTimer = wx.Timer(self)  # 定时检查鼠标状态
        self._resizeTimer.Start(500)
        self.resizeMode = ResizeMode.CENTER
        self._isResizeRectExpired = True  # resize区域是否失效
        self._resizeFilter = ResizeFilter(self.frame)

    def __Bind(self):
        self.Bind(wx.EVT_TIMER, self.OnTimer, self._resizeTimer)
        self.frame.Bind(wx.EVT_MOVE, self.InvalidateResizeRects)
        self.frame.Bind(wx.EVT_SIZE, self.InvalidateResizeRects)

    def OnTimer(self, event):
        '''定时检测鼠标位置'''
        # 保证框架处于屏幕内
        pos = self.frame.GetPosition()
        if pos.x < 0 or pos.y < 0:
            self.frame.Move(0 if pos.x < 0 else pos.x, 0 if pos.y < 0 else pos.y)
        # 最大化不检测
        if self.frame.IsMaximized():
            return
        # 点击状态不检测
        state = wx.GetMouseState()
        if state.LeftIsDown():
            return
        # 失效更新
        if self._isResizeRectExpired:
            self.UpdateResizeRects()
            self._isResizeRectExpired = False
        self._HitTest(wx.Point(state.GetX(), state.GetY()))

    def InvalidateResizeRects(self, event):
        '''移动或size事件时标记resize区域失效'''
        self._isResizeRectExpired = True
        event.Skip()

    def UpdateResizeRects(self, event=None):
        '''构建各个resize模式对应区域'''
        if event:
            event.Skip()
        _range = 5
        rect = self.frame.GetScreenRect()
        self._resizeRects = [
            (
                wx.Rect(
                    rect.topLeft.x + _range, rect.topLeft.y + _range,
                    rect.width - 2 * _range, rect.height - 2 * _range
                ),
                ResizeMode.CENTER
            ),
            (
                wx.Rect(rect.topLeft.x, rect.topLeft.y, _range, _range),
                ResizeMode.TOPLEFT
            ),
            (
                wx.Rect(rect.topLeft.x + _range, rect.topLeft.y, rect.width - 2 * _range, _range),
                ResizeMode.TOP
            ),
            (
                wx.Rect(rect.topRight.x - _range, rect.topRight.y, _range, _range),
                ResizeMode.TOPRIGHT
            ),
            (
                wx.Rect(rect.topLeft.x, rect.topLeft.y + _range, _range, rect.height - 2 * _range),
                ResizeMode.LEFT
            ),
            (
                wx.Rect(rect.topRight.x - _range, rect.topRight.y + _range, _range, rect.height - 2 * _range),
                ResizeMode.RIGHT
            ),
            (
                wx.Rect(rect.bottomLeft.x, rect.bottomLeft.y - _range, _range, _range),
                ResizeMode.BOTTOMLEFT
            ),
            (
                wx.Rect(rect.bottomLeft.x + _range, rect.bottomLeft.y - _range, rect.width - 2 * _range, _range),
                ResizeMode.BOTTOM
            ),
            (
                wx.Rect(rect.bottomRight.x - _range, rect.bottomRight.y - _range, _range, _range),
                ResizeMode.BOTTOMRIGHT
            ),
        ]

    ############################################################################
    def _HitTest(self, point):
        '''测试鼠标位置'''
        for rect, mode in self._resizeRects:
            if rect.Contains(point):
                if mode != self.resizeMode:   # 模式变更，设置光标
                    self.frame.SetCursor(wx.Cursor(RESIZEMODE_CURSOR.get(mode, self._defaultCursor)))
                    self.resizeMode = mode
                return
        if self.resizeMode != ResizeMode.OUTSIDE:  # 恢复默认光标
            self.frame.SetCursor(wx.Cursor(self._defaultCursor))
        self.resizeMode = ResizeMode.OUTSIDE


class ResizeFilter(wx.EventFilter):
    '''resize模式下接管事件处理'''
    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        self.__OnInit()

    def __OnInit(self):
        wx.EvtHandler.AddFilter(self)
        self.resizing = False
        self.minSize = None
        self.evtFunc = {    # 需要劫持的事件及对应handler
            wx.wxEVT_LEFT_DOWN: self.OnLeftDown,
            wx.wxEVT_LEFT_UP: self.OnLeftUp,
            wx.wxEVT_MOTION: self.OnMotion,
            wx.wxEVT_MOUSE_CAPTURE_LOST: self.OnCaptureLost,
        }
        self.modeFunc = {   # resize不同模式对应的handler
            ResizeMode.TOPLEFT: self._ResizeTopLeft,
            ResizeMode.TOP: self._ResizeTop,
            ResizeMode.TOPRIGHT: self._ResizeTopRight,
            ResizeMode.LEFT: self._ResizeLeft,
            ResizeMode.RIGHT: self._ResizeRight,
            ResizeMode.BOTTOMLEFT: self._ResizeBottomLeft,
            ResizeMode.BOTTOM: self._ResizeBottom,
            ResizeMode.BOTTOMRIGHT: self._ResizeBottomRight,
        }

    def __del__(self):
        '''清理'''
        wx.EvtHandler.RemoveFilter(self)

    def FilterEvent(self, event):
        '''事件过滤'''
        # 非resize状态
        if self.frame.resizeMode in (ResizeMode.OUTSIDE, ResizeMode.CENTER):
            return self.Event_Skip
        # 非resize事件
        if event.GetEventType() not in self.evtFunc.keys():
            return self.Event_Skip
        return self.evtFunc[event.GetEventType()](event)

    def OnLeftDown(self, event):
        '''开始Resize'''
        self._rect = self.frame.GetRect()
        self.minSize = self.frame.GetMinSize()
        if not self.frame.HasCapture():
            self.frame.CaptureMouse()
        self.resizing = True
        return self.Event_Processed

    def OnLeftUp(self, event=None):
        '''结束Resize'''
        if self.frame.HasCapture():
            self.frame.ReleaseMouse()
        self.resizing = False
        return self.Event_Processed

    def OnMotion(self, event):
        '''Resizing'''
        if self.resizing and event.LeftIsDown() and event.Dragging():
            self._Resize(self.frame.resizeMode, self._rect, wx.GetMousePosition())
            return self.Event_Processed
        return self.Event_Skip

    def OnCaptureLost(self, event):
        '''丢失Capture'''
        if event.GetEventObject() != self.frame:
            return self.Event_Skip
        return self.OnLeftUp()

    def _Resize(self, mode, rect, pos):
        '''调整Size'''
        self.frame.SetRect(self.modeFunc[mode](rect, pos))

    def _ResizeTopLeft(self, rect, pos):
        '''TopLeft'''
        bottomRight = rect.BottomRight   # 不动点
        topLeft = wx.Point(
            bottomRight.x - max(bottomRight.x - pos.x, self.minSize.width),
            bottomRight.y - max(bottomRight.y - pos.y, self.minSize.height),
        )
        return wx.Rect(topLeft, bottomRight)

    def _ResizeTop(self, rect, pos):
        '''Top'''
        bottomRight = self._rect.BottomRight   # 不动点
        topLeft = wx.Point(
            rect.TopLeft.x,
            min(pos.y, bottomRight.y - self.minSize.height)
        )
        return wx.Rect(topLeft, bottomRight)

    def _ResizeTopRight(self, rect, pos):
        '''TopRight'''
        bottomLeft = rect.bottomLeft  # 不动点
        topLeft = wx.Point(bottomLeft.x, min(pos.y, bottomLeft.y - self.minSize.height))
        bottomRight = wx.Point(max(pos.x, bottomLeft.x + self.minSize.width), bottomLeft.y)
        return wx.Rect(topLeft, bottomRight)

    def _ResizeLeft(self, rect, pos):
        '''Left'''
        bottomRight = rect.BottomRight    # 不动点
        topLeft = wx.Point(
            min(pos.x, bottomRight.x - self.minSize.width),
            rect.TopLeft.y
        )
        return wx.Rect(topLeft, bottomRight)

    def _ResizeRight(self, rect, pos):
        '''Right'''
        topLeft = rect.TopLeft   # 不动点
        bottomRight = wx.Point(
            max(topLeft.x + self.minSize.width, pos.x), rect.BottomRight.y
        )
        return wx.Rect(topLeft, bottomRight)

    def _ResizeBottomLeft(self, rect, pos):
        '''BottomLeft'''
        topRight = rect.TopRight  # 不动点
        topLeft = wx.Point(min(pos.x, topRight.x - self.minSize.width), topRight.y)
        bottomRight = wx.Point(topRight.x, max(pos.y, topRight.y + self.minSize.height))
        return wx.Rect(topLeft, bottomRight)

    def _ResizeBottom(self, rect, pos):
        '''Bottom'''
        topLeft = rect.TopLeft  # 不动点
        bottomRight = wx.Point(rect.BottomRight.x, max(pos.y, topLeft.y + self.minSize.height))
        return wx.Rect(topLeft, bottomRight)

    def _ResizeBottomRight(self, rect, pos):
        '''BottomRight'''
        topLeft = rect.TopLeft   # 不动点
        bottomRight = wx.Point(
            max(pos.x, topLeft.x + self.minSize.width),
            max(pos.y, topLeft.y + self.minSize.height)
        )
        return wx.Rect(topLeft, bottomRight)


class FrameLessFrame(wx.Frame, ResizeMixin):
    '''无边框框架'''
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, style=wx.BORDER_NONE)
        ResizeMixin.__init__(self)
        self.__OnInit()

    def __OnInit(self):
        self._isMaximized = False   # 是否最大化
        self._oldRect = None  # 原始Rect
        self.SetMinSize((400, 300))

    ############################################################################
    def Maximize(self, maximize=True):
        '''无标题栏框架最大化会覆盖任务栏， 需要自定义实现'''
        if maximize:
            if not self.IsMaximized():
                self._oldRect = self.GetScreenRect()
            self.SetRect(wx.GetClientDisplayRect())
            self._isMaximized = True
        else:
            if self._oldRect:
                self.SetRect(self._oldRect)
            self._isMaximized = False

    def IsMaximized(self):
        return self._isMaximized


class Panel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour('#212021')

        minimizeButton = wx.Button(self, -1, '最小化')
        maximizeButton = wx.Button(self, -1, '最大化')
        normalButton = wx.Button(self, -1, '正常化')
        closeButton = wx.Button(self, -1, '关闭')

        minimizeButton.Bind(wx.EVT_BUTTON, self.OnMinimize)
        maximizeButton.Bind(wx.EVT_BUTTON, self.OnMaximize)
        normalButton.Bind(wx.EVT_BUTTON, self.OnNormal)
        closeButton.Bind(wx.EVT_BUTTON, self.OnClose)

        sizer = wx.GridSizer(2)
        sizer.Add(minimizeButton, 0, wx.ALIGN_CENTER)
        sizer.Add(maximizeButton, 0, wx.ALIGN_CENTER)
        sizer.Add(normalButton, 0, wx.ALIGN_CENTER)
        sizer.Add(closeButton, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)

    def OnMinimize(self, event):
        self.GetTopLevelParent().Iconize()

    def OnMaximize(self, event):
        self.GetTopLevelParent().Maximize(True)

    def OnNormal(self, event):
        self.GetTopLevelParent().Maximize(False)

    def OnClose(self, event):
        self.GetTopLevelParent().Close()


class Frame(FrameLessFrame):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.SetTitle(title)
        panel = Panel(self)
        sizer = wx.BoxSizer()
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()  # 必须的


class App(wx.App):
    def OnInit(self):
        frame = Frame(None, '无边框框架')
        frame.Center()
        frame.Show()
        return super().OnInit()


def main():
    app = App()
    app.MainLoop()


if __name__ == '__main__':
    main()
