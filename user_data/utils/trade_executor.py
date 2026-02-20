# 交易执行系统
# 用于管理订单执行、风险管理和交易监控

import logging
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
from freqtrade.exchange import Exchange
from freqtrade.strategy import IStrategy
import numpy as np
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    交易执行器类
    用于管理订单执行、风险管理和交易监控
    """
    
    def __init__(self, exchange: Exchange, strategy: IStrategy):
        """
        初始化交易执行器
        
        Args:
            exchange: 交易所对象
            strategy: 策略对象
        """
        self.exchange = exchange
        self.strategy = strategy
        self.max_open_trades = strategy.config.get('max_open_trades', 3)
        self.stoploss = strategy.config.get('stoploss', -0.03)
        self.trading_mode = strategy.config.get('trading_mode', 'spot')
        self.margin_mode = strategy.config.get('margin_mode', 'isolated')
        
        # 风险管理参数
        self.risk_per_trade = 0.02  # 每笔交易风险控制在2%
        self.max_position_size = 0.3  # 单个持仓最大占比30%
        self.cooldown_period = 60  # 交易冷却期（秒）
        
        # 交易状态
        self.last_trade_time = datetime.now() - timedelta(seconds=self.cooldown_period)
        
        logger.info("交易执行器初始化完成")
    
    def check_risk_management(self, pair: str, amount: float, price: float) -> bool:
        """
        检查风险管理
        
        Args:
            pair: 交易对
            amount: 交易数量
            price: 交易价格
        
        Returns:
            是否通过风险检查
        """
        try:
            # 检查冷却期
            if (datetime.now() - self.last_trade_time).total_seconds() < self.cooldown_period:
                logger.warning(f"交易冷却期未结束，跳过交易: {pair}")
                return False
            
            # 检查最大开仓数量
            open_trades = Trade.get_open_trades_count()
            if open_trades >= self.max_open_trades:
                logger.warning(f"已达到最大开仓数量: {open_trades}/{self.max_open_trades}")
                return False
            
            # 计算交易价值
            trade_value = amount * price
            
            # 检查账户余额
            balance = self.exchange.get_balance()
            stake_currency = self.strategy.config.get('stake_currency', 'USDT')
            available_balance = balance.get(stake_currency, {}).get('available', 0)
            
            if trade_value > available_balance:
                logger.warning(f"余额不足，可用余额: {available_balance}, 交易需要: {trade_value}")
                return False
            
            # 检查单个持仓最大占比
            total_balance = balance.get(stake_currency, {}).get('total', 0)
            if total_balance > 0 and trade_value > total_balance * self.max_position_size:
                logger.warning(f"持仓过大，单个持仓最大占比: {self.max_position_size * 100}%")
                return False
            
            # 检查每笔交易风险
            risk_amount = trade_value * abs(self.stoploss)
            if risk_amount > total_balance * self.risk_per_trade:
                logger.warning(f"风险过大，每笔交易风险控制: {self.risk_per_trade * 100}%")
                return False
            
            return True
        except Exception as e:
            logger.error(f"风险管理检查失败: {e}")
            return False
    
    def execute_entry_order(self, pair: str, amount: float, price: float) -> dict:
        """
        执行入场订单
        
        Args:
            pair: 交易对
            amount: 交易数量
            price: 交易价格
        
        Returns:
            订单信息
        """
        try:
            # 检查风险管理
            if not self.check_risk_management(pair, amount, price):
                return {"success": False, "message": "风险管理检查失败"}
            
            # 执行订单
            if self.trading_mode == 'futures':
                # 期货交易
                order = self.exchange.create_order(
                    pair=pair,
                    side='buy',
                    ordertype='market',
                    amount=amount,
                    price=price,
                    leverage=self.strategy.config.get('leverage', 1),
                    reduce_only=False
                )
            else:
                # 现货交易
                order = self.exchange.create_order(
                    pair=pair,
                    side='buy',
                    ordertype='market',
                    amount=amount,
                    price=price
                )
            
            # 更新最后交易时间
            self.last_trade_time = datetime.now()
            
            logger.info(f"入场订单执行成功: {pair}, 数量: {amount}, 价格: {price}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"入场订单执行失败: {e}")
            return {"success": False, "message": str(e)}
    
    def execute_exit_order(self, trade: Trade) -> dict:
        """
        执行出场订单
        
        Args:
            trade: 交易对象
        
        Returns:
            订单信息
        """
        try:
            # 执行订单
            if self.trading_mode == 'futures':
                # 期货交易
                order = self.exchange.create_order(
                    pair=trade.pair,
                    side='sell',
                    ordertype='market',
                    amount=trade.stake_amount,
                    price=trade.close_rate or self.exchange.get_ticker(trade.pair)['last'],
                    leverage=self.strategy.config.get('leverage', 1),
                    reduce_only=True
                )
            else:
                # 现货交易
                order = self.exchange.create_order(
                    pair=trade.pair,
                    side='sell',
                    ordertype='market',
                    amount=trade.stake_amount,
                    price=trade.close_rate or self.exchange.get_ticker(trade.pair)['last']
                )
            
            logger.info(f"出场订单执行成功: {trade.pair}, 数量: {trade.stake_amount}")
            return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"出场订单执行失败: {e}")
            return {"success": False, "message": str(e)}
    
    def check_stoploss(self, trade: Trade) -> bool:
        """
        检查止损
        
        Args:
            trade: 交易对象
        
        Returns:
            是否触发止损
        """
        try:
            # 获取当前价格
            ticker = self.exchange.get_ticker(trade.pair)
            current_price = ticker['last']
            
            # 计算收益率
            if trade.open_rate:
                return_rate = (current_price - trade.open_rate) / trade.open_rate
                
                # 检查止损
                if return_rate <= self.stoploss:
                    logger.info(f"触发止损: {trade.pair}, 当前收益率: {return_rate * 100:.2f}%")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查止损失败: {e}")
            return False
    
    def manage_open_trades(self):
        """
        管理未平仓交易
        """
        try:
            open_trades = Trade.get_open_trades()
            
            for trade in open_trades:
                # 检查止损
                if self.check_stoploss(trade):
                    result = self.execute_exit_order(trade)
                    if result['success']:
                        logger.info(f"止损执行成功: {trade.pair}")
                    
                # 检查其他出场条件
                # 这里可以添加更多出场条件，比如止盈、时间条件等
                
        except Exception as e:
            logger.error(f"管理未平仓交易失败: {e}")
    
    def get_trade_status(self) -> dict:
        """
        获取交易状态
        
        Returns:
            交易状态
        """
        try:
            # 获取未平仓交易
            open_trades = Trade.get_open_trades()
            open_trades_count = len(open_trades)
            
            # 获取账户余额
            balance = self.exchange.get_balance()
            stake_currency = self.strategy.config.get('stake_currency', 'USDT')
            available_balance = balance.get(stake_currency, {}).get('available', 0)
            total_balance = balance.get(stake_currency, {}).get('total', 0)
            
            # 计算未平仓交易价值
            open_trades_value = 0
            for trade in open_trades:
                if trade.open_rate and trade.stake_amount:
                    open_trades_value += trade.open_rate * trade.stake_amount
            
            # 计算风险指标
            risk_exposure = open_trades_value / total_balance if total_balance > 0 else 0
            
            status = {
                "open_trades_count": open_trades_count,
                "max_open_trades": self.max_open_trades,
                "available_balance": available_balance,
                "total_balance": total_balance,
                "open_trades_value": open_trades_value,
                "risk_exposure": risk_exposure,
                "stoploss": self.stoploss,
                "trading_mode": self.trading_mode,
                "margin_mode": self.margin_mode
            }
            
            logger.info(f"交易状态: {status}")
            return status
        except Exception as e:
            logger.error(f"获取交易状态失败: {e}")
            return {}
    
    def execute_trade(self, pair: str, signal: str, amount: float = None, price: float = None) -> dict:
        """
        执行交易
        
        Args:
            pair: 交易对
            signal: 信号类型 (buy/sell)
            amount: 交易数量
            price: 交易价格
        
        Returns:
            交易结果
        """
        try:
            if signal == 'buy':
                # 执行买入
                if amount is None or price is None:
                    # 如果没有指定数量和价格，使用默认值
                    ticker = self.exchange.get_ticker(pair)
                    price = price or ticker['last']
                    
                    # 计算交易数量
                    stake_amount = self.strategy.config.get('stake_amount', 'unlimited')
                    if stake_amount == 'unlimited':
                        balance = self.exchange.get_balance()
                        stake_currency = self.strategy.config.get('stake_currency', 'USDT')
                        available_balance = balance.get(stake_currency, {}).get('available', 0)
                        amount = available_balance / price * 0.99  # 留1%的缓冲
                    else:
                        amount = float(stake_amount) / price
                
                result = self.execute_entry_order(pair, amount, price)
            
            elif signal == 'sell':
                # 执行卖出
                # 查找该交易对的未平仓交易
                open_trades = Trade.get_open_trades()
                trade_to_close = None
                
                for trade in open_trades:
                    if trade.pair == pair:
                        trade_to_close = trade
                        break
                
                if trade_to_close:
                    result = self.execute_exit_order(trade_to_close)
                else:
                    logger.warning(f"没有找到未平仓交易: {pair}")
                    result = {"success": False, "message": "没有找到未平仓交易"}
            
            else:
                logger.error(f"无效的交易信号: {signal}")
                result = {"success": False, "message": "无效的交易信号"}
            
            return result
        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return {"success": False, "message": str(e)}
