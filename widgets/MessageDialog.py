#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    MessageDialog.py
@Time  :    2023/04/25 14:00:48
@Author:    daidai_up
@Desc  :
'''
import wx
from wx.lib.buttons import GenButton


class CustomMessageDialog(wx.Dialog):
    '''消息对话框'''
    def __init__(self, parent, message):
        super().__init__(parent, style=wx.BORDER_SIMPLE)
        self.__OnInit(message)
        self.__CreateWidgets()
        self.__Bind()
        self.__Layout()

    def __OnInit(self, message):
        self.message = message
        self.InitSettings()
        self.SetSize(200, 100)
        self.CenterOnParent()
        self.SetBackgroundColour(self.settings['background_colour'])

    def InitSettings(self):
        self.settings = {
            'background_colour': wx.Colour('#212021'),
            'foreground_colour': wx.Colour('#FFFFFF'),
            'button_background_colour': wx.Colour('#212021'),
            'button_foreground_colour': wx.Colour('#FFFFFF'),
        }

    def __CreateWidgets(self):
        self.message = wx.StaticText(self, -1, self.message)
        self.message.SetFont(wx.Font(wx.FontInfo(20)))
        self.message.SetForegroundColour(self.settings['foreground_colour'])
        #
        self.btn = GenButton(self, wx.ID_OK, '确定')
        self.btn.SetFocus()
        self.btn.SetBackgroundColour(self.settings['button_background_colour'])
        self.btn.SetForegroundColour(self.settings['button_foreground_colour'])

    def __Bind(self):
        self.Bind(wx.EVT_CHAR_HOOK, self.OnChar)

    def __Layout(self):
        sizer = wx.GridSizer(1)
        sizer.Add(self.message, 0, wx.ALIGN_CENTER)
        sizer.Add(self.btn, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)

    def OnChar(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.btn.Notify()
        else:
            event.Skip()


class MessageDialog(CustomMessageDialog):
    def InitSettings(self):
        settings = wx.GetApp().settings['dialog']
        self.settings = {
            'background_colour': wx.Colour(settings['background_colour']),
            'foreground_colour': wx.Colour(settings['foreground_colour']),
            'button_background_colour': wx.Colour(settings['button_background_colour']),
            'button_foreground_colour': wx.Colour(settings['button_foreground_colour']),
        }


class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        button = wx.Button(self, -1, '消息对话框')
        button.Bind(wx.EVT_BUTTON, self.OnButton)

    def OnButton(self, event):
        dlg = CustomMessageDialog(self, '测试消息')
        dlg.ShowModal()
        dlg.Destroy()


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
