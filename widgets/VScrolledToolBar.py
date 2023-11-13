#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    VScrolledToolBar.py
@Time  :    2023/04/18 11:19:22
@Author:    daidai_up
@Desc  :
'''
import wx


class ToolBase(wx.Control):
    '''工具项'''
    def __init__(self, parent, id, label, bitmap, fgColour, bgColour, enterColour, width, height, clientData=None):
        super().__init__(parent, id, style=wx.BORDER_NONE)
        self.__OnInit(label, bitmap, fgColour, bgColour, enterColour, width, height, clientData)
        self.__Bind()

    def __OnInit(self, label, bitmap, fgColour, bgColour, enterColour, width, height, clientData):
        '''初始化'''
        self.width = width
        self.height = height
        self.clientData = clientData
        self.SetSize((width, height))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.InitBuffer(label, bitmap, fgColour, bgColour, enterColour)

    def __Bind(self):
        '''事件绑定'''
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    ############################################################################
    def InitBuffer(self, label, bitmap, fgColour, bgColour, enterColour):
        '''绘图'''
        self._normalBuffer = self._InitBuffer(label, bitmap, fgColour, bgColour)
        self._enterBuffer = self._InitBuffer(label, bitmap, fgColour, enterColour)
        self._buffer = self._normalBuffer

    def _InitBuffer(self, label, bitmap, fgColour, bgColour):
        _buffer = wx.Bitmap(self.width, self.height)
        dc = wx.MemoryDC(_buffer)
        dc.SetBackground(wx.Brush(bgColour))
        dc.Clear()
        dc.SetTextForeground(fgColour)
        bitmapPos, textPos = self._CalcPositon(label, bitmap)
        dc.DrawBitmap(bitmap, bitmapPos)
        dc.DrawText(label, textPos)
        return _buffer

    def _CalcPositon(self, label, bitmap):
        '''计算图片和文本的起始位置'''
        bitmapWidth, bitmapHeight = bitmap.GetSize()
        dc = wx.MemoryDC(wx.Bitmap(20, 20))
        textWidth, textHeight = dc.GetTextExtent(label)
        padding = (self.height - bitmapHeight - textHeight) / 2
        bitmapPos = (int((self.width - bitmapWidth) / 2), int(padding))
        textPos = (int((self.width - textWidth) / 2), int(self.height - textHeight - padding))
        return bitmapPos, textPos

    ############################################################################
    def OnPaint(self, event):
        _ = wx.BufferedPaintDC(self, self._buffer)

    def OnEnterWindow(self, event):
        self._buffer = self._enterBuffer
        self.Refresh()
        event.Skip()

    def OnLeaveWindow(self, event):
        self._buffer = self._normalBuffer
        self.Refresh()
        event.Skip()

    def OnLeftUp(self, event):
        '''点击时构造ToolEvent'''
        event = wx.MenuEvent(wx.wxEVT_TOOL, id=event.GetId())
        wx.QueueEvent(self.GetTopLevelParent(), event)

    def GetClientData(self):
        return self.clientData


class CustomVScrolledToolBar(wx.ScrolledWindow):
    '''自定义纵向滚动工具栏'''
    def __init__(self, parent):
        super().__init__(parent, style=wx.VSCROLL)
        self.__OnInit()
        self.__Bind()

    def __OnInit(self):
        self.InitSettings()
        self._tools = []
        self.SetScrollRate(0, 1)
        self.DisableKeyboardScrolling()
        self.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)   # 不显示滚动条
        self.SetBackgroundColour(self.settings['background_colour'])

    def InitSettings(self):
        self.settings = {
            'foreground_colour': wx.Colour('#FFFFFF'),
            'background_colour': wx.Colour('#212021'),
            'enter_colour': wx.Colour('#414141'),
            'padding': 8,
        }

    def __Bind(self):
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)

    ############################################################################
    def AddTool(self, label, bitmap, clientData=None):
        '''增加工具项'''
        toolId = wx.NewIdRef()
        self._tools.append((toolId, label, bitmap, clientData))
        return toolId

    def Realize(self):
        '''布局'''
        self.Scroll(0, 0)  # 必须的
        self.toolSize = self._GetToolSize()
        self.SetMinClientSize(self.toolSize)
        height = 0
        for toolId, label, bitmap, clientData in self._tools:
            tool = ToolBase(
                self, toolId, label, bitmap, self.settings['foreground_colour'],
                self.settings['background_colour'], self.settings['enter_colour'],
                *self.toolSize, clientData
            )
            tool.SetPosition((0, height))
            height += self.toolSize.height
        self.SetVirtualSize(-1, height)
        sizer = self.GetContainingSizer()
        if sizer is not None:
            sizer.Layout()

    def ClearTools(self):
        '''清空工具栏'''
        for child in self.GetChildren():
            child.Destroy()
        self._tools.clear()

    def OnWheel(self, event):
        '''滚轮控制滚动'''
        _, y = self.GetViewStart()
        _, ty = self.toolSize
        _, my = self.GetVirtualSize()
        if event.GetWheelRotation() > 0:
            next_y = max(0, y - ty)
        else:
            next_y = min(y + ty, my)
        self.Scroll(-1, next_y)

    ############################################################################
    def _GetToolSize(self):
        '''统一工具项Size'''
        if not self._tools:    # 默认Size
            return (60, 60)
        widths = []
        heights = []
        _dc = wx.MemoryDC(wx.Bitmap(20, 20))
        for _, label, bitmap, _ in self._tools:
            width, height = self._CalcToolSize(label, bitmap, _dc)
            widths.append(width)
            heights.append(height)
        return wx.Size(max(widths), max(heights))

    def _CalcToolSize(self, label, bitmap, dc):
        '''单个工具项Size'''
        bitmapWidth, bitmapHeight = bitmap.GetSize()
        textWidth, textHeight = dc.GetTextExtent(label)
        return (
            max(bitmapWidth, textWidth) + self.settings['padding'] * 2,
            bitmapHeight + textHeight + self.settings['padding'] * 2,
        )


class VScrolledToolBar(CustomVScrolledToolBar):
    '''纵向滚动工具栏'''
    def InitSettings(self):
        settings = wx.GetApp().settings['toolbar']
        self.settings = {
            'foreground_colour': wx.Colour(settings['foreground_colour']),
            'background_colour': wx.Colour(settings['background_colour']),
            'enter_colour': wx.Colour(settings['enter_colour']),
            'padding': settings['padding'],
        }


class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetTitle('纵向滚动标题栏')
        self.SetSize(600, 400)
        bitmap = wx.Bitmap('assets/images/putty.png')

        toolBar = CustomVScrolledToolBar(self)
        for idx in range(20):
            toolBar.AddTool(f'SSH-00{idx}', bitmap, clientData={'index': idx})
        toolBar.Realize()
        toolBar.Bind(wx.EVT_TOOL, self.OnTool)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(toolBar, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def OnTool(self, event):
        toolBar = wx.FindWindowById(event.GetId())
        print(toolBar.GetClientData())


class App(wx.App):
    def OnInit(self):
        frame = Frame(None)
        frame.Center()
        frame.Show()
        return super().OnInit()


def main():
    app = App()
    app.MainLoop()


if __name__ == '__main__':
    main()
