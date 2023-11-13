#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    MultiTab.py
@Time  :    2023/04/15 14:14:13
@Author:    daidai_up
@Desc  :    为Putty Cygwin提供多标签支持

# 实现方法：
* CreateProcess(...)创建子程序窗口。 lpStartupInfo特定参数隐藏窗口
* SetParent(...)设置父窗口
* SetWindowPos(...)显示窗口， 同时设置子窗口位置及大小
* MoveWindow(...)调整子窗口位置及大小


# 问题：
1.  窗口样式问题。

    利用SetWindowLong(...)设置GWL_STYLE及GWL_EXSTYLE可以删除标题栏等修饰，但是有些exe运
    行过程中也会修改STYLE，导致设置失效。

    解决办法: 不设置窗口样式，而是调整窗口位置，增大窗口Size，使得其工作区Size刚好等于Page的
    Size, 而标题栏和窗口边框等修饰被覆盖隐藏。

    边框宽度(borders)设置: 标准窗口使用默认值即可，非标准窗口需要自己调整


2.  焦点切换问题。

    exe窗口不是 *完全* 的子窗口， 无法使用SetFocus(...)切换焦点？

    解决办法: 设置前台窗口(SetForegroundWindow(...))让exe子窗口自己切换焦点。


# 打包：
    ```
        python -m nuitka --follow-imports --standalone --onefile --show-progress
        --disable-console --windows-icon-from-ico=assets/images/favicon.ico MultiTab.py
    ```
'''
import os
import wx
import sys
import json
import yaml
import logging
import win32api
import win32con
import win32gui

from utils.UI import GetBorders, ListenKeyThread
from utils.StartExe import StartExeThread, KillPids

from widgets.Notebook import Notebook
from widgets.MessageDialog import MessageDialog
from widgets.VScrolledToolBar import VScrolledToolBar
from wx.lib.agw.flatnotebook import EVT_FLATNOTEBOOK_PAGE_CLOSING

################################################################################
# 初始化
################################################################################
BASE_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
ASSETS_PATH = os.path.join(BASE_PATH, 'assets')
THEME_FILE = os.path.join(ASSETS_PATH, 'theme.json')
CORE_FILE = os.path.join(ASSETS_PATH, 'core.json')
CONFIG_TEMPLATE_FILE = os.path.join(ASSETS_PATH, 'config.yaml.template')
CONFIG_FILE_NAME = 'config.yaml'
CONFIG_FILE = os.path.join(BASE_PATH, CONFIG_FILE_NAME)
# 日志
LOG_PATH = os.path.join(BASE_PATH, 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOG_FILE = os.path.join(LOG_PATH, 'run.log')
file_handler = logging.FileHandler(filename=LOG_FILE, mode='a', encoding='UTF-8')
logging.basicConfig(
    handlers=(file_handler, ), level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
    format='[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s]:  %(message)s',
)
logger = logging.getLogger(__name__)


################################################################################
# 配置文件
################################################################################
def GetConfigurations():
    '''初始化配置'''
    configurations = {}
    with open(CONFIG_FILE, encoding='UTF-8') as fh:
        try:
            configurations = yaml.safe_load(fh)
        except Exception:
            logger.error('配置异常', exc_info=True)
    if configurations:
        FillConfigurationDefaults(configurations)
    else:
        configurations = {}
    return configurations


def FillConfigurationDefaults(configurations):
    '''填充默认值'''
    # 默认项
    for item in configurations['items']:
        if item['name'] == 'default':
            defaultItem = item
            break
    # 删除无效项
    for item in configurations['items'][::-1]:
        if not (item['image'] and item['cmd'] and item['type']):
            configurations['items'].remove(item)
    # 填充默认值
    for n, item in enumerate(configurations['items']):
        item['index'] = n
        item['name'] = str(item['name'])
        for key, value in defaultItem.items():
            if key not in item:
                item[key] = value


################################################################################
# 主界面
################################################################################
class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.__OnInit()
        self.__CreateWidgets()
        self.__Layout()
        self.__Bind()
        self.Maximize()
        self.Layout()

    def __OnInit(self):
        '''初始化'''
        self.InitSettings()
        self.InitConfigurations()
        self.InitCoreMappings()
        self.SetTitle(self.settings['title'])
        self.SetIcon(wx.Icon(self.settings['icon']))
        self.SetBackgroundColour(self.settings['background_colour'])
        # 内部保存信息
        self.pidExe = {}   # page ID => exe信息
        self.hwnds = set([self.GetHandle()])  # 所有窗口句柄
        # 焦点切换
        self._focusTimer = wx.Timer()
        self._focusTimer.SetOwner(self)
        self._focusTimer.Start(200)
        # 配置更新
        self.configWatcher = wx.FileSystemWatcher()
        self.configWatcher.AddTree(BASE_PATH, wx.FSW_EVENT_MODIFY, CONFIG_FILE_NAME)
        self.configWatcher.SetOwner(self)

    def InitSettings(self):
        '''界面相关设置'''
        settings = wx.GetApp().settings
        self.settings = {
            'title': settings['app']['title'],
            'icon': settings['app']['icon'],
            'background_colour': settings['app']['background_colour'],
            'border_colour': settings['app']['border_colour'],
        }

    def InitConfigurations(self):
        '''工具栏相关配置'''
        # 初次启动, 从模板生成配置文件
        if not os.path.exists(CONFIG_FILE):   # 初次启动
            with open(CONFIG_TEMPLATE_FILE, encoding='UTF-8') as fh:
                configTemplate = fh.read().format(**GetBorders())
            with open(CONFIG_FILE, mode='w', encoding='UTF-8') as fh:
                fh.write(configTemplate)
        self.configurations = GetConfigurations()

    def InitCoreMappings(self):
        '''核心映射关系'''
        with open(CORE_FILE, encoding='UTF-8') as fh:
            self.coreMappings = json.loads(fh.read())

    def __CreateWidgets(self):
        '''构造主框架'''
        self.contentPanel = wx.Panel(self, style=wx.BORDER_NONE)
        self.contentPanel.SetBackgroundColour(self.settings['border_colour'])
        self.toolBar = self.__CreateToolBar(self.contentPanel)
        self.UpdateToolBar()
        self.notebook = self.__CreateNotebook(self.contentPanel)

    def __CreateToolBar(self, parent):
        '''构造工具栏'''
        toolBar = VScrolledToolBar(parent)
        return toolBar

    def UpdateToolBar(self):
        '''更新工具项'''
        self.toolBar.ClearTools()
        for item in self.configurations.get('items', []):
            if item['type'] not in self.coreMappings:  # 缺失核心映射
                continue
            self.toolBar.AddTool(item['name'], wx.Bitmap(item['image']), clientData=item)
        self.toolBar.Realize()

    def __CreateNotebook(self, parent):
        '''构造book'''
        imgList = wx.ImageList(16, 16)
        for item in self.configurations['items']:
            imgList.Add(wx.Bitmap(wx.Image(item['image']).Scale(16, 16)))
        notebook = Notebook(parent)
        notebook.AssignImageList(imgList)
        return notebook

    def __Layout(self):
        '''布局'''
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        csizer.AddSpacer(1)
        csizer.Add(self.toolBar, 0, wx.EXPAND | wx.ALL, 1)
        csizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL & (~wx.LEFT), 1)
        self.contentPanel.SetSizer(csizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.contentPanel, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def __Bind(self):
        '''事件绑定'''
        # 启动exe
        self.Bind(wx.EVT_TOOL, self.OnTool)
        # 关闭
        self.Bind(EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # 焦点切换
        self.Bind(wx.EVT_TIMER, self.OnFocus, self._focusTimer)
        # 配置更新
        self.Bind(wx.EVT_FSWATCHER, self.OnUpdateConfig)
        # 热键监控 (默认激活窗口为exe子窗口, 无法使用普通方法创建热键，需要全局的按键监听)
        listen = ListenKeyThread()
        listen.AddHotKey('<ctrl>+<9>', self.OnChangePage)  # Ctrl + Tab 切换Page
        listen.AddHotKey('<alt>+`', self.OnTogglePage)   # Ctrl + ~ 两个页面相关切换
        listen.Start()

    #################################### 启动exe ################################
    def OnTool(self, event):
        '''创建 启动exe 线程'''
        toolItem = self.FindWindowById(event.GetId())
        # Tool事件过滤： https://github.com/wxWidgets/Phoenix/issues/2347
        if toolItem is None:
            return
        self._BeforeStartExe()
        toolData = toolItem.GetClientData()
        type_ = self.coreMappings[toolData['type']]
        # 启动
        StartExeThread(
            toolData['cmd'], toolData['path'], toolData['env'],
            type_['class_name'], type_['process_keys'],
            lambda hwnd, pids: self._StartExeCallback(hwnd, pids, toolData)
        ).start()

    def _BeforeStartExe(self):
        '''启动exe前准备'''
        self.toolBar.Disable()
        self._busyInfo = wx.BusyInfo(
            wx.BusyInfoFlags().Parent(self)
            .Title('正在启动').Text('请稍后...')
            .Foreground(self.settings['border_colour'])
            .Background(self.settings['background_colour'])
        )

    def _AfterStartExe(self):
        '''启动exe后恢复'''
        self.toolBar.Enable()
        del self._busyInfo

    def _StartExeCallback(self, hwnd, pids, toolData):
        '''子线程回调'''
        if hwnd is None:
            realCallback = self._OnStartExeFailed
        else:
            realCallback = self._OnStartExeSuccessed
        wx.CallAfter(realCallback, hwnd, pids, toolData)   # 子线程不能直接更新UI
        wx.CallAfter(self._AfterStartExe)

    def _OnStartExeSuccessed(self, hwnd, pids, toolData):
        '''启动成功'''
        page = wx.Panel(self.notebook)
        self.hwnds.add(hwnd)
        self.pidExe[page.GetId()] = {'hwnd': hwnd, 'pids': pids, 'toolData': toolData}
        self._ExeAttachedToPage(hwnd, page, toolData['borders'])
        page.Bind(wx.EVT_SIZE, self.OnSize)
        self.notebook.AddPage(page, toolData['name'], True, toolData['index'])

    def _OnStartExeFailed(self, hwnd, pids, toolData):
        '''启动失败'''
        dlg = MessageDialog(self, '启动异常')
        dlg.ShowModal()
        dlg.Destroy()

    #################################### 关闭exe ################################
    def OnPageClose(self, event):
        '''关闭单页'''
        pid = self.notebook.GetPage(event.GetSelection()).GetId()
        exeInfo = self.pidExe[pid]
        KillPids(exeInfo['pids'])  # 清理相关的所有进程
        # win32gui.SendMessage(exeInfo['hwnd'], win32con.WM_CLOSE, 0, 0)  # 更好?
        self.hwnds.remove(exeInfo['hwnd'])
        del self.pidExe[pid]
        event.Skip()

    def OnClose(self, event):
        '''关闭所有页'''
        for _ in range(len(self.pidExe)):
            self.notebook.DeletePage(0)
        self.Destroy()

    ############################################################################
    def OnSize(self, event):
        '''调整窗口size'''
        event.Skip()
        pid = event.GetId()
        page = self.FindWindowById(pid)
        hwnd = self.pidExe[pid]['hwnd']
        borders = self.pidExe[pid]['toolData']['borders']
        self._ReSizeExeWindow(hwnd, page, borders)

    def OnFocus(self, event):
        '''空闲时, 自动切换焦点'''
        fgHwnd = win32gui.GetForegroundWindow()
        if fgHwnd not in self.hwnds:    # 非激活状态
            return
        if wx.GetMouseState().LeftIsDown():   # 点击状态忽略
            return
        index = self.notebook.GetSelection()
        if index == -1:
            return
        pid = self.notebook.GetPage(index).GetId()
        if pid not in self.pidExe:
            return
        if self.pidExe[pid]['hwnd'] == fgHwnd:  # 已经激活
            return
        self._SetFocus(self.pidExe[pid]['hwnd'])

    def OnUpdateConfig(self, event):
        '''配置更新 & 工具栏更新'''
        if GetConfigurations() != self.configurations:
            self.InitConfigurations()
            self.UpdateToolBar()

    ########################## 热键处理 ##########################################
    def WrapHotKeyHandler(handler):
        '''封装热键handler'''
        return lambda self: wx.CallAfter(handler, self)  # 子线程不能直接更新UI

    @WrapHotKeyHandler
    def OnChangePage(self):
        '''Page切换'''
        if win32gui.GetForegroundWindow() not in self.hwnds:   # 非激活状态
            return
        self.notebook.AdvanceSelection()

    @WrapHotKeyHandler
    def OnTogglePage(self):
        '''两个Page相互切换'''
        page = self.notebook.GetPreviousSelection()
        if 0 <= page < self.notebook.GetPageCount():
            self.notebook.SetSelection(page)

    ############################ win32api相关 ###################################
    def _ExeAttachedToPage(self, hwnd, page, borders):
        '''exe窗口附着到Page'''
        pos, size = self._CalcPageRect(page, borders)
        win32gui.SetParent(hwnd, page.GetHandle())
        flags = win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, *pos, *size, flags)
        win32gui.BringWindowToTop(hwnd)

    def _ReSizeExeWindow(self, hwnd, parent, borders):
        '''exe窗口调整位置和大小'''
        pos, size = self._CalcPageRect(parent, borders)
        win32gui.MoveWindow(hwnd, *pos, *size, True)

    def _SetFocus(self, hwnd):
        '''设置焦点'''
        # 必须的。确保切换窗口时，该窗口能够显示
        self.SetWindowStyle(self.GetWindowStyle() | wx.STAY_ON_TOP)
        # 调用SetForegroundWindow()会有很多限制
        # 此处在调用SetForegroundWindow()前事先发送一个键盘event来解决该问题
        # import win32com.client
        # shell = win32com.client.Dispatch('WScript.Shell')
        # shell.SendKeys('%')
        win32api.keybd_event(0x20, 0, 0, 0)
        win32gui.SetForegroundWindow(hwnd)
        self.SetWindowStyle(self.GetWindowStyle() & (~wx.STAY_ON_TOP))

    def _CalcPageRect(self, page, borders):
        '''计算子exe窗口位置和大小'''
        w, h = page.GetClientSize()
        w += borders['left'] + borders['right']  # exe 左/右边框
        h += borders['top'] + borders['bottom']  # exe 上/下边框
        return (-1 * borders['left'], -1 * borders['top']), (w, h)


class App(wx.App):
    def OnInit(self):
        self.InitSettings()
        frame = Frame(None)
        frame.Center()
        frame.Show()
        return super().OnInit()

    def InitSettings(self):
        '''初始化App配置'''
        with open(THEME_FILE, encoding='UTF-8') as fh:
            self.settings = json.loads(fh.read())


def main():
    app = App()
    app.MainLoop()


if __name__ == '__main__':
    main()
