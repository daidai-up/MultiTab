#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    Notebook.py
@Time  :    2023/04/24 11:11:56
@Author:    daidai_up
@Desc  :
'''
import wx
import wx.lib.agw.flatnotebook as fn


class CustomNotebook(fn.FlatNotebook):
    def __init__(self, parent):
        agwStyle = (
            fn.FNB_FANCY_TABS | fn.FNB_NO_X_BUTTON | fn.FNB_X_ON_TAB |
            fn.FNB_NO_TAB_FOCUS | fn.FNB_NAV_BUTTONS_WHEN_NEEDED
        )
        super().__init__(parent, -1, style=wx.BORDER_NONE, agwStyle=agwStyle)
        self.__OnInit()

    def __OnInit(self):
        '''初始化'''
        self.InitSettings()
        self.SetBackgroundColour(self.settings['background_colour'])
        self.SetTabAreaColour(self.settings['background_colour'])
        self.SetGradientColours(
            self.settings['background_colour'],
            self.settings['background_colour'],
            self.settings['border_colour']
        )
        self.SetActiveTabTextColour(self.settings['active_tab_foreground_colour'])
        self.SetNonActiveTabTextColour(self.settings['inactive_tab_foreground_colour'])

    def InitSettings(self):
        self.settings = {
            'background_colour': wx.Colour('#212021'),
            'border_colour': wx.Colour('#FFFFFF'),
            'active_tab_foreground_colour': wx.Colour('#FFFFFF'),
            'inactive_tab_foreground_colour': wx.Colour('#808080'),
            'page_background_colour': wx.Colour('#212021'),
        }


class Notebook(CustomNotebook):
    def InitSettings(self):
        settings = wx.GetApp().settings['notebook']
        self.settings = {
            'background_colour': wx.Colour(settings['background_colour']),
            'border_colour': wx.Colour(settings['border_colour']),
            'active_tab_foreground_colour': wx.Colour(settings['active_tab_foreground_colour']),
            'inactive_tab_foreground_colour': wx.Colour(settings['inactive_tab_foreground_colour']),
            'page_background_colour': wx.Colour(settings['page_background_colour']),
        }


class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetTitle('Notebook')
        self.SetSize(600, 400)

        imgList = wx.ImageList(16, 16)
        imgList.Add(wx.Bitmap(wx.Image('assets/images/putty.png').Scale(16, 16)))
        notebook = CustomNotebook(self)
        notebook.AssignImageList(imgList)

        for idx in range(20):
            page = wx.Panel(notebook)
            page.SetBackgroundColour('#212021')
            notebook.AddPage(page, f'第{idx}页', imageId=0)


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
