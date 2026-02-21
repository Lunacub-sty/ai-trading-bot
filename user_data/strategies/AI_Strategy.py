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
from sklearn.metrics import accuracy_score, classification_report
import ta
import joblib
import os
from datetime import datetime, timedelta


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
        self.model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42,
            n_jobs=-1,  # 使用所有可用CPU核心
            max_depth=10,  # 限制树深度，防止过拟合
            min_samples_split=5,  # 最小分裂样本数
            min_samples_leaf=2  # 最小叶节点样本数
        )
        self.scaler = StandardScaler()
        self.model_trained = False
        self.last_train_time = None
        self.train_interval = timedelta(hours=6)  # 模型训练间隔
        
        # 模型保存路径
        self.model_dir = os.path.join("user_data", "models")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, "ai_strategy_model.joblib")
        self.scaler_path = os.path.join(self.model_dir, "ai_strategy_scaler.joblib")
        
        # 使用Freqtrade的日志系统
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI Strategy initialized")
        
        # 尝试加载预训练模型
        self.load_model()
    
    def load_model(self):
        """
        加载预训练模型
        """
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.model_trained = True
                self.last_train_time = datetime.now()
                self.logger.info("成功加载预训练模型")
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
    
    def save_model(self):
        """
        保存模型
        """
        try:
            # 检查模型目录大小
            self._check_model_directory_size()
            
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            self.logger.info("模型保存成功")
        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
    
    def _check_model_directory_size(self):
        """
        检查并清理模型目录
        """
        try:
            # 模型目录最大大小（MB）
            max_model_dir_size = 100
            
            # 计算目录大小
            total_size = 0
            for root, dirs, files in os.walk(self.model_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            total_size_mb = total_size / 1024 / 1024
            self.logger.info(f"模型目录大小: {total_size_mb:.2f} MB")
            
            # 如果目录大小超过阈值，删除旧模型文件
            if total_size_mb > max_model_dir_size:
                self.logger.warning(f"模型目录大小超过限制，清理旧文件")
                
                # 获取所有模型文件并按修改时间排序
                model_files = []
                for root, dirs, files in os.walk(self.model_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file.endswith('.joblib'):
                            model_files.append((file_path, os.path.getmtime(file_path)))
                
                # 按修改时间排序
                model_files.sort(key=lambda x: x[1])
                
                # 删除最旧的文件，直到目录大小低于阈值
                while total_size_mb > max_model_dir_size and model_files:
                    oldest_file, _ = model_files.pop(0)
                    file_size = os.path.getsize(oldest_file)
                    os.remove(oldest_file)
                    total_size -= file_size
                    total_size_mb = total_size / 1024 / 1024
                    self.logger.info(f"删除旧模型文件: {oldest_file}")
                    
        except Exception as e:
            self.logger.error(f"检查模型目录大小失败: {e}")
    
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
        
        # 额外技术指标
        dataframe['stoch'] = ta.momentum.stoch(dataframe['high'], dataframe['low'], dataframe['close'])
        dataframe['stoch_signal'] = ta.momentum.stoch_signal(dataframe['high'], dataframe['low'], dataframe['close'])
        dataframe['atr'] = ta.volatility.average_true_range(dataframe['high'], dataframe['low'], dataframe['close'])
        dataframe['adx'] = ta.trend.adx(dataframe['high'], dataframe['low'], dataframe['close'])
        
        # 价格变化
        dataframe['price_change'] = dataframe['close'].pct_change() * 100
        dataframe['volume_change'] = dataframe['volume'].pct_change() * 100
        
        # 特征工程
        dataframe['rsi_overbought'] = (dataframe['rsi'] > 70).astype(int)
        dataframe['rsi_oversold'] = (dataframe['rsi'] < 30).astype(int)
        dataframe['price_above_ma5'] = (dataframe['close'] > dataframe['ma5']).astype(int)
        dataframe['price_above_ma20'] = (dataframe['close'] > dataframe['ma20']).astype(int)
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle'] * 100
        dataframe['ma_diff'] = (dataframe['ma5'] - dataframe['ma20']) / dataframe['ma20'] * 100
        dataframe['stoch_overbought'] = (dataframe['stoch'] > 80).astype(int)
        dataframe['stoch_oversold'] = (dataframe['stoch'] < 20).astype(int)
        
        # 目标变量：预测下一个周期的价格变化方向
        dataframe['target'] = np.where(dataframe['close'].shift(-1) > dataframe['close'], 1, 0)
        
        # 训练模型
        current_time = datetime.now()
        if (len(dataframe) > 100 and not self.model_trained) or \
           (self.last_train_time and (current_time - self.last_train_time) > self.train_interval):
            self.train_model(dataframe)
            self.last_train_time = current_time
        
        # 预测
        if self.model_trained:
            features = self.get_features(dataframe)
            if len(features) > 0:
                # 只预测最后一行，提高性能
                last_features = features[-1:]
                prediction = self.model.predict(last_features)
                dataframe.loc[dataframe.index[-1], 'prediction'] = prediction[0]
                
                # 添加预测概率
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(last_features)
                    dataframe.loc[dataframe.index[-1], 'prediction_prob'] = proba[0][1]
        
        return dataframe
    
    def get_features(self, dataframe: DataFrame) -> np.array:
        """
        获取特征数据
        """
        feature_columns = [
            'rsi', 'macd', 'bb_width', 'price_change', 'volume_change',
            'rsi_overbought', 'rsi_oversold', 'price_above_ma5', 'price_above_ma20',
            'stoch', 'stoch_signal', 'atr', 'adx', 'ma_diff',
            'stoch_overbought', 'stoch_oversold'
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
            # 检查系统资源
            if not self._check_system_resources():
                self.logger.warning("系统资源不足，跳过模型训练")
                return
            
            # 准备训练数据
            feature_columns = [
                'rsi', 'macd', 'bb_width', 'price_change', 'volume_change',
                'rsi_overbought', 'rsi_oversold', 'price_above_ma5', 'price_above_ma20',
                'stoch', 'stoch_signal', 'atr', 'adx', 'ma_diff',
                'stoch_overbought', 'stoch_oversold'
            ]
            
            # 移除NaN值
            train_data = dataframe.dropna(subset=feature_columns + ['target'])
            
            # 限制训练数据量
            max_train_size = 5000  # 最多使用5000条数据，适合2核CPU
            if len(train_data) > max_train_size:
                train_data = train_data.tail(max_train_size)
                self.logger.info(f"训练数据量过大，限制为{max_train_size}条")
            
            if len(train_data) > 100:  # 增加最小训练数据量
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
                
                # 生成详细的分类报告
                report = classification_report(y_test, y_pred, output_dict=True)
                precision = report['1']['precision']
                recall = report['1']['recall']
                f1_score = report['1']['f1-score']
                
                self.model_trained = True
                self.last_train_time = datetime.now()
                
                # 保存模型
                self.save_model()
                
                self.logger.info(f"模型训练完成，准确率: {accuracy:.2f}, 精确率: {precision:.2f}, 召回率: {recall:.2f}, F1分数: {f1_score:.2f}")
        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
    
    def _check_system_resources(self):
        """
        检查系统资源是否充足
        """
        try:
            import psutil
            
            # 检查内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent > 70:
                self.logger.warning(f"内存使用率过高: {memory_percent:.2f}%")
                return False
            
            # 检查CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 70:
                self.logger.warning(f"CPU使用率过高: {cpu_percent:.2f}%")
                return False
            
            # 检查存储使用
            stat = os.statvfs(self.model_dir)
            free_space = stat.f_bavail * stat.f_frsize
            total_space = stat.f_blocks * stat.f_frsize
            storage_percent = (total_space - free_space) / total_space * 100
            if storage_percent > 70:
                self.logger.warning(f"存储使用率过高: {storage_percent:.2f}%")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"检查系统资源失败: {e}")
            return True  # 检查失败时默认允许训练
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        生成入场信号
        """
        # 确保prediction列存在
        if 'prediction' not in dataframe.columns:
            dataframe['prediction'] = 0
        
        # 确保prediction_prob列存在
        if 'prediction_prob' not in dataframe.columns:
            dataframe['prediction_prob'] = 0.5
        
        dataframe.loc[
            (
                (dataframe['prediction'] == 1) &  # 模型预测上涨
                (dataframe['rsi'] < 70) &  # RSI不在超买区域
                (dataframe['volume'] > 0) &  # 有成交量
                (dataframe['price_above_ma5'] == 1) &  # 价格在5日均线之上
                (dataframe['prediction_prob'] > 0.6)  # 预测概率大于60%
            ),
            'enter_long'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        生成退出信号
        """
        # 确保prediction列存在
        if 'prediction' not in dataframe.columns:
            dataframe['prediction'] = 0
        
        dataframe.loc[
            (
                (dataframe['prediction'] == 0) &  # 模型预测下跌
                (dataframe['rsi'] > 30) &  # RSI不在超卖区域
                (dataframe['volume'] > 0)  # 有成交量
            ),
            'exit_long'] = 1
        
        return dataframe
    
    def custom_exit(self, trade: Trade, current_time, current_rate, current_profit, **kwargs):
        """
        自定义退出逻辑
        """
        # 可以在这里添加额外的退出逻辑
        # 例如基于当前市场状况的动态退出策略
        return None
