#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    TitleBar.py
@Time  :    2023/04/15 17:22:15
@Author:    daidai_up
@Desc  :
'''
import wx


class TitlebarBox(wx.Window):
    '''Box基类'''
    def __init__(self, parent, colour, bitmap, enterColour, enterBitmap, width, height):
        super().__init__(parent, style=wx.BORDER_NONE)
        self.__OnInit(colour, bitmap, enterColour, enterBitmap, width, height)
        self.__Bind()

    def __OnInit(self, colour, bitmap, enterColour, enterBitmap, width, height):
        self.width = width
        self.height = height
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.InitBuffer(colour, bitmap, enterColour, enterBitmap)

    def __Bind(self):
        '''事件绑定'''
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    ############################################################################
    def InitBuffer(self, colour, bitmap, enterColour, enterBitmap):
        '''绘图'''
        self._normalBuffer = self._InitBuffer(colour, bitmap)
        self._enterBuffer = self._InitBuffer(enterColour, enterBitmap)
        self._buffer = self._normalBuffer

    def _InitBuffer(self, colour, bitmap):
        iw, ih = bitmap.GetSize()
        pos = ((self.width - iw) / 2, (self.height - ih) / 2)
        _buffer = wx.Bitmap(self.width, self.height)
        dc = wx.MemoryDC(_buffer)
        dc.SetBackground(wx.Brush(colour))
        dc.Clear()
        if pos[0] >= 0 and pos[1] >= 0 and bitmap:
            dc.DrawBitmap(bitmap, pos)
        return _buffer

    ############################################################################
    def OnPaint(self, event):
        '''Paint事件'''
        _ = wx.BufferedPaintDC(self, self._buffer)

    def OnEnter(self, event):
        '''进入事件'''
        self._buffer = self._enterBuffer
        self.Refresh()
        event.Skip()

    def OnLeave(self, event):
        '''离开事件'''
        self._buffer = self._normalBuffer
        self.Refresh()
        event.Skip()

    def DoGetBestClientSize(self):
        '''默认Size'''
        return wx.Size(self.width, self.height)


class CustomTitleBar(wx.Panel):
    '''自定义标题栏'''
    def __init__(self, parent, isMaximized=False):
        super().__init__(parent, style=wx.BORDER_NONE)
        self.__OnInit(isMaximized)
        self.__CreateWidgets()
        self.__Layout()
        self.__Bind()

    def __OnInit(self, isMaximized):
        '''初始化'''
        self.InitSettings()
        self._startPos = None
        self.isMaximized = isMaximized  # 初始是否最大化状态
        self.frame = self.GetTopLevelParent()
        self.SetBackgroundColour(self.settings['background_colour'])

    def __CreateWidgets(self):
        '''构建组件'''
        self.CreateIconBox()
        self.CreateTitleBox()
        self.CreateMinimizeBox()
        self.CreateMaximizeBox()
        self.CreateNormalizeBox()
        self.CreateCloseBox()

    def __Layout(self):
        '''布局'''
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.iconBox, 0, wx.ALIGN_CENTER | wx.RIGHT, 5)
        sizer.Add(self.titleBox, 0, wx.ALIGN_CENTER)
        sizer.AddStretchSpacer()
        sizer.Add(self.minimizeBox)
        sizer.Add(self.maximizeBox)
        sizer.Add(self.normalizeBox)
        sizer.Add(self.closeBox)
        self.SetSizer(sizer)
        self.Layout()

    def __Bind(self):
        # 最小化/最大化/关闭
        self.minimizeBox.Bind(wx.EVT_LEFT_UP, self.OnMinimize)
        self.maximizeBox.Bind(wx.EVT_LEFT_UP, self.OnMaximize)
        self.normalizeBox.Bind(wx.EVT_LEFT_UP, self.OnMaximize)
        self.closeBox.Bind(wx.EVT_LEFT_UP, self.OnClose)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnMaximize)  # 双击最大化
        # 移动
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnCaptureLost)

    ############################################################################
    def InitSettings(self):
        self.settings = {
            'background_colour': wx.Colour('#212021'),
            'foreground_colour': wx.Colour('#FFFFFF'),
            'icon': wx.Bitmap(wx.Image('assets/images/favicon.ico').Scale(22, 22)),
            'title': 'Title Bar',

            'box_width': 32,
            'box_height': 32,

            'minimize_box': {
                'colour': wx.Colour('#212021'),
                'image': wx.Bitmap('assets/images/minimize.png'),
                'enter_colour': wx.Colour('#414141'),
                'enter_image': wx.Bitmap('assets/images/minimize.png')
            },
            'maximize_box': {
                'colour': wx.Colour('#212021'),
                'image': wx.Bitmap('assets/images/maximize.png'),
                'enter_colour': wx.Colour('#414141'),
                'enter_image': wx.Bitmap('assets/images/maximize.png')
            },
            'normalize_box': {
                'colour': wx.Colour('#212021'),
                'image': wx.Bitmap('assets/images/normalize.png'),
                'enter_colour': wx.Colour('#414141'),
                'enter_image': wx.Bitmap('assets/images/normalize.png')
            },
            'close_box': {
                'colour': wx.Colour('#212021'),
                'image': wx.Bitmap('assets/images/close.png'),
                'enter_colour': wx.Colour('#E81123'),
                'enter_image': wx.Bitmap('assets/images/close.png')
            },
        }

    ############################################################################
    def CreateIconBox(self):
        '''Icon'''
        self.iconBox = TitlebarBox(
            self, self.settings['background_colour'], self.settings['icon'],
            self.settings['background_colour'], self.settings['icon'],
            self.settings['box_width'], self.settings['box_height']
        )

    def CreateTitleBox(self):
        '''标题'''
        self.titleBox = wx.StaticText(self, -1, label=self.settings['title'])
        self.titleBox.SetForegroundColour(self.settings['foreground_colour'])

    def CreateMinimizeBox(self):
        '''最小化框'''
        settings = self.settings['minimize_box']
        self.minimizeBox = TitlebarBox(
            self, settings['colour'], settings['image'],
            settings['enter_colour'], settings['enter_image'],
            self.settings['box_width'], self.settings['box_height']
        )

    def CreateMaximizeBox(self):
        '''最小化框'''
        settings = self.settings['maximize_box']
        self.maximizeBox = TitlebarBox(
            self, settings['colour'], settings['image'],
            settings['enter_colour'], settings['enter_image'],
            self.settings['box_width'], self.settings['box_height']
        )
        self.maximizeBox.Show(not self.isMaximized)

    def CreateNormalizeBox(self):
        '''正常化框'''
        settings = self.settings['normalize_box']
        self.normalizeBox = TitlebarBox(
            self, settings['colour'], settings['image'],
            settings['enter_colour'], settings['enter_image'],
            self.settings['box_width'], self.settings['box_height']
        )
        self.normalizeBox.Show(self.isMaximized)

    def CreateCloseBox(self):
        '''关闭框'''
        settings = self.settings['close_box']
        self.closeBox = TitlebarBox(
            self, settings['colour'], settings['image'],
            settings['enter_colour'], settings['enter_image'],
            self.settings['box_width'], self.settings['box_height']
        )

    ############################################################################
    def OnMinimize(self, event):
        '''最小化'''
        self.frame.Iconize()

    def OnMaximize(self, event=None):
        '''最大化'''
        self.frame.Maximize(not self.frame.IsMaximized())
        self.maximizeBox.Show(not self.frame.IsMaximized())
        self.normalizeBox.Show(self.frame.IsMaximized())
        self.Layout()

    def OnClose(self, event):
        '''关闭'''
        self.frame.Close()

    def OnLeftDown(self, event):
        '''开始移动'''
        if self.frame.IsMaximized():   # 最大化禁止拖动
            return
        self._startPos = event.GetPosition()
        if not self.HasCapture():
            self.CaptureMouse()

    def OnMotion(self, event):
        '''移动中'''
        if self._startPos and event.LeftIsDown() and event.Dragging():
            self.frame.Move(wx.GetMousePosition() - self._startPos)

    def OnLeftUp(self, event=None):
        '''结束移动'''
        if self.HasCapture():
            self.ReleaseMouse()
        self._startPos = None

    def OnCaptureLost(self, event):
        '''释放'''
        self.OnLeftUp()


class TitleBar(CustomTitleBar):
    '''标题栏'''
    def __init__(self, parent):
        super().__init__(parent, isMaximized=True)

    def InitSettings(self):
        settings = wx.GetApp().settings
        tsetings = settings['titlebar']
        self.settings = {
            'background_colour': wx.Colour(tsetings['background_colour']),
            'foreground_colour': wx.Colour(tsetings['foreground_colour']),

            'icon': wx.Bitmap(wx.Image(settings['app']['icon']).Scale(22, 22)),
            'title': settings['app']['title'],

            'box_width': tsetings['box_width'],
            'box_height': tsetings['box_height'],

            'minimize_box': {
                'colour': wx.Colour(tsetings['minimize_box']['colour']),
                'image': wx.Bitmap(tsetings['minimize_box']['image']),
                'enter_colour': wx.Colour(tsetings['minimize_box']['enter_colour']),
                'enter_image': wx.Bitmap(tsetings['minimize_box']['enter_image'])
            },
            'maximize_box': {
                'colour': wx.Colour(tsetings['maximize_box']['colour']),
                'image': wx.Bitmap(tsetings['maximize_box']['image']),
                'enter_colour': wx.Colour(tsetings['maximize_box']['enter_colour']),
                'enter_image': wx.Bitmap(tsetings['maximize_box']['enter_image'])
            },
            'normalize_box': {
                'colour': wx.Colour(tsetings['normalize_box']['colour']),
                'image': wx.Bitmap(tsetings['normalize_box']['image']),
                'enter_colour': wx.Colour(tsetings['normalize_box']['enter_colour']),
                'enter_image': wx.Bitmap(tsetings['normalize_box']['enter_image'])
            },
            'close_box': {
                'colour': wx.Colour(tsetings['close_box']['colour']),
                'image': wx.Bitmap(tsetings['close_box']['image']),
                'enter_colour': wx.Colour(tsetings['close_box']['enter_colour']),
                'enter_image': wx.Bitmap(tsetings['close_box']['enter_image'])
            },
        }


class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetTitle('标题栏')
        self.SetSize(600, 400)
        titleBar = CustomTitleBar(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(titleBar, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()


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
