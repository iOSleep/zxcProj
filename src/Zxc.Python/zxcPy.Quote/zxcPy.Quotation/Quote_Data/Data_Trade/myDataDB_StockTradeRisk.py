#-*- coding: utf-8 -*-
"""
Created on  张斌 2019-09-24 22:58:00 
    @author: zhang bin
    @email:  zhangbin@gsafety.com
    
    自定义简易库表操作-股票风险设置记录
"""
import sys, os, time, copy, datetime, mySystem
from collections import OrderedDict
from operator import itemgetter, attrgetter
from decimal import Decimal

#引用根目录类文件夹--必须，否则非本地目录起动时无法找到自定义类
mySystem.Append_Us("../Prjs", False, __file__)
mySystem.Append_Us("../../../zxcPy.Quotation", False, __file__)
mySystem.Append_Us("../../../zxcPy.Quotation/Quote_Source", False, __file__)
mySystem.Append_Us("", False) 
import myEnum, myIO, myIO_xlsx, myData, myData_DB, myData_Trans, myManager_Msg, myDebug #myQuote_Setting
import myQuote



# 股票风险设置记录 
class mySet_StockTradeRisk():
    def __init__(self, dictSets = None, nameDB = "zxcDB_StockTradeRisk", dir = ""):  
        self.ID = -1
        self.usrID = ""
        self.stockID = ""           #标的编号
        self.stockName = ""         #标的名称
        self.stockAvg = 0           #标的均价-所有买入 
        self.stockNum = 0           #标的数量
        self.sumStock_Trade = 0     #更新交易数量-买卖
        self.stockPosition = 1      #标的仓位-当前
        self.stockFee = 0.003       #标的手续费率,卖出时统一计算
        
        self.stopProfit = 0.10          #止盈线，默认为6%
        self.stopLoss = -0.02           #止损线，默认为-2%
        self.stopProfit_Dynamic = True  #动态止盈 
        self.stopLoss_Dynamic = True    #动态止损 
        self.stopProfit_Retreat = 0.01  #止盈回撤，默认为1%
        self.stopLoss_Retreat = 0.01    #止损回撤，默认为1%
        self.stopProfit_Trade = 0.2     #止盈交易比例，默认为20%
        self.stopLoss_Trade = 0.2       #止损交易比例，默认为20%
        
        self.priceMax = 0               #最高价格，默认为0，用于统计
        self.priceCost = 0              #成本价格，默认为0，买卖时更新，当前仓位的实际成本均价，累计卖出收益，卖出手续费
        self.priceAvg_sell = 0          #卖出均价，默认为0，用于统计
        self.priceNow = 0               #当前价格，默认为0，用于统计
        self.profitMax_Stage = 0        #阶段浮盈，默认为0，触发止盈、止损时更新
        self.profitMax = 0              #最大浮盈，默认为0，触发止盈时更新
        self.profitMin = 0              #最小浮盈，默认为0，触发止损时更新
        self.profitNow = 0              #阶段浮盈-当前价格，默认为0，用于统计
        self.stopProfit_goon = False    #正止盈状态
        self.logOperates = []           #操盘记录

        self.datetime = datetime.datetime.now()  
        self.remark = ""                #备注
        self.valid = True               #是否有效
        self.dictSets = {}              #字典型设置信息
        self.Trans_FromDict(dictSets, False)

    # 转换为字典结构
    def Trans_ToDict(self, dictSets = None):  
        if(dictSets == None): dictSets = self.dictSets
        dictSets['ID'] = self.ID
        dictSets['用户名'] = self.usrID
        dictSets['标的编号'] = self.stockID
        dictSets['标的名称'] = self.stockName
        dictSets['标的均价'] = round(self.stockAvg, 4)
        dictSets['标的数量'] = self.stockNum
        dictSets['标的仓位'] = round(self.stockPosition, 4)
        dictSets['手续费率'] = round(self.stockFee, 4)
        
        dictSets['止盈线'] = self.stopProfit
        dictSets['止损线'] = self.stopLoss
        dictSets['动态止盈'] = self.stopProfit_Dynamic
        dictSets['动态止损'] = self.stopLoss_Dynamic
        dictSets['止盈回撤'] = self.stopProfit_Retreat
        dictSets['止损回撤'] = self.stopLoss_Retreat
        dictSets['止盈比例'] = self.stopProfit_Trade
        dictSets['止损比例'] = self.stopLoss_Trade
        
        dictSets['最高价格'] = round(self.priceMax, 4)
        dictSets['成本价格'] = round(self.priceCost, 4)
        dictSets['卖出均价'] = round(self.priceAvg_sell, 4)
        dictSets['当前价格'] = round(self.priceNow, 4)
        dictSets['阶段浮盈'] = round(self.profitMax_Stage, 4)
        dictSets['最高浮盈'] = round(self.profitMax, 4)
        dictSets['当前浮盈'] = round(self.profitNow, 4)
        dictSets['止盈状态'] = self.stopProfit_goon

        dictSets['日期'] = self.datetime
        dictSets['isDel'] = not self.valid 
        dictSets['备注'] = self.remark
        dictSets['操作日志'] = self.logOperates
        return self.dictSets
    # 转换为对象，由字典结构
    def Trans_FromDict(self, dictSets, canLog = True):  
        #验证股票信息
        #pStocks = gol._Get_Value('setsStock', None)
        #lstStock = pStocks._Find(dictSets.get('标的编号',""), dictSets.get('标的名称',""), exType="")
        #if(len(lstStock) != 1): return{}
        #pStock = lstStock[0]
        #self.stockID = pStock.code_id
        #self.stockName = pStock.code_name
        

        #交易信息必须存在
        if(dictSets == None): return False
        index = -1
        strTime = dictSets.get('日期', "")
        if(type(strTime) != str): strTime = myData_Trans.Tran_ToDatetime_str(dictSets['日期'], "%Y-%m-%d %H:%M:%S")
        for x in self.logOperates:
            if(x['时间'] == strTime):
                index += 1
                break

        #解析信息
        self.ID = dictSets.get('ID',-1)
        self.usrID = dictSets['用户名']
        self.stockID = dictSets.get('标的编号',"")
        self.stockName = dictSets.get('标的名称',"")  

        stockNum_temp = myData_Trans.To_Float(str(dictSets.get("标的数量", 0)))
        stockAvg_temp = myData_Trans.To_Float(str(dictSets.get("标的均价", 0)))
        stockPosition_temp = myData_Trans.To_Float(str(dictSets.get("标的仓位", 1)))
        if(stockNum_temp == 0 or stockNum_temp == 0): return False

        self.datetime = dictSets.get("日期", self.datetime)
        self.remark = dictSets.get("备注", self.remark)
        self.isDel = not dictSets.get('isDel', not self.valid)  

        if(canLog):
            #提取时间
            strTime = self.datetime
            if(type(strTime) != str): strTime = myData_Trans.Tran_ToDatetime_str(strTime, "%Y-%m-%d %H:%M:%S")

            #存在则更新
            if(index == -1):
                self.logOperates.append({"股数": stockNum_temp,"股价":stockAvg_temp,"时间": strTime})    #仓位变化记录
            else:
                self.logOperates[index] = {"股数": stockNum_temp,"股价":stockAvg_temp,"时间": strTime}
        else:
            self.logOperates = dictSets.get('操作日志', self.logOperates)
        
        #计算仓位变化
        if(index == -1):
            stockNum = self.stockNum
            if(stockNum_temp > 0):
                #买入时更新成本 
                stockNum += abs(stockNum_temp) 
                stockMoney = self.stockAvg * self.stockNum + stockNum_temp * stockAvg_temp
                self.stockPosition = (stockNum_temp * stockPosition_temp + self.stockNum * self.stockPosition) / stockNum
                self.stockAvg = stockMoney / stockNum
                self.stockNum = int(stockNum) 
            else:
                #卖出更新仓位
                self.stockPosition = (stockNum_temp * stockPosition_temp + self.stockNum * self.stockPosition) / stockNum
                if(self.stockPosition <= 0):
                    self.stockPosition = 0
                    self.valid = False
        self.stockFee = dictSets.get("手续费率", self.stockFee)

        self.stopProfit = dictSets.get("止盈线", self.stopProfit)
        self.stopLoss = dictSets.get("止损线", self.stopLoss)
        self.stopProfit_Dynamic = dictSets.get("动态止盈", self.stopProfit_Dynamic)
        self.stopLoss_Dynamic = dictSets.get("动态止损", self.stopLoss_Dynamic)
        self.stopProfit_Retreat = dictSets.get("止盈回撤", self.stopProfit_Retreat)
        self.stopLoss_Retreat = dictSets.get("止损回撤", self.stopLoss_Retreat)
        self.stopProfit_Trade = dictSets.get("止盈比例", self.stopProfit_Trade)
        self.stopLoss_Trade = dictSets.get("止损比例", self.stopLoss_Trade)
        
        self.priceMax = dictSets.get("最高价格", self.priceMax)
        self.priceCost = dictSets.get("成本价格", self.stockAvg)
        self.priceAvg_sell = dictSets.get("卖出均价", stockAvg_temp)
        self.priceNow = dictSets.get("当前价格", stockAvg_temp)
        self.profitMax_Stage = dictSets.get("阶段浮盈", self.profitMax_Stage)
        self.profitNow = dictSets.get("当前浮盈", self.profitNow)
        self.stopProfit_goon = dictSets.get("止盈状态", self.stopProfit_goon)
        return True

    # 统计收益（实际浮盈、已卖出收益）
    def Static_Profit(self, strokPrice, bUpdata = True):  
        #累计买入、卖出
        sumStock_Buy = 0
        sumMoney_Buy = 0
        sumStock_Sell = 0
        sumMoney_Sell_fee = 0
        for x in self.logOperates:
            if(x["股数"] < 0):
                sumStock_Sell += x["股数"]
                sumMoney_Sell_fee += x["股价"] * x["股数"]      #计算含手续费
            else:
                sumStock_Buy += x["股数"]
                sumMoney_Buy += x["股价"] * x["股数"]           #计算含手续费

        #统计计算
        sumStock_Trade = sumStock_Buy + abs(sumStock_Sell)
        sumMoney_Sell = sumMoney_Sell_fee * (1 - self.stockFee)                     #卖出总金额（不含手续费）
        sumMoney = (sumStock_Buy + sumStock_Sell) * strokPrice - sumMoney_Sell      #当前市值（含卖出）
        sumStock = sumStock_Buy + sumStock_Sell
        profitNow = sumMoney / sumMoney_Buy - 1                                     #当前浮盈-阶段
        stockAvg_sell = 0
        if(sumStock_Sell != 0):
            stockAvg_sell = sumMoney_Sell_fee / sumStock_Sell                       #卖出均价
        stockCost = (sumMoney_Buy + sumMoney_Sell) / myData.iif(sumStock <= 0, sumStock_Buy, sumStock)

        #更新
        if(bUpdata == True):
            self.sumStock_Trade = sumStock_Trade            #更新交易数量-买卖
            self.priceCost = stockCost                      #更新成本价格
            self.priceNow = strokPrice                      #更新当前价格
            self.priceAvg_sell = stockAvg_sell              #更新卖出均价
            self.profitNow = profitNow                      #更新当前阶段浮盈
            if(self.profitMax < self.profitMax_Stage):
                self.profitMax = self.profitMax_Stage       #更新最大浮盈
        return profitNow, stockCost
    
# 股票风险监测类 
class myMonitor_TradeRisk():
    def __init__(self, minPrice5, maxPrice5, minPrice10=-1, maxPrice10=-1, minPrice20=-1, maxPrice20=-1):  
        self.setRisk = mySet_StockTradeRisk()   #交易风险设置
        self.maxPrice5 = maxPrice5              #5日最高价
        self.maxPrice10 = maxPrice10            #10日最高价
        self.maxPrice20 = maxPrice20            #20日最高价
        self.minPrice5 = minPrice5              #5日最低价
        self.minPrice10 = minPrice10            #10日最低价
        self.minPrice20 = minPrice20            #20日最低价
        self.maxPrice = max(self.maxPrice5, self.maxPrice10, self.maxPrice20)
        self.minPrice = min(self.minPrice5, self.minPrice10, self.minPrice20)

        self.isStop_Profit = False              #是否激活止盈，与止损互斥
        self.isStop_Loss = False                #是否激活止损，与止盈互斥
        self.stopProfit_Retreat = 0             #当前止盈回撤，超过止盈线以上则为2倍
        self.stopProfit_Trade = 0               #当前止盈交易比例
        self.markStop_Profit = 0                #标记止盈提醒次数
        self.sumStock_Trade = 0                 #更新交易数量-买卖

    #初始风险设置
    def initSet(self, setRisk, setDB):
        self.setRisk = setRisk
        self.setDB = setDB

        #检查止盈止损状态
        self.checkState(self.maxPrice)
        self.checkState(self.minPrice)
    #保存修改
    def saveSet(self):
        dictRisk = self.setRisk.Trans_ToDict()
        self.setDB._Updata(self.setRisk.ID, dictRisk, True, False)
    #更新交易操作
    def updataTrade(self, strokPrice, stockNum):
        #复制当前设置
        rowInfo = {'ID': self.setRisk.ID,'用户名': self.setRisk.usrID, '标的编号': self.setRisk.stockID, '标的名称': self.setRisk.stockName, '标的均价': strokPrice, '标的数量': stockNum}
        self.setRisk.Trans_FromDict(rowInfo) 
        self.setRisk.Static_Profit(strokPrice)  #收益统计
        self.saveSet()                          #保存修改

    #通知接收新行情
    def notifyQuotation(self, price, bSave_Auto = True):
        #检查止盈止损状态
        self.checkState(price)

        #执行动态止盈止损
        strTitle = ""
        if(self.isStop_Profit):
            strTitle = self.stopProfit(price, bSave_Auto)
        elif(self.isStop_Loss):
            self.isStop_Loss = False            
        else:
            prift = price / self.setRisk.stockAvg - 1
            strProfit = str(Decimal((prift * 100)).quantize(Decimal('0.00'))) + "%"
            myDebug.Debug("收益：" + strProfit)
            
            #触发止盈-每次启动提醒一次
            if(self.setRisk.stopProfit_goon and self.markStop_Profit == 0):
                strTitle = self.getTitleMark(price, True) 
        return strTitle

            
    #止盈操作(1.非动态，到达位置立即卖出，1.动态，到达位置触发止盈) 
    """
    交易策略：
    1.前20/10/5日高点取最高，日内高点，回撤起始1%建议平仓 20%，回撤2%建议平仓 20%，回撤3%建议平仓 20%，回撤4%建议平仓 20%，回撤5%建议平仓 20%
    2.建议需要记录，便于分阶段处理。
    3.止盈规则：
	    达到指定涨幅时（默认10%），触发交易止盈/动态止盈。
	    动态止盈：
		    按回撤比例分阶段分步卖出，从当前最高点回撤1%时第一次触发，之后每回撤1%触发一次，连续回撤5%时全部卖出。
		    当涨幅回升，突破新高时，初始回撤触发状态，即从高点再次回撤1%时触发，直到卖出完毕。
			    突破新高规则：涨幅突破前一阶段止盈点，涨幅突破止盈涨幅线，涨幅突破10/5日高点。突破后实时比对更新新高，更新最高点。
            动态回撤计算，按浮盈与止盈线比值来确定倍数，最大6%
			
	    关键点：止盈线、10/5日高点、回撤后实时新高
    """
    def stopProfit(self, price, bSave_Auto = False):
        #提取股票交易建议信息
        tradeInfo = self.getTradeInfo(price)
        numSell = tradeInfo['numSell'] 

        #自动更新交易记录
        if(bSave_Auto):
            self.updataTrade(price, -numSell)
        else:
            self.setRisk.Static_Profit(price)  #收益统计

        #返回提示信息
        return self.getTitleMark(price, True, numSell)
    
    #提取返回信息
    def getTitleMark(self, price, isStopProfit = True, numSell = 0):
        #提取股票交易建议信息
        tradeInfo = self.getTradeInfo(price) 
        prift = tradeInfo['prift']
        priftMax = tradeInfo['priftMax']
        numSell = tradeInfo['numSell'] 

        #组装提示要素
        strPrice = str(Decimal(price).quantize(Decimal('0.00'))) + " 元"    #价格
        strSell = str(numSell) + "股"                                       #股数
        strRetreat = str(Decimal((self.stopProfit_Retreat * 100)).quantize(Decimal('0.0'))) + "%"       #回撤
        strTrade = str(Decimal((self.stopProfit_Trade * 10)).quantize(Decimal('0.0'))) + "成"           #仓位
        strProfitNow = str(Decimal((self.setRisk.profitNow * 100)).quantize(Decimal('0.00'))) + "%"     #当前浮盈
        strProfit = str(Decimal((prift * 100)).quantize(Decimal('0.0'))) + "%"                          #当前收益
        strMax = str(Decimal((priftMax * 100)).quantize(Decimal('0.00'))) + "%"                         #最高浮盈
        strMaxStage = str(Decimal((self.setRisk.profitMax_Stage * 100)).quantize(Decimal('0.00'))) + "%"#阶段浮盈-前高

        #组装各类提示
        strReutrn = ""
        if(isStopProfit):
            if(self.setRisk.stopProfit_goon):
                #触发止盈线-第一次
                if(self.markStop_Profit == 0):
                    strStopProfit = str(Decimal((self.setRisk.stopProfit * 100)).quantize(Decimal('0.0'))) + "%"    #回撤
                    strReutrn = F"{self.setRisk.stockName}: {strPrice}, 浮盈超 {strStopProfit}.\r\n操作策略: 超过止盈线, 动态止盈启动.\r\n策略收益: {strProfit}, 涨幅前高 {strMaxStage}, 最高 {strMax}."
                    self.markStop_Profit += 1
                else:
                    #正常止盈-动态
                    strReutrn = F"{self.setRisk.stockName}: {strPrice}, 回撤逾 {strRetreat}.\r\n操作策略: 建议止盈, 操作 {strTrade}仓, 卖出 {strSell}.\r\n策略收益: {strProfit}, 当前浮盈: {strProfitNow}, 涨幅前高 {strMaxStage}, 最高 {strMax}."
            else:
                #正常止盈-静态
                if(self.isStop_Profit and self.setRisk.stopProfit_Dynamic == False):
                    strStopProfit = str(Decimal((self.setRisk.stopProfit * 100)).quantize(Decimal('0.0'))) + "%"    #回撤
                    strReutrn = F"{self.setRisk.stockName}: {strPrice}, 浮盈超 {strStopProfit}.\r\n操作策略: 建议止盈, 操作 全仓, 卖出 {strSell}.\r\n策略收益: {strProfit}, 涨幅前高 {strMaxStage}, 最高 {strMax}."
            #设置同步
            self.setRisk.profitMax_Stage = prift    #修正阶段高值
            self.isStop_Profit = False              #恢复状态
        else:
            pass
        myDebug.Debug(strReutrn.replace("\r\n", ""))
        return strReutrn
    
    #提取股票交易建议信息
    def getTradeInfo(self, price, numSell = 0):
        #股票信息
        prift = price / self.setRisk.stockAvg - 1                           #涨幅
        priftMax = self.setRisk.priceMax / self.setRisk.stockAvg - 1        #最大涨幅
        self.stopProfit_Trade = myData.iif(self.setRisk.stopProfit_Dynamic, self.setRisk.stopProfit_Trade, 1)
        if(numSell == 0):
            numSell = self.stopProfit_Trade * self.setRisk.stockNum         #卖出数量
            if(self.stopProfit_Trade > self.setRisk.stockPosition):         #低仓位修正
                numSell = self.setRisk.stockPosition * self.setRisk.stockNum    
            numSell = int(Decimal(numSell) + Decimal(0.5))
        return {"prift": prift, "priftMax": priftMax, "numSell": numSell}


    #检查止盈止损状态
    def checkState(self, price):
        #仓位检查
        if(self.setRisk.stockPosition <=0): return

        #计算盈亏比例,更新统计值
        prift = round(price / self.setRisk.stockAvg - 1, 6)
        if(self.setRisk.priceMax < price):
            self.setRisk.priceMax = price

        #区分止盈、止损，互斥
        if(prift > 0):
            #过止盈线触发止盈
            if(self.setRisk.stopProfit_Dynamic):    #开启动态止盈
                #区分是否正止盈中
                if(self.setRisk.stopProfit_goon):
                    #校正回撤动态幅度 
                    self.stopProfit_Retreat = self.checkPiofitRetreat()
                    
                    #回撤超过界限，激活止盈(精度修正+0.00000001,避免计算过程小数点精度导致的临界计算错误)
                    if(self.setRisk.profitMax_Stage - prift - self.stopProfit_Retreat + 0.00000001 >= 0.0):
                        self.setState(True)
                    else:
                        #更新阶段最高价
                        if(self.setRisk.profitMax_Stage < prift):
                            self.setRisk.profitMax_Stage = prift      #赋值阶段最高价

                        #其他止盈逻辑-特殊
                        pass
                else:   
                    #非止盈状态，超过止盈线时激活止盈
                    if(prift >= self.setRisk.stopProfit):
                        self.setRisk.stopProfit_goon = True     #激活止盈状态
                        self.setRisk.profitMax_Stage = prift    #赋值阶段最收益-止盈时
            else:
                #超过止盈线时激活止盈
                if(prift >= self.setRisk.stopProfit):
                    self.isStop_Profit = True
                    self.isStop_Loss = False
        else:
            if(self.setRisk.stopLoss_Dynamic):      #开启动态止损
                if(prift >= self.setRisk.stopLoss):
                    self.isStop_Loss = True
                    self.isStop_Profit = False

        #记录交易数量，便于区分有无处理            
        self.sumStock_Trade = self.setRisk.sumStock_Trade
    #校正回撤动态幅度 
    def checkPiofitRetreat(self):
        #默认回撤为设置值 
        self.stopProfit_Retreat = self.setRisk.stopProfit_Retreat
            
        #特殊修正
        if(1 == 1):
            #计算当前与前期高点差价
            profitStage = self.setRisk.profitMax_Stage - self.setRisk.profitMax
            
            #回撤率修正，阶段盈利为前高2倍以上，扩大回撤容忍范围为2倍，可以减少总回撤率
            if(profitStage >= (self.setRisk.stopProfit) * 3):
                self.stopProfit_Retreat = self.setRisk.stopProfit_Retreat * 3
            elif(profitStage >= (self.setRisk.stopProfit) * 2):
                self.stopProfit_Retreat = self.setRisk.stopProfit_Retreat * 2
            pass
      
        #最大回撤限制
        self.stopProfit_Retreat = myData.iif(self.stopProfit_Retreat > 0.06, 0.06, self.stopProfit_Retreat)
        return self.stopProfit_Retreat

    #设置止盈止损状态   
    def setState(self, isStopProfit):
        if(self.setRisk.stockPosition >= 0):
            self.isStop_Profit = isStopProfit
            self.isStop_Loss = not isStopProfit


# 自定义简易库表操作-股票风险设置记录 
class myDataDB_StockTradeRisk(myData_DB.myData_Table):
    def __init__(self, nameDB = "zxcDB_StockTradeRisk", dir = ""):  
        #初始根目录信息
        if(dir == ""):
            strDir, strName = myIO.getPath_ByFile(__file__)
            self.Dir_Base = os.path.abspath(os.path.join(strDir, "../../.."))  
            self.Dir_DataDB = self.Dir_Base + "/Data/DB_Risks/"
            myIO.mkdir(self.Dir_DataDB, False) 
        super().__init__(nameDB, self.Dir_DataDB, True) 
        
    # 检查是否已经存在   
    def _Check(self, rowInfo, updata = False): 
        #修正数据类型 
        if(rowInfo.get('操作日志', "") == ""):
            psetRisk = mySet_StockTradeRisk()
            psetRisk.Trans_FromDict(rowInfo)

            #调用基类更新
            psetRisk.Trans_ToDict(rowInfo)
        return super()._Check(rowInfo, updata)
    #单条有效修正
    def _Check_oneValid(self, rowInfo): 
        if(rowInfo.get('用户名', '') != ""):
            datas = self.Query("用户名== " + rowInfo['用户名'] + " && 标的编号==" + rowInfo['标的编号'])
            for x in datas:
                datas[x]['isDel'] = True
        return True
    # 检查是否相同--继承需重写  
    def _IsSame(self, rowInfo, rowInfo_Base): 
        if(super()._IsSame(rowInfo, rowInfo_Base)): return True

        # 必须ID相同、是否删除相同
        if(rowInfo['ID'] > 0):
            if(rowInfo['ID'] != rowInfo_Base['ID']): return False
        if(rowInfo['isDel'] != rowInfo_Base['isDel']): return False
        if(rowInfo['用户名'] == rowInfo_Base['用户名']):
            if(rowInfo['标的编号'] == rowInfo_Base['标的编号']):
                if (rowInfo['日期'] - rowInfo_Base['日期']).days < 1024:
                    return True
        return False
            
    # 更新
    def _Updata(self, x, rowInfo, bSave = False, bCheck = True): 
        #参数设置更新
        if(bCheck == True):
            psetRisk = mySet_StockTradeRisk(self.rows[x])
            psetRisk.Trans_FromDict(rowInfo)
            psetRisk.Trans_ToDict(rowInfo)

        #调用基类更新
        super()._Updata(x, rowInfo, bSave)
    
    # 提取设置集
    def getSets(self, setDB = None): 
        # 查询数据
        if(setDB == None):
            setDB = gol._Get_Value('zxcDB_StockTradeRisk')
        dictSet = setDB.Query("isDel==False" , "", True)
        return dictSet
    # 提取设置，指定用户名、股票编号
    def getSet(self, usrNmae, stockID, isDel = False, setDB = None): 
        # 组装查询条件
        strFilter = F"isDel=={str(isDel)} && 用户名=={usrNmae} && 标的编号=={stockID}" 

        # 查询数据
        if(setDB == None):
            setDB = gol._Get_Value('zxcDB_StockTradeRisk')
        dictSet = setDB.Query(strFilter, "", True)

        # 提取及返回
        lstSet = list(dictSet.values())
        if(len(lstSet) == 1):
            return lstSet[0]
        return None
    # 提取交易风险对象，指定用户名、股票编号
    def getTradeRisk(self, usrNmae, stockID, avg5 = True, avg10 = False, avg20 = False, end_date=None): 
        # 提取设置
        setDB = gol._Get_Value('zxcDB_StockTradeRisk')
        dictSet = self.getSet(usrNmae, stockID, False, setDB)
        if(dictSet == None): return None
        
        #获取均值
        nTimes = myData.iif(dictSet['标的名称'].count('50ETF') == 1, 10000, 1)
        stockSource = gol._Get_Value('quoteSource_API_JqData', None)
        avgs = [0, 0, -1, -1, -1, -1]
        if(avg5):
            avg5s = stockSource.getPrice_avg_day(stockID, 5, False, end_date)
            avgs[0] = avg5s['high'] * nTimes
            avgs[1] = avg5s['low'] * nTimes
        if(avg10):
            avg10s = stockSource.getPrice_avg_day(stockID, 10, False, end_date)
            avgs[2] = avg10s['high'] * nTimes
            avgs[3] = avg10s['low'] * nTimes
        if(avg20):
            avg20s = stockSource.getPrice_avg_day(stockID, 10, False, end_date)
            avgs[4] = avg20s['high'] * nTimes
            avgs[5] = avg20s['low'] * nTimes

        # 初始风险监测对象
        pSet = mySet_StockTradeRisk(dictSet)
        if(nTimes == 10000):    # 修正期权默认设置
            pSet.stopProfit = 0.10          #止盈线，默认为6%
            pSet.stopLoss = 0.06            #止损线，默认为-2%  
            pSet.stopProfit_Retreat = 0.03  #止盈回撤，默认为1%, 超过止盈线以上则为2倍
            pSet.stopLoss_Retreat = 0.02    #止损回撤，默认为1%
        pRisk = myMonitor_TradeRisk(avgs[0], avgs[1], avgs[2], avgs[3], avgs[4], avgs[5])
        pRisk.initSet(pSet, setDB)
        pRisk.saveSet()
        return pRisk

# 风险控制操作类 
class myRisk_Control():
    def __init__(self):   
        self.riskDB = gol._Get_Value('zxcDB_StockTradeRisk')
        self.stockSet = gol._Get_Value('setsStock')
        self.msgManger = gol._Get_Setting('manageMsgs')
        self.initRiskSets()
    # 初始风控设置集
    def initRiskSets(self):  
        pSets = self.riskDB.getSets(self.riskDB )
        self.dictRisk = {}
        for x in pSets:
            pSet = pSets[x]
            pRisk = self.initRiskSet(pSet['用户名'], pSet['标的编号'], pSet['标的名称'], False)

            #缓存
            dictRisk = self.dictRisk.get(pSet['标的编号'], {})
            dictRisk[pSet['用户名']] = pRisk
            if(len(dictRisk) == 1):
                self.dictRisk[pSet['标的编号']] = dictRisk
        
    # 初始风控设置
    def initRiskSet(self, usrID, stockID, stockName, bCheck = True):  
        #解析正确股票信息
        if(bCheck == True):
            stocks = self.stockSet._Find(stockID, stockName, "****")
            if(len(stocks) == 1):
                pStock = stocks[0]
                stockID = pStock.code_id + "." + pStock.extype2
                stockName = pStock.code_name

        #提取风险对象
        pRisk = self.riskDB.getTradeRisk(usrID, stockID, True)
        return pRisk
        
    # 提取风控对象
    def getRiskSet(self, usrID, stockID, stockName, bCheck = True):  
        #解析正确股票信息
        if(bCheck):
            stocks = self.stockSet._Find(stockID, stockName, "****")
            if(len(stocks) == 1):
                pStock = stocks[0]
                stockID = pStock.code_id + "." + pStock.extype2
                stockName = pStock.code_name

        #提取
        dictRisk = self.dictRisk.get(stockID, None)
        if(dictRisk == None): return None
        return dictRisk.get(usrID, None)

    # 添加设置
    def addRiskSet(self, usrID, stockID, stockName, stockPrice, stockNum, time = "", dictSet = {}):  
        dictSet['用户名'] = usrID
        
        #解析正确股票信息
        if(True):
            stocks = self.stockSet._Find(stockID, stockName, "****")
            if(len(stocks) == 1):
                pStock = stocks[0]
                stockID = pStock.code_id + "." + pStock.extype2
                stockName = pStock.code_name

        dictSet['标的编号'] = stockID
        dictSet['标的名称'] = stockName
        dictSet['标的均价'] = stockPrice
        dictSet['标的数量'] = stockNum
        dictSet['日期'] = myData.iif(time != "", time, myData_Trans.Tran_ToDatetime_str(None, "%Y-%m-%d %H:%M:%S"))

        #添加
        strR = self.riskDB.Add_Row(dictSet, True)
        myDebug.Debug(strR)
        
    #通知接收新行情
    def notifyRisk(self, price, stockID, stockName, bSave_Auto = True):
        #提取设置字典
        dictRisk = self.dictRisk.get(stockID, None)
        if(dictRisk != None):
            for x in dictRisk:
                pRisk = dictRisk[x]
                strR = pRisk.notifyQuotation(price, bSave_Auto)

                #发送消息
                if(strR != ""):
                    msg = self.msgManger.OnCreatMsg()
                    msg["usrName"] = "@*股票风控监测群"
                    msg["msgType"] = "TEXT"
                    msg["usrPlat"] = "wx"
                    msg["msg"] = strR
                    self.msgManger.OnHandleMsg(msg, '', True)   #必须check



#初始全局消息管理器
from myGlobal import gol 
gol._Init()     #先必须在主模块初始化（只在Main模块需要一次即可）
gol._Set_Value('zxcDB_StockTradeRisk', myDataDB_StockTradeRisk())     #实例 股票收益库对象 
gol._Get_Value('zxcDB_StockTradeRisk').Add_Fields(['用户名', '标的编号', '标的名称', '标的均价', '标的数量', "标的仓位", "手续费率", '止盈线', '动态止盈', '止盈回撤', '止盈比例', '止损线', '动态止损', '止损回撤', '止盈比例', '最高价格', '成本价格', '当前价格', '卖出均价','阶段浮盈','当前浮盈','止盈状态', '日期', '备注', '操作日志'], ['string','string','string','float','int','float','float','float','bool','float','float','float','bool','float','float','float','float','float','float','float','float','bool','datetime','string','list'], [])
gol._Set_Value('zxcRisk_Control', myRisk_Control())                   #实例 风险控制操作类 


"""
交易策略：
1.前20/10/5日高点取最高，日内高点，回撤起始1%建议平仓 20%，回撤2%建议平仓 20%，回撤3%建议平仓 20%，回撤4%建议平仓 20%，回撤5%建议平仓 20%
2.建议需要记录，便于分阶段处理。
3.止盈规则：
	达到指定涨幅时（默认6%），触发交易止盈/动态止盈。
	动态止盈：
		按回撤比例分阶段分步卖出，从当前最高点回撤1%时第一次触发，之后每回撤1%触发一次，连续回撤5%时全部卖出。
		当涨幅回升，突破新高时，初始回撤触发状态，即从高点再次回撤1%时触发，直到卖出完毕。
			突破新高规则：涨幅突破前一阶段止盈点，涨幅突破止盈涨幅线，涨幅突破10/5日高点。突破后实时比对更新新高。
			
	关键点：止盈线、10/5日高点、回撤后实时新高

3.止损规则：
	达到指定跌幅时（默认-2%），触发交易止损/动态止损。
	动态止损：
		按跌幅比例分阶段分步卖出，从当前止损线跌1%时第一次触发，之后每跌1%触发一次，连续跌5%时全部卖出。
		当涨幅回升，突破新高时，初始止损触发状态，即从高点再次回撤1%时触发，直到卖出完毕。
			突破新高规则：涨幅突破前一阶段止损点，涨幅突破止损线。突破后实时比对更新新高。
"""


#主启动程序
if __name__ == "__main__":
    #测试库表操作
    pDB = gol._Get_Value('zxcDB_StockTradeRisk')
    pRisk = gol._Get_Value('zxcRisk_Control')
    
    # 添加买入及测试信息 sz,002547,春兴精工,CXJG,stock,CN,深圳证券交易所,XSHE
    pRisk.addRiskSet('茶叶一主号','002547',"", 8, 10000, '2019-08-27 11:11:00', {}) 
    pRisk.addRiskSet('茶叶一主号','300033',"", 96.943, 700, '2019-08-27 11:11:00', {}) 
    pRisk.addRiskSet('茶叶一主号','10001965.XSHG',"50ETF购11月3000", 550.25, 8, '2019-10-23 09:31:00', {}) 
    pRisk.addRiskSet('茶叶一主号','10001966.XSHG',"50ETF购11月3100", 226, 7, '2019-10-23 09:31:00', {}) 



    # 添加行数据
    if(1==2):
        print(pDB.Add_Row({'用户名': '茶叶一主号', '标的编号': '600001', '标的名称': "测试股票", '标的均价': '10.3', '标的数量': 5000, '止盈线': 0.08, '日期': '2019-08-27 11:11:00'}, True))
        print(pDB.Add_Row({'用户名': '茶叶一主号', '标的编号': '600001', '标的名称': "测试股票", '标的均价': '9.7', '标的数量': 5000, '日期': '2019-08-27 11:12:00'}, True))
    
        # 查询数据
        dictSet = pDB.Query("isDel==False && 用户名==茶叶一主号 && 标的编号==600001", "", True)
        pSet = mySet_StockTradeRisk(list(dictSet.values())[0])


        # 风险监测测试
        pRisk = myMonitor_TradeRisk(9.5, 10.8)
        pRisk.initSet(pSet, pDB)
        pRisk.notifyQuotation(12)     
        pRisk.notifyQuotation(11.7)     #回撤 
        pRisk.notifyQuotation(12.7)      
        pRisk.notifyQuotation(13.3)      
        pRisk.notifyQuotation(10.4)     #回撤
        pRisk.notifyQuotation(10.6)
        pRisk.notifyQuotation(10.7)     
        pRisk.notifyQuotation(10.9)     #阶段反弹新高，需细分处理反弹
        pRisk.notifyQuotation(10.8)     #回撤
        pRisk.notifyQuotation(10.75)     
        pRisk.notifyQuotation(10.8)     
        pRisk.notifyQuotation(10.7)     #回撤
        pRisk.notifyQuotation(10.6, False)
        pRisk.notifyQuotation(10.55, False)
        pRisk.notifyQuotation(10.5, False)
        pRisk.notifyQuotation(10.8)     
        pRisk.notifyQuotation(10.7)     #回撤
        pRisk.notifyQuotation(10.6)      
        pRisk.notifyQuotation(10.4)     
        pRisk.notifyQuotation(10.3)     

    # 期权交易测试
    pSource = gol._Get_Value('quoteSource_API_JqData', None)
    if(1 == 2):
        print("当天3000的期权信息：")
        pSource = gol._Get_Value('quoteSource_API_JqData', None)
        sources = pSource.getPrice(security='10001945.XSHG',frequency='1m',start_date='2019-10-14 09:30:00',end_date='2019-10-14 15:00:00')
    
        # 添加买入及测试信息
        print(pDB.Add_Row({'用户名': '茶叶一主号', '标的编号': '10001945.XSHG', '标的名称': "50ETF购10月3000", '标的均价': '650', '标的数量': 10, '日期': '2019-10-14 09:31:00'}, True))
    
        pRisk = pDB.getTradeRisk('茶叶一主号', '10001945.XSHG', True)
        for x in range(0, len(sources)):
             pRisk.notifyQuotation(sources['high'][x] * 10000)    

        print()
        
    # 期权交易测试-实时模拟
    if(1 == 2):
        #初始风险对象
        pRisk_300033 = pRisk.getRiskSet('茶叶一主号', '300033', "", True)
        pRisk_3000 = pRisk.getRiskSet('茶叶一主号', '10001965.XSHG', "", True)
        pRisk_3100 = pRisk.getRiskSet('茶叶一主号', '10001966.XSHG', "", True)

        #消息初始 
        pMMsg = gol._Get_Setting('manageMsgs')
        msg = pMMsg.OnCreatMsg()
        msg["usrName"] = "@*股票风控监测群"
        msg["msgType"] = "TEXT"
        msg["usrPlat"] = "wx"

        #循环
        dtTime = myData_Trans.Tran_ToDatetime("2019-10-23 09:30:00", "%Y-%m-%d %H:%M:%S")
        num = 1
        while(True):
            #时间参数
            dtTime += datetime.timedelta(minutes=1)
            dtNow = myData_Trans.Tran_ToDatetime_str(dtTime, "%Y-%m-%d %H:%M")
            dtStart = myData_Trans.Tran_ToDatetime(dtNow + ":00", "%Y-%m-%d %H:%M:%S")
            dtNext = myData_Trans.Tran_ToDatetime(dtNow + ":59", "%Y-%m-%d %H:%M:%S")
        
            #提取当前期权价格
            sources_300033 = pSource.getPrice(security='300033.XSHE',frequency='1m',start_date=dtStart,end_date=dtNext)
            sources_3000 = pSource.getPrice(security='10001965.XSHG',frequency='1m',start_date=dtStart,end_date=dtNext)
            sources_3100 = pSource.getPrice(security='10001966.XSHG',frequency='1m',start_date=dtStart,end_date=dtNext)
            if(len(sources_3100) < 1): continue
            
            priceAvg_300033 = sources_300033['money'][0] / sources_300033['volume'][0]
            priceAvg_3000 = sources_3000['money'][0] / sources_3000['volume'][0]
            priceAvg_3100 = sources_3100['money'][0] / sources_3100['volume'][0]
            print(priceAvg_300033, priceAvg_3000, priceAvg_3100, "---", dtStart)

            #风险调用
            bSave = myData.iif(num % 5 == 0, True, False)
            pRisk.notifyRisk(priceAvg_300033, '300033.XSHE', "", bSave)
            pRisk.notifyRisk(priceAvg_3000, '10001965.XSHG', "", bSave)
            pRisk.notifyRisk(priceAvg_3100, '10001966.XSHG', "", bSave)

            #延时5秒     
            time.sleep(2)
        

    #需要调整盈利对比，实际利润变动，不可靠
    print()



#开发内容：
#   1.增加风险控制交易，可以简化为按标识识别，非真实交易，真实交易需同步（非必需）。
