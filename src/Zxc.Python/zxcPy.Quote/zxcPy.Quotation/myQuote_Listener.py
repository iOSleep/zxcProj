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
import myData, myQuote_Data, myManager_Msg

#初始全局消息管理器
from myGlobal import gol 
gol._Init()     #先必须在主模块初始化（只在Main模块需要一次即可）

        
#行情监听
class Quote_Listener:
    def __init__(self, name = "", nameAlias = ""):
        self.name = name
        self.nameAlias = nameAlias
        self.pMMsg = gol._Get_Setting('manageMsgs')
        self.pSet = None
    def getName(self):
        return self.name  
    def OnUpdataSet(self, quoteDatas):pass 
    def OnRecvQuote(self, quoteDatas):pass 
    #消息处理
    def OnHandleMsg(self, quoteDatas, strMsg, nSleep = 0):
        if(quoteDatas.autoSave == False): return False          #屏蔽旧数据处理
        if(strMsg == ""): return False

        #通知处理
        self.pSet = quoteDatas.setting.GetSetting(self.nameAlias)
        if(self.pSet == None): return False
        for x in self.pSet.msgUsers:
            #生成用户消息
            usrSet = self.pSet.msgUsers[x]
            if(usrSet[1] == False): continue

            usrPlat = usrSet[0]
            msg = self.OnCreatMsgInfo(x, strMsg, quoteDatas.data.time, plat=usrPlat)
            if(self.pMMsg != None):
                self.pMMsg.OnHandleMsg(msg, usrPlat, True, nSleep)   #推送至消息处理器处理(使用消息校正)
        self.OnHandleMsg_desk(quoteDatas)                            #消息处理-桌面
        return True
    def OnHandleMsgs(self, quoteDatas, lstMsgs, nSleep = 0):
        if(quoteDatas.autoSave == False): return False          #屏蔽旧数据处理

        #通知处理
        self.pSet = quoteDatas.setting.GetSetting(self.nameAlias)
        if(self.pSet == None): return False
        for x in lstMsgs:
            #生成用户消息
            usrPlat = x["usrPlat"]
            msg = self.OnCreatMsgInfo(x['usrName'], x["msg"], quoteDatas.data.time, plat=usrPlat)
            if(self.pMMsg != None):
                self.pMMsg.OnHandleMsg(msg, usrPlat, True, nSleep)   #推送至消息处理器处理(使用消息校正)
        return True
    #消息处理-桌面
    def OnHandleMsg_desk(self, quoteDatas):
        #涨跌标识    
        tag = quoteDatas.data.name
        dValue_N = quoteDatas.data.priceRiseFall * 100
        strTag0 = myData.iif(dValue_N >=0, "涨", "跌")
        strTag0 = myData.iif(dValue_N ==0, "平", strTag0) 
        strMsg = strTag0 + str(round(dValue_N,2)) + "%" 
        for x in self.pSet.msgUsers:
            #生成用户消息
            if(x != "@*股票监测--大盘行情" and x != "@*股票监测--自选行情" and x != "@*测试群"):
                continue
            usrPlat = self.pSet.msgUsers[x]
            if(usrPlat != "wx"): continue

            msg = self.OnCreatMsgInfo(x, strMsg, quoteDatas.data.time, plat='wx')            
            msg['typeCmd'] = 'quote'
            msg['infCmd'] = {"tag": tag, "value": dValue_N, "msg": strMsg}            
            if(self.pMMsg != None):
                self.pMMsg.usePrint = True
                self.pMMsg.OnHandleMsg(msg, "usrWin", True)       #推送消息(桌面)
    #创建新消息
    def OnCreatMsgInfo(self, to_user, text, time = '', type = "TEXT", plat = 'wx'):
        if(self.pMMsg != None):
            msg = self.pMMsg.OnCreatMsg()
        else: msg ={}

        #尾部标签
        strTag = "  --zxcRobot(Stock)  " + time
        if(len(strTag) < 34):
            strTag = (34 - len(strTag)) * " " + strTag

        #更新 
        msg["usrName"] = to_user
        msg["msg"] = text + "\n" + strTag
        msg["msgType"] = type
        msg["usrPlat"] = plat
        return msg
    #创建消息内容
    def OnCreatMsgstr(self, quoteDatas):
        pass
    #功能是否可用
    def IsEnable(self, quoteDatas):
        self.pSet = quoteDatas.setting.GetSetting(self.nameAlias)
        if(self.pSet != None):
            return self.pSet.isValid
        return False


#主启动程序
if __name__ == "__main__":
    pMMsg = gol._Get_Setting('manageMsgs')

    import myListener_Printer
    pListener = myListener_Printer.Quote_Listener_Printer()
    #pListener.OnRecvQuote(myQuote_Data.Quote_Data())

    users = ['茶叶一主号', '@*测试群']
    for i in range(0, 2):
        for x in users:
            strMsg = "Hello " + x 
            msg = pListener.OnCreatMsgInfo(x, strMsg, str(i))
            if(pMMsg != None):
                pMMsg.OnHandleMsg(msg, '', True)
    print()
