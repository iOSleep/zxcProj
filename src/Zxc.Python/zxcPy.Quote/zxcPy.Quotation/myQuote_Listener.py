#-*- coding: utf-8 -*-
"""
Created on  张斌 2018-05-03 14:58:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    监听--基类 
"""
import sys, os, mySystem 

#引用根目录类文件夹--必须，否则非本地目录起动时无法找到自定义类
mySystem.m_strFloders.append('/Quote_Listener')
mySystem.Append_Us("", False) 
import myManager_Msg, myQuote_Data

#初始全局消息管理器
from myGlobal import gol 
gol._Init()     #先必须在主模块初始化（只在Main模块需要一次即可）

        
#行情监听
class Quote_Listener:
    def __init__(self, name):
        self.name = name
        self.pMMsg = gol._Get_Setting('manageMsgs')
    def getName(self):
        return self.name  
    def OnRecvQuote(self, quoteDatas):pass 
    #消息处理
    def OnHandleMsg(self, quoteDatas, strMsg):
        if(quoteDatas.autoSave == False): return False    #屏蔽旧数据处理
        #通知处理
        pSet = quoteDatas.setting
        for x in pSet.msgUsers_wx:
            #生成用户消息
            msg = self.OnCreatMsgInfo(x, strMsg, quoteDatas.data.time)
            if(self.pMMsg != None):
                self.pMMsg.OnHandleMsg(msg)
        return True
    #创建新消息
    def OnCreatMsgInfo(self, to_user, text, time = '', type = "TEXT", plat = 'weixin'):
        if(self.pMMsg != None):
            msg = self.pMMsg.OnCreatMsg()
        else: msg ={}

        #更新
        msg["user"] = to_user
        msg["text"] = text + "\r\n\t   --zxcRobot(Stock)   " + time
        msg["type"] = type
        msg["plat"] = plat
        return msg
    #创建消息内容
    def OnCreatMsgstr(self, quoteDatas):
        pass


#主启动程序
if __name__ == "__main__":
    pMMsg = gol._Get_Setting('manageMsgs')

    import myListener_Printer
    pListener = myListener_Printer.Quote_Listener_Printer()
    #pListener.OnRecvQuote(myQuote_Data.Quote_Data())

    users = ['茶叶一主号', '老婆']
    for i in range(0, 15):
        for x in users:
            strMsg = "Hello " + x 
            msg = pListener.OnCreatMsgInfo(x, strMsg, str(i))
            if(pMMsg != None):
                pMMsg.OnHandleMsg(msg)
    print()