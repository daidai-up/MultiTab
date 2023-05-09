#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File  :    StartExe.py
@Time  :    2023/04/24 16:46:49
@Author:    daidai_up
@Desc  :
'''
import os
import sys
import time
import psutil
import logging
import win32gui
import win32con
import win32process
from threading import Thread

logger = logging.getLogger(__name__)
BASE_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))


################################################################################
def formatPath(path=None):
    '''格式化Path'''
    if path is None:    # 默认当前Path
        path = BASE_PATH
    return os.path.abspath(path)


def formatCmdline(cmd):
    '''格式化命令行'''
    if isinstance(cmd, str):
        cmd = cmd.split()
    return os.path.normpath(' '.join(cmd))


def formatEnv(env=None):
    '''格式化环境变量'''
    newEnv = os.environ
    if isinstance(env, dict):   # 更新环境变量
        newEnv.update(env)
    return newEnv


################################################################################
def GetAllPids():
    '''获取所有进程ID'''
    return set(psutil.pids())


def GetUesrNewPids(oldPids):
    '''获取用户的新进程ID'''
    newPids = set()
    user = psutil.Process(os.getpid()).username()
    for pid in (GetAllPids() - oldPids):
        try:
            _user = psutil.Process(pid).username()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if _user == user:   # 根据用户过滤
            newPids.add(pid)
    return newPids


def KillPids(pids):
    '''清理进程'''
    for pid in pids:
        logger.info(f'kill: {pid}')
        try:
            os.kill(pid, 9)
        except OSError:
            continue


def GetAssociatedPids(pids, pkeys):
    '''根据关键字获取相关进程ID'''
    def isAssociated(cmdline):
        '''判断是否相关'''
        for pkey in pkeys:
            if pkey in cmdline:
                return True
        return False

    associatedPids = set()
    for pid in pids:
        try:
            process = psutil.Process(pid)
            if isAssociated(formatCmdline(process.cmdline()).lower()):
                associatedPids.add(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if len(associatedPids) != len(pkeys):   # 不完整
        associatedPids.clear()
    return associatedPids
################################################################################


def GetAllHwnds():
    '''获取所有窗口句柄'''
    def _walk(hwnd, lpararm):
        if win32gui.IsWindow(hwnd):
            hwnds.add(hwnd)

    hwnds = set()
    win32gui.EnumWindows(_walk, 0)
    return hwnds


def GetHwnd(hwndClassName, pids):
    '''按类名和进程号获取hwnd'''
    for hwnd in GetAllHwnds():
        # 窗口句柄对应的进程过滤
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid not in pids:
            continue
        if win32gui.GetClassName(hwnd) == hwndClassName:
            return hwnd
    return None


################################################################################
# 启动exe
################################################################################
class StartExeThread(Thread):
    '''启动exe的子线程'''
    def __init__(self, cmd, path, env, hwndClassName, pkeys, callback):
        super().__init__(daemon=True)
        self.cmd = formatCmdline(cmd)
        self.path = formatPath(path)
        self.env = formatEnv(env)
        self.hwndClassName = hwndClassName
        self.pkeys = pkeys
        self.callback = callback

    def run(self):
        hwnd = None
        associatedPids = set()
        try:
            hwnd, associatedPids = StartExe(
                self.cmd, self.path, self.env, self.hwndClassName, self.pkeys
            )
            logger.info(f'hwnd: {hwnd}  associatedPids: {associatedPids}')
        except Exception:
            logger.error('启动异常', exc_info=True)
        self.callback(hwnd, associatedPids)


def StartExe(cmd, path, env, hwndClassName, pkeys):
    '''启动一个exe窗口程序, 并返回Hwnd及Pids'''
    oldPids = GetAllPids()
    logger.info(f'cmd: {cmd}  path: {path} env: {env}')
    _StartExe(cmd, path, env)
    for _ in range(3):
        time.sleep(1)
        newPids = GetUesrNewPids(oldPids)
        associatedPids = GetAssociatedPids(newPids, pkeys)
        if associatedPids:
            break
    if not associatedPids:  # 未能成功获取关联Pids, 清理
        KillPids(newPids)
    hwnd = GetHwnd(hwndClassName, associatedPids)
    if hwnd is None:     # 未能成功获取窗口句柄, 清理
        KillPids(associatedPids)
    return hwnd, associatedPids


def _StartExe(cmd, path, env):
    '''启动一个exe窗口程序, 并隐藏'''
    startInfo = win32process.STARTUPINFO()  # 控制子进程启动方式的参数
    startInfo.dwFlags = win32process.STARTF_USESHOWWINDOW
    startInfo.wShowWindow = win32con.SW_HIDE   # 隐藏窗口
    flags = win32con.CREATE_NEW_CONSOLE | win32con.CREATE_NEW_PROCESS_GROUP
    win32process.CreateProcess(None, cmd, None, None, 0, flags, env, path, startInfo)
