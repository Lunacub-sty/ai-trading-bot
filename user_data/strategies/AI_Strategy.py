# AI交易策略
# 基于机器学习的加密货币交易策略

from freqtrade.strategy import IStrategy
from freqtrade.persistence import Trade
from freqtrade.strategy import informative
from pandas import DataFrame
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import ta


class AI_Strategy(IStrategy):
    """
    AI交易策略
    基于机器学习的交易策略，使用技术指标作为特征，预测市场走势
    """
    
    # 策略配置
    timeframe = '5m'  # 交易时间周期
    minimal_roi = {
        "0": 0.05,  # 5%的回报率
        "30": 0.02,  # 30分钟后2%的回报率
        "60": 0.01,  # 60分钟后1%的回报率
        "120": 0.005  # 120分钟后0.5%的回报率
    }
    stoploss = -0.03  # 止损设置为3%
    trailing_stop = True  # 启用追踪止损
    trailing_stop_positive = 0.01  # 追踪止损的正偏移
    trailing_stop_positive_offset = 0.02  # 追踪止损的正偏移开始点
    trailing_only_offset_is_reached = True  # 只有达到偏移点才开始追踪
    process_only_new_candles = True  # 只处理新的K线
    use_exit_signal = True  # 使用退出信号
    exit_profit_only = False  # 不仅在盈利时退出
    ignore_roi_if_entry_signal = False  # 不忽略ROI如果有入场信号
    startup_candle_count = 30  # 启动所需的K线数量
    
    def __init__(self, config):
        """
        初始化策略
        """
        super().__init__(config)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.model_trained = False
        # 使用Freqtrade的日志系统
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI Strategy initialized")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        添加技术指标作为特征
        """
        # 基本技术指标
        dataframe['rsi'] = ta.momentum.rsi(dataframe['close'], window=14)
        dataframe['macd'] = ta.trend.macd_diff(dataframe['close'])
        dataframe['bb_upper'] = ta.volatility.bollinger_hband(dataframe['close'])
        dataframe['bb_lower'] = ta.volatility.bollinger_lband(dataframe['close'])
        dataframe['bb_middle'] = ta.volatility.bollinger_mavg(dataframe['close'])
        
        # 移动平均线
        dataframe['ma5'] = ta.trend.sma_indicator(dataframe['close'], window=5)
        dataframe['ma10'] = ta.trend.sma_indicator(dataframe['close'], window=10)
        dataframe['ma20'] = ta.trend.sma_indicator(dataframe['close'], window=20)
        
        # 价格变化
        dataframe['price_change'] = dataframe['close'].pct_change() * 100
        dataframe['volume_change'] = dataframe['volume'].pct_change() * 100
        
        # 特征工程
        dataframe['rsi_overbought'] = (dataframe['rsi'] > 70).astype(int)
        dataframe['rsi_oversold'] = (dataframe['rsi'] < 30).astype(int)
        dataframe['price_above_ma5'] = (dataframe['close'] > dataframe['ma5']).astype(int)
        dataframe['price_above_ma20'] = (dataframe['close'] > dataframe['ma20']).astype(int)
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle'] * 100
        
        # 目标变量：预测下一个周期的价格变化方向
        dataframe['target'] = np.where(dataframe['close'].shift(-1) > dataframe['close'], 1, 0)
        
        # 训练模型
        if len(dataframe) > 100 and not self.model_trained:
            self.train_model(dataframe)
        
        # 预测
        if self.model_trained:
            features = self.get_features(dataframe)
            if len(features) > 0:
                dataframe['prediction'] = self.model.predict(features)
        
        return dataframe
    
    def get_features(self, dataframe: DataFrame) -> np.array:
        """
        获取特征数据
        """
        feature_columns = [
            'rsi', 'macd', 'bb_width', 'price_change', 'volume_change',
            'rsi_overbought', 'rsi_oversold', 'price_above_ma5', 'price_above_ma20'
        ]
        features = dataframe[feature_columns].dropna()
        if len(features) > 0:
            return self.scaler.transform(features)
        return np.array([])
    
    def train_model(self, dataframe: DataFrame) -> None:
        """
        训练机器学习模型
        """
        try:
            # 准备训练数据
            feature_columns = [
                'rsi', 'macd', 'bb_width', 'price_change', 'volume_change',
                'rsi_overbought', 'rsi_oversold', 'price_above_ma5', 'price_above_ma20'
            ]
            
            # 移除NaN值
            train_data = dataframe.dropna(subset=feature_columns + ['target'])
            
            if len(train_data) > 50:
                # 分割特征和目标变量
                X = train_data[feature_columns]
                y = train_data['target']
                
                # 分割训练集和测试集
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # 标准化特征
                self.scaler.fit(X_train)
                X_train_scaled = self.scaler.transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
                
                # 训练模型
                self.model.fit(X_train_scaled, y_train)
                
                # 评估模型
                y_pred = self.model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                self.model_trained = True
                self.logger.info(f"模型训练完成，准确率: {accuracy:.2f}")
        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        生成入场信号
        """
        dataframe.loc[
            (
                (dataframe['prediction'] == 1) &  # 模型预测上涨
                (dataframe['rsi'] < 70) &  # RSI不在超买区域
                (dataframe['volume'] > 0) &  # 有成交量
                (dataframe['price_above_ma5'] == 1)  # 价格在5日均线之上
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        生成退出信号
        """
        dataframe.loc[
            (
                (dataframe['prediction'] == 0) &  # 模型预测下跌
                (dataframe['rsi'] > 30) &  # RSI不在超卖区域
                (dataframe['volume'] > 0)  # 有成交量
            ),
            'exit_long'] = 1
        
        return dataframe
