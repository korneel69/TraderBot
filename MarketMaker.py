# First iteration only with no lending spot

# Cast orders to liquidate position faster
# For each build position: sell spot at x% higher and buy future at y% lower than current price.

# Requirements:
# - Present position
# - bid prices of futures
# - ask prices of spots
# - When the pairTrader spots an opportunity, it should still be able to act to it


# Solution:
# - Get balance spot
# - Make sure the spot balance is higher than the maximumTradeValue of PairTrader, to make sure pairTrader can make a trade when it wants
# - Get ask price of spot
# - If the balance of spot is higher than 0, then cast sell orders
# --- Given a certain ask price of the spot, cast order at x% higher
#
# - Each cycle
# --- When the price changes, update the orderprice accordingly (does not count for FTX order limit per minute)
# --- When the balance changes to below the maximumTradeValue of PairTrader, cancel the order
# 


# Remarks:
# - available balance cash or spot impacted when casting orders?
# --- If this is the case, then we might not be able to build or liquidate our positions like we did without order casting
# --- Yes, there is an impact on available balance. This does have an impact on the free collateral field!
# ------ What are the implications of lower free collateral? 
#
#
# - Websocket price feed needs to be trustworthy!
#
# - When an order that is cast is filled, the balancingFunction will kick in to correct the position 

from FTXclient import *
from Orders import *
import threading
from Config import *
from PairTrader import *
import pandas

def calculateMidPrice(self):
    self.midPrice=(self.spot_bid+self.future_ask)/2

def calculateOrderPrice(self):
    self.futureOrder=self.midPrice*(1+self.ratioBidWeight-1)
    self.spotOrder=self.midPrice*(1+self.ratioAskWeight-1)

# Sell at a worse price, for better excecution
def discountedPriceOrderCasting(self, price):
    multiplier=1/self.price_increment
    if self.price_increment<0:
        count=len(str(self.price_increment).split('.')[0])
        p=round(multiplier*price/Premium,count)/multiplier
    else:
        count=0
        p=round(multiplier*price/Premium,count)/multiplier
    return p

# Buy at a worse price, for better excecution
def premiumPriceOrderCasting(self, price):
    multiplier=1/self.price_increment
    if self.price_increment<0:
        count=len(str(self.price_increment).split('.')[0])
        p=round(multiplier*price*Premium,count)/multiplier
    else:
        count=0
        p=round(multiplier*price*Premium,count)/multiplier
    return p

def castOrders(self):
    size=self.increment
    try:
        order1=threading.Thread(target=client.place_order, args=(self._future,'sell',premiumPriceOrderCasting(self, price=self.futureOrder), size,'limit',False, False))
        order1.start()
        time.sleep(0.22)
        order2=threading.Thread(target=client.place_order, args=(self.spot_name,'buy',discountedPriceOrderCasting(self, price=self.spotOrder), size,'limit',False, False))
        order2.start()
        order1.join()
        order2.join()
    except Exception as e:
        print(e)
        print(self._future,'Position building failed')
    print('Building',self._future,'| balance future vs spot: ',self._futureBalance,self._spotBalance,'| ratioBid: ' ,self.ratioBid,'| order size vs max size:' ,size,'/' ,sizeMAX,'| order price future vs spot ',  self.discountedPrice(price=self.future_bid), self.premiumPrice(price=self.spot_ask),'| Excecution time: ',t1-t0)
    return True

def checkForOrder(market):
    result=client.get_open_orders(market=market)
    return result

def checkOpenOrders(self):
    self.futureOpenOrders=pandas.DataFrame(checkForOrder(self._future))
    self.spotOpenOrders=pandas.DataFrame(checkForOrder(self.spot_name))
    
def determineActions(self,df,future):
    try:
        if df.empty==True:
            print('place order')
            castOrders(self)
        elif df.count()['id'] > 1:
            client.cancel_order(df['id'][df.index[-1]]) 
        elif df.count()['id']==1:
            orderId=df['id'][0]
            modifyOrder(self,orderId,future)   
        time.sleep(0.001)
    except Exception as e:
        print(e)

        

def modifyOrder(self, orderId, future):
    if future == True:
        client.modify_order(existing_order_id=orderId,price=premiumPriceOrderCasting(self,price=self.midPrice))
    elif future == False:
        client.modify_order(existing_order_id=orderId,price=discountedPriceOrderCasting(self,price=self.midPrice))

def marketMakeing(self):
    calculateMidPrice(self)
    calculateOrderPrice(self)
    checkOpenOrders(self)
    self.web_socket_ready()
    self.calculate_potential()
    determineActions(self,self.futureOpenOrders, future=True)
    determineActions(self,self.spotOpenOrders, future=False)
    #print('openfuture', self._future,self.futureOpenOrders)
    #print('openspot',self.spot_name,self.spotOpenOrders)













    

