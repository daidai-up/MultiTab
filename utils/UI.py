#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    UI.py
@Time  :    2023/11/13 10:37:03
@Author:    daidai_up
@Desc  :
'''
import wx
from pynput import keyboard
from threading import Thread


def GetBorders():
    '''获取普通窗口边框宽度'''
    frame = wx.Frame(None)
    frame.Hide()
    w, h = frame.GetSize()
    cw, ch = frame.GetClientSize()
    left = right = bottom = (w - cw) // 2
    top = h - ch - bottom
    frame.Close()
    return {'top': top, 'bottom': bottom, 'left': left, 'right': right}


class ListenKeyThread(Thread):
    '''监控热键线程'''
    def __init__(self):
        super().__init__(daemon=True)
        self.__hotkeys = {}

    def AddHotKey(self, hotKey, callback):
        '''热键=>回调'''
        self.__hotkeys[hotKey] = callback

    def Start(self):
        '''Rename'''
        self.start()

    def run(self):
        with keyboard.GlobalHotKeys(self.__hotkeys, daemon=True) as ghk:
            ghk.join()
