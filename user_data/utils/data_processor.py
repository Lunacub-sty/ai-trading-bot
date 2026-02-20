# 数据获取与处理模块
# 用于处理加密货币交易数据的下载、预处理和存储

import os
import pandas as pd
import numpy as np
import ccxt
from freqtrade.configuration import Configuration
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    数据处理器类
    用于下载、处理和存储加密货币交易数据
    """
    
    def __init__(self, config_path: str = 'user_data/config.json'):
        """
        初始化数据处理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = Configuration.from_files([config_path])
        self.data_dir = self.config.get('datadir', 'user_data/data')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"数据处理器初始化完成，数据目录: {self.data_dir}")
    
    def download_history_data(self, pairs: list, timeframe: str, days: int = 30):
        """
        下载历史数据
        
        Args:
            pairs: 交易对列表
            timeframe: 时间周期
            days: 下载天数
        """
        try:
            logger.info(f"开始下载历史数据: {pairs}, {timeframe}, {days}天")
            
            # 初始化交易所
            exchange = ccxt.okx()
            
            # 计算开始时间戳
            end_timestamp = exchange.milliseconds()
            start_timestamp = end_timestamp - (days * 24 * 60 * 60 * 1000)
            
            # 下载每个交易对的数据
            for pair in pairs:
                try:
                    logger.info(f"下载 {pair} 的历史数据")
                    
                    # 分批获取数据
                    all_ohlcv = []
                    current_timestamp = start_timestamp
                    
                    while current_timestamp < end_timestamp:
                        # 获取数据
                        ohlcv = exchange.fetch_ohlcv(
                            pair,
                            timeframe,
                            since=current_timestamp,
                            limit=1000
                        )
                        
                        if not ohlcv:
                            break
                        
                        all_ohlcv.extend(ohlcv)
                        current_timestamp = ohlcv[-1][0] + exchange.parse_timeframe(timeframe) * 1000
                        
                        # 避免API限制
                        exchange.sleep(1000)
                    
                    # 转换为DataFrame
                    if all_ohlcv:
                        df = pd.DataFrame(
                            all_ohlcv, 
                            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        )
                        
                        # 保存数据
                        filename = f"{pair.replace('/', '_')}_{timeframe}.json"
                        filepath = os.path.join(self.data_dir, filename)
                        df.to_json(filepath, orient='records')
                        
                        logger.info(f"成功保存 {pair} 的历史数据: {len(df)}行")
                    
                except Exception as e:
                    logger.error(f"下载 {pair} 的数据失败: {e}")
                    continue
            
            logger.info("历史数据下载完成")
        except Exception as e:
            logger.error(f"下载历史数据失败: {e}")
    
    def load_data(self, pair: str, timeframe: str) -> pd.DataFrame:
        """
        加载历史数据
        
        Args:
            pair: 交易对
            timeframe: 时间周期
        
        Returns:
            数据帧
        """
        try:
            # 构建文件路径
            filename = f"{pair.replace('/', '_')}_{timeframe}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                data = pd.read_json(filepath)
                logger.info(f"成功加载数据: {filepath}, 数据量: {len(data)}行")
                return data
            else:
                logger.warning(f"数据文件不存在: {filepath}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return pd.DataFrame()
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        预处理数据
        
        Args:
            data: 原始数据
        
        Returns:
            预处理后的数据
        """
        try:
            if data.empty:
                return data
            
            # 确保时间列是datetime类型
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'], unit='ms')
                data.set_index('date', inplace=True)
            elif 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
                data.set_index('timestamp', inplace=True)
            
            # 排序数据
            data.sort_index(inplace=True)
            
            # 移除重复值
            data = data[~data.index.duplicated(keep='first')]
            
            # 填充缺失值
            data = data.fillna(method='ffill').fillna(method='bfill')
            
            # 计算收益率
            data['returns'] = data['close'].pct_change()
            
            logger.info(f"数据预处理完成，处理后数据量: {len(data)}行")
            return data
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return data
    
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成特征
        
        Args:
            data: 预处理后的数据
        
        Returns:
            带有特征的数据
        """
        try:
            if data.empty:
                return data
            
            # 基本特征
            data['volume_change'] = data['volume'].pct_change()
            data['high_low_range'] = (data['high'] - data['low']) / data['close']
            data['open_close_change'] = (data['close'] - data['open']) / data['open']
            
            # 移动平均线
            data['ma5'] = data['close'].rolling(window=5).mean()
            data['ma10'] = data['close'].rolling(window=10).mean()
            data['ma20'] = data['close'].rolling(window=20).mean()
            
            # 移动平均线差异
            data['ma5_ma10_diff'] = (data['ma5'] - data['ma10']) / data['ma10']
            data['ma10_ma20_diff'] = (data['ma10'] - data['ma20']) / data['ma20']
            
            # 波动率
            data['volatility_5'] = data['returns'].rolling(window=5).std()
            data['volatility_10'] = data['returns'].rolling(window=10).std()
            
            # 移除NaN值
            data = data.dropna()
            
            logger.info(f"特征生成完成，生成后数据量: {len(data)}行")
            return data
        except Exception as e:
            logger.error(f"特征生成失败: {e}")
            return data
    
    def save_processed_data(self, data: pd.DataFrame, pair: str, timeframe: str):
        """
        保存处理后的数据
        
        Args:
            data: 处理后的数据
            pair: 交易对
            timeframe: 时间周期
        """
        try:
            if data.empty:
                logger.warning("空数据，跳过保存")
                return
            
            # 构建文件路径
            processed_dir = os.path.join(self.data_dir, 'processed')
            os.makedirs(processed_dir, exist_ok=True)
            
            filename = f"{pair.replace('/', '_')}_{timeframe}_processed.json"
            filepath = os.path.join(processed_dir, filename)
            
            # 保存数据
            data.to_json(filepath)
            logger.info(f"处理后的数据已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存处理后的数据失败: {e}")
    
    def get_data_for_strategy(self, pair: str, timeframe: str) -> pd.DataFrame:
        """
        获取策略所需的数据
        
        Args:
            pair: 交易对
            timeframe: 时间周期
        
        Returns:
            策略所需的数据
        """
        try:
            # 加载数据
            data = self.load_data(pair, timeframe)
            
            if data.empty:
                # 如果数据不存在，尝试下载
                logger.info(f"数据不存在，尝试下载: {pair}")
                self.download_history_data([pair], timeframe, days=10)
                data = self.load_data(pair, timeframe)
            
            # 预处理数据
            data = self.preprocess_data(data)
            
            # 生成特征
            data = self.generate_features(data)
            
            # 保存处理后的数据
            self.save_processed_data(data, pair, timeframe)
            
            return data
        except Exception as e:
            logger.error(f"获取策略数据失败: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    """
    测试数据处理器
    """
    # 初始化数据处理器
    processor = DataProcessor()
    
    # 测试下载数据
    pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    processor.download_history_data(pairs, "5m", days=7)
    
    # 测试数据处理
    for pair in pairs:
        data = processor.get_data_for_strategy(pair, "5m")
        print(f"{pair} 数据处理结果: {len(data)}行")
        print(data.head())
