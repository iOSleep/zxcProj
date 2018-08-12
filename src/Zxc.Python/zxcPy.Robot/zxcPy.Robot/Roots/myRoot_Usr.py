#-*- coding: utf-8 -*-
"""
Created on  张斌 2018-06-25 10:58:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com

    机器人-用户对象 真实用户对象，可能来自多个平台
"""
import sys, os, datetime, uuid, mySystem 

#引用根目录类文件夹--必须，否则非本地目录起动时无法找到自定义类
mySystem.Append_Us("", False)    
import myIO, myIO_xlsx, myData_Trans, myRoot_Prj


#用户对象
class myRoot_Usr():
    def __init__(self, usrName, usrName_Nick = "", usrID = "", fromID = ""): 
        self.usrID_sys = str(uuid.uuid1())   #用户ID--系统ID(唯一)
        self.usrID = ""         #用户ID
        self.usrName = usrName  #用户名
        self.usrName_Nick = ""  #用户名--昵称
        self.usrPlants = []     #用户类型(来源平台集)
        self.usrTag = ""        #标签
        self.usrRamak = ""      #备注
        self.usrPhone = ""      #电话号码
        self.usrNotes = ""      #描述信息
        self.usrInd = -1        #用户集中的序号
        self.usrTime_Regist = datetime.datetime.now()          #注册时间
        self.usrTime_Logined_Last = datetime.datetime.now()    #最后登录时间（请求）
        self.usrLoaded = False  
        self.usrPrj = myRoot_UsrPrj(usrName, "", "")           #当前功能管理对象 
        self._Init(usrName_Nick, usrID, fromID)
    # 初始用户信息
    def _Init(self, usrName_Nick = "", usrID = "", fromID = ""): 
        if(usrName_Nick != ""): self.usrName_Nick = usrName_Nick
        if(usrID != ""): self.usrID = usrID
        if(fromID != ""): 
            if(fromID in self.usrPlants == False):
                self.usrPlants.append(fromID)
        self.usrPrj = myRoot_UsrPrj(self.usrName, self.usrName_Nick, self.usrID)       #当前功能管理对象 
        return True 
        
    #新消息处理
    def Done(self, pPrj, Text, msgID = "", isGroup = False, pGroup = None):    
        #提取功能设置信息
        if(pPrj == None): 
            pPrj = self.usrPrj.prjInfo
            if(pPrj == None): return None                           #当前无功能启用
        if(self.usrPrj.prjInfo != None):
            if(pPrj.prjName != self.usrPrj.prjInfo.prjName):        #命令切换
                prjClass = self.usrPrj.prjDos.get(pPrj.prjName, None) 
                self.usrPrj._Change_prjDo(prjClass, pPrj)

        #提取当前功能对象
        prjClass = self.usrPrj.prjDo
        if(prjClass == None): 
            prjClass = self.usrPrj.prjDos.get(pPrj.prjName, None) 

        #调用消息处理，及其他处理 
        pReturn = self.usrPrj.Done(pPrj, prjClass, Text, msgID, isGroup, pGroup)
        for x in self.usrPrj.prjDos:
            prjDo = self.usrPrj.prjDos[x]
            if(prjDo.isBackUse):
                prjDo.Done(Text, msgID, isGroup, pGroup)
        return pReturn
#消息回复用户功能管理类
class myRoot_UsrPrj():
    def __init__(self, usrName, nickName = "", usrID = ""):
        self.usrName = usrName
        self.nickName = nickName
        self.usrID = usrID
        self.prjDos = {}            #消息处理类集合
        self.prjDo = None		    #消息处理类当前 
        self.prjInfo = None		    #功能信息
    #增加功能
    def _Change_prjInf(self, pPrj): 
        if(self.prjInfo == None):				        #当前记录功能
            self.prjInfo = pPrj
        elif(pPrj.prjName != self.prjInfo.prjName):	    #功能变更，关闭当前功能,并切换
            self.prjInfo = pPrj

        #更新运行状态
        prjDo = self.prjDo
        if(prjDo == None): prjDo = self.prjDos.get(pPrj.prjName, None) 
        if(prjDo != None):
            pPrj.isRunning = prjDo.isRunning

    #查找功能
    def _Find_prjDo(self, prjDo):
        pFind = self.prjDos.get(prjDo.prjName, None) 
        return pFind
    #增加功能
    def _Add_prjDo(self, prjDo): 
        if(prjDo == None): return True		#非命令，直接返回

        #查找功能并添加
        pFind = self._Find_prjDo(prjDo)
        if(pFind == None):					#无历史命令，直接添加
            self.prjDos[prjDo.prjName] = prjDo 
        return prjDo
    #增加功能集(所有全局非root功能)
    def _Add_prjDos(self, rootPrjs): 
        lstDos = rootPrjs.prjRoots.keys()
        for x in lstDos:
            prj = rootPrjs.prjRoots[x]
            if(prj.isRoot == False and prj.IsRunSingle()):    #非root功能，且非单例
                self._Add_prjDo(prj.prjClass) 
            elif(prj.isRunBack == True):    #后台运行
                self._Add_prjDo(prj.prjClass) 
    #增加功能
    def _Change_prjDo(self, prjDo, pPrj): 
        if(self.prjDo == None):				        #当前无命令，直接更新命令
            self._Add_prjDo(prjDo)
            self.prjDo = prjDo
        elif(prjDo.prjName != self.prjDo.prjName):	#命令变更，关闭当前功能,并切换
            self._Close_prjDo(self.prjDo)
            self._Add_prjDo(prjDo)
            self.prjDo = prjDo
        else: 
            return True							    #命令相同，直接返回
        if(pPrj != None):
            self._Change_prjInf(pPrj)
    #关闭功能
    def _Close_prjDo(self, prjDo): 
        if(prjDo == None): return False
        prjDo._Close()                #启动关闭命令

        #查找功能并关闭
        pFind = self._Find_prjDo(prjDo)
        if(pFind != None):      
            pFind.isRunning = prjDo.isRunning       #更新当前功能状态
            if(self.prjDo.isSingleUse == False):    #非单例运行功能移除   
                self.prjDos.pop(prjDo.prjName)
        return True
 
    #新消息处理
    def Done(self, pPrj, prjDo, Text, msgID = "", isGroup = False, pGroup = None):         
        #切换功能 
        self._Change_prjDo(prjDo, pPrj)
        if(self.prjDo == None): return None    #None表示无命令，忽略 
            
        #调用处理命令对象
        pReturn = self.prjDo.Done(Text, msgID, isGroup, pGroup)

		#命令有效性检查，失效则初始状态
        if(self.prjDo._Check() == False): 
            self._Close_prjDo(self.prjDo)
            self.prjDo = None
        return pReturn;

#用户对象集
class myRoot_Usrs():
    def __init__(self, usrName, userID): 
        self.usrName = usrName      #归属用户
        self.usrID_sys = userID     #归属用户ID
        self.usrList = {}           #用户集(按顺序索引)
        self.usrList_Name = {}      #用户集--(按名称索引)
        self.usrList_Name_Nick = {} #用户集--(按别名索引)
        self.usrList_usrID = {}     #用户集--(按ID索引)
        self.usrList_usrID_sys = {} #用户集--(按系统ID索引)

        #初始根目录信息
        strDir, strName = myIO.getPath_ByFile(__file__)
        self.Dir_Base = os.path.abspath(os.path.join(strDir, "../.."))  
        self.Dir_Setting = self.Dir_Base + "/Setting"
        self.Path_SetUser = self.Dir_Setting + "/UserInfo.xls"
        self.lstFields = ["ID","用户名","用户昵称","用户ID","来源平台","电话","标签","备注","描述","注册时间","最后登录时间"]
        self._Init()
    #初始参数信息等   
    def _Init(self):            
        #提取字段信息 
        dtUser = myIO_xlsx.loadDataTable(self.Path_SetUser, 0, 1)            #用户信息
        if(len(dtUser.dataMat) < 1 or len(dtUser.dataField) < 1): return
        lstFields_ind = dtUser.Get_Index_Fields(self.lstFields)

        #转换为功能权限对象集
        for dtRow in dtUser.dataMat:
            pUser = myRoot_Usr(dtRow[lstFields_ind["用户名"]])
            pUser.usrID_sys = dtRow[lstFields_ind["ID"]]
            pUser.usrName_Nick = dtRow[lstFields_ind["用户昵称"]]
            pUser.usrID = dtRow[lstFields_ind["用户ID"]]
            pUser.usrPlants = dtRow[lstFields_ind["来源平台"]].split(',')
            pUser.usrPhone = dtRow[lstFields_ind["电话"]]
            pUser.usrTag = dtRow[lstFields_ind["标签"]]
            pUser.usrRamak = dtRow[lstFields_ind["备注"]]
            pUser.usrNotes = dtRow[lstFields_ind["描述"]]
            pUser.usrTime_Regist = myData_Trans.Tran_ToDatetime(dtRow[lstFields_ind["注册时间"]])
            pUser.usrTime_Logined_Last = myData_Trans.Tran_ToDatetime(dtRow[lstFields_ind["最后登录时间"]])
            pUser.usrLoaded = True  
            self._Index(pUser)      #索引用户信息
    def _Save(self):            
        dtUser = myIO_xlsx.DtTable()    #用户信息表
        dtUser.dataName = "dataName"
        dtUser.dataField = self.lstFields
        dtUser.dataFieldType = ['string', 'string', 'string', 'string', 'string', 'string', 'string', 'string', 'string', 'datetime', 'datetime']
       
        # 组装行数据
        keys = self.usrList.keys()
        for x in keys:
            pUser = self.usrList[x]
            pValues = []
            pValues.append(pUser.usrID_sys)
            pValues.append(pUser.usrName)
            pValues.append(pUser.usrName_Nick)
            pValues.append(pUser.usrID)
            pValues.append(myData_Trans.Tran_ToStr(pUser.usrPlants))
            pValues.append(pUser.usrPhone)
            pValues.append(pUser.usrTag)
            pValues.append(pUser.usrRamak)
            pValues.append(pUser.usrNotes)
            pValues.append(pUser.usrTime_Regist.strftime("%Y-%m-%d %H:%M:%S"))
            pValues.append(pUser.usrTime_Logined_Last.strftime("%Y-%m-%d %H:%M:%S"))
            dtUser.dataMat.append(pValues)

        # 保存
        dtUser.Save(self.Dir_Setting, "UserInfo", 0, 0, True, "用户信息表")

    #查找 
    def _Find(self, usrName, usrName_Nick, usrID, usrID_sys = "", usrType = "", bCreate_Auto = False): 
        pUser = None

        #按名称查找
        if(pUser == None):
            pUser = self._Find_ByName(usrName.lower())
        if(pUser == None):
            pUser = self._Find_ByName_Nick(usrName_Nick.lower())

        #按ID查找
        if(pUser == None):
            pUser = self._Find_ByID(usrID.lower())
        if(pUser == None):
            pUser = self._Find_ByID_sys(usrID_sys.lower())
 
        # 不存在
        if(bCreate_Auto and pUser == None):
            pUser = myRoot_Usr(usrName, usrName_Nick, usrID, usrType)
            self._Index(pUser)
        # 信息更新, 并返回
        self._Refresh(pUser)
        return pUser
    def _Find_ByID(self, usrID): 
        return self.usrList_usrID.get(usrID, None)
    def _Find_ByID_sys(self, usrID_sys): 
        return self.usrList_usrID_sys.get(usrID_sys, None)
    def _Find_ByName(self, usrName): 
        return self.usrList_Name.get(usrName, None)
    def _Find_ByName_Nick(self, usrName_Nick): 
        return self.usrList_Name_Nick.get(usrName_Nick, None)

    # 添加用户
    def _Add(self, pUser): 
        if(pUser == None): return False
        if(pUser.usrName == ""): 
            pUser.usrName = pUser.usrName_Nick

        # 不存在才可添加    
        if(self._Find(pUser.usrName, pUser.usrName_Nick, pUser.usrID, pUser.usrID_sys, "", False) == None):
            self._Index(pUser)
            return True
        return False 
    # 用户索引
    def _Index(self, pUser): 
        ind = len(self.usrList.keys()) 
        self.usrList[ind] = pUser
        pUser.usrInd = ind        #用户集中的序号

        #用户集--(按名称索引)
        if(pUser.usrName != ""):
            if(self.usrList_Name.get(pUser.usrName, None) == None):
                self.usrList_Name[pUser.usrName] = pUser
                
        #用户集--(按名称索引)
        if(pUser.usrName_Nick != ""):
            if(self.usrList_Name_Nick.get(pUser.usrName_Nick, None) == None):
                self.usrList_Name_Nick[pUser.usrName_Nick] = pUser
                
        #用户集--(按ID索引)
        if(pUser.usrID != ""):
            if(self.usrList_usrID.get(pUser.usrID, None) == None):
                self.usrList_usrID[pUser.usrID] = pUser
                
        #用户集--(按系统ID索引)
        if(pUser.usrID_sys != ""):
            if(self.usrList_usrID_sys.get(pUser.usrID_sys, None) == None):
                self.usrList_usrID_sys[pUser.usrID_sys] = pUser
    # 刷新更新部分信息
    def _Refresh(self, pUser): 
        # 信息更新
        if(pUser != None):
            pUser.usrTime_Logined_Last = datetime.datetime.now()

    
    # 用户是否存在
    def IsExist(self, usrName, usrName_Nick, usrID, usrID_sys = ""): 
        pUser = self._Find(usrName, usrName_Nick, usrID, usrID_sys, "", False) 
        if(pUser == None): return False
        return True
    # 添加用户
    def Add(self, msgInfo = {}, canUpdata = False): 
        usrName = msgInfo.get("usrName", "")
        usrName_Nick = msgInfo.get("usrName_Nick", "")
        usrID = msgInfo.get("usrID", "")
        usrType = msgInfo.get("usrType", "")
        if(usrName == None): return False

        # 新用户
        pUser = self._Find(usrName, usrName_Nick, usrID, "", usrType, True)
        if(pUser.usrLoaded and canUpdata == False): return False

        # 信息更新
        pUser.usrPhone = msgInfo.get("usrPhone", "")  
        pUser.usrTag = msgInfo.get("usrTag", "")  
        pUser.usrRamak = msgInfo.get("usrRamak", "")  
        pUser.usrNotes = msgInfo.get("usrNotes", "") 
        if(usrType != ""):
            if(not usrType in pUser.usrPlants):
                pUser.usrPlants.append(usrType)
        return True
    # 添加用户
    def Del(self, usrName): 
        usrName = usrName.strip().lower()
        pUser = self._Find(usrName, usrName, "", "", "", False) 
        if(pUser == None): return False
        self.usrList.pop(pUser.usrInd)
        self.usrList_Name.pop(pUser.usrName)
        self.usrList_Name_Nick.pop(pUser.usrName_Nick)
        self.usrList_usrID.pop(pUser.usrID)
        self.usrList_usrID_sys.pop(pUser.usrID_sys)
        return True
    

#主启动程序
if __name__ == "__main__":
    pUsers = myRoot_Usrs("zxcPy", "@@zxcPy")
    pUser = pUsers.Add({'usrName': "Test",'usrName_Nick': "测试",'usrID': "@@1" ,'usrType': "wx"}, True)
    pUser = pUsers.Add({'usrName': "Test3",'usrName_Nick': "测试3",'usrID': "@@3" })
    pUsers.Del("测试3")

    pUsers._Save()
    print(pUser)
