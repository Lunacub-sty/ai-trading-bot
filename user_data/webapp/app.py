# Web数据可视化界面后端
# 基于FastAPI

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
import asyncio
from functools import lru_cache
import psutil

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI交易机器人",
    description="基于Freqtrade的AI交易策略可视化界面",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="user_data/webapp/static"), name="static")
app.mount("/components", StaticFiles(directory="user_data/webapp/components"), name="components")

# 数据目录
DATA_DIR = "user_data/data"
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs("user_data/webapp/static", exist_ok=True)
os.makedirs("user_data/webapp/templates", exist_ok=True)

# 缓存配置
CACHE_TTL = 300  # 缓存有效期（秒）

# 监控配置
MONITORING_INTERVAL = 3600  # 监控间隔（秒）
MAX_MEMORY_USAGE = 80  # 最大内存使用率（%）
MAX_STORAGE_USAGE = 80  # 最大存储使用率（%）

# 定期监控任务
async def monitoring_task():
    """定期监控系统资源使用情况"""
    while True:
        check_memory_usage()
        check_storage_usage()
        await asyncio.sleep(MONITORING_INTERVAL)

def check_memory_usage():
    """检查内存使用情况"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        logger.info(f"内存使用: {memory_info.rss / 1024 / 1024:.2f} MB, 使用率: {memory_percent:.2f}%")
        
        # 如果内存使用率超过阈值，执行清理
        if memory_percent > MAX_MEMORY_USAGE:
            logger.warning(f"内存使用率过高 ({memory_percent:.2f}%)，执行清理...")
            # 执行清理操作，如清空缓存等
            global cache
            cache.cache.clear()
            logger.info("已清空缓存")
    except Exception as e:
        logger.error(f"检查内存使用情况失败: {e}")

def check_storage_usage():
    """检查存储使用情况"""
    try:
        stat = os.statvfs(DATA_DIR)
        free_space = stat.f_bavail * stat.f_frsize
        total_space = stat.f_blocks * stat.f_frsize
        usage_percent = (total_space - free_space) / total_space * 100
        
        logger.info(f"存储使用: {usage_percent:.2f}%, 可用空间: {free_space / 1024 / 1024 / 1024:.2f} GB")
        
        # 如果存储使用率超过阈值，执行清理
        if usage_percent > MAX_STORAGE_USAGE:
            logger.warning(f"存储使用率过高 ({usage_percent:.2f}%)，执行清理...")
            cleanup_old_data()
    except Exception as e:
        logger.error(f"检查存储使用情况失败: {e}")

def cleanup_old_data():
    """清理旧数据"""
    try:
        # 清理超过30天的历史数据
        cutoff_date = datetime.now() - timedelta(days=30)
        cleaned_files = 0
        
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        cleaned_files += 1
                        logger.info(f"删除旧文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")
        
        logger.info(f"清理完成，删除了{cleaned_files}个旧文件")
    except Exception as e:
        logger.error(f"清理旧数据失败: {e}")

# 模拟交易数据
mock_trades = [
    {
        "id": 1,
        "pair": "BTC/USDT",
        "side": "buy",
        "amount": 0.01,
        "price": 60000,
        "status": "open",
        "open_date": "2026-02-20T10:00:00",
        "current_price": 61000,
        "profit": 100,
        "profit_percent": 1.67
    },
    {
        "id": 2,
        "pair": "ETH/USDT",
        "side": "buy",
        "amount": 0.1,
        "price": 3000,
        "status": "closed",
        "open_date": "2026-02-19T15:00:00",
        "close_date": "2026-02-20T09:00:00",
        "close_price": 3100,
        "profit": 10,
        "profit_percent": 3.33
    },
    {
        "id": 3,
        "pair": "BNB/USDT",
        "side": "buy",
        "amount": 1,
        "price": 300,
        "status": "closed",
        "open_date": "2026-02-18T08:00:00",
        "close_date": "2026-02-19T10:00:00",
        "close_price": 290,
        "profit": -10,
        "profit_percent": -3.33
    }
]

# 模拟账户数据
mock_account = {
    "balance": 1000,
    "total_trades": 3,
    "winning_trades": 2,
    "losing_trades": 1,
    "win_rate": 66.67,
    "total_profit": 100,
    "total_profit_percent": 10.0,
    "max_drawdown": 5.0
}

# 缓存装饰器
class Cache:
    def __init__(self, ttl, max_size=100):
        self.ttl = ttl
        self.cache = {}
        self.max_size = max_size
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = datetime.now().timestamp()
            
            # 清理过期缓存
            self._clean_expired()
            
            # 检查缓存大小
            if len(self.cache) >= self.max_size and key not in self.cache:
                # 删除最旧的缓存项
                oldest_key = min(self.cache, key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                logger.info(f"缓存大小超过限制，删除最旧缓存项")
            
            # 检查缓存是否有效
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                if now - timestamp < self.ttl:
                    return cached_data
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            self.cache[key] = (result, now)
            return result
        return wrapper
    
    def _clean_expired(self):
        """清理过期的缓存项"""
        now = datetime.now().timestamp()
        expired_keys = [k for k, (_, t) in self.cache.items() if now - t >= self.ttl]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            logger.info(f"清理了{len(expired_keys)}个过期缓存项")

# 创建缓存实例
cache = Cache(CACHE_TTL)

@app.get("/")
async def root():
    """
    根路径，返回前端页面
    """
    return FileResponse("user_data/webapp/templates/index.html")

@app.get("/config")
async def config_page():
    """
    配置管理页面
    """
    return FileResponse("user_data/webapp/templates/config.html")

@app.get("/analysis")
async def analysis_page():
    """
    分析页面
    """
    return FileResponse("user_data/webapp/templates/analysis.html")

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ai-trading-bot-web"
    }

@app.get("/api/trades")
@cache
async def get_trades():
    """
    获取交易数据
    """
    try:
        # 这里可以从数据库或文件中获取真实交易数据
        # 暂时返回模拟数据
        return {
            "success": True,
            "data": mock_trades,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取交易数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取交易数据失败")

@app.get("/api/account")
@cache
async def get_account():
    """
    获取账户数据
    """
    try:
        # 这里可以从数据库或文件中获取真实账户数据
        # 暂时返回模拟数据
        return {
            "success": True,
            "data": mock_account,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取账户数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取账户数据失败")

@app.get("/api/chart/{pair}")
@cache
async def get_chart_data(pair: str):
    """
    获取图表数据
    """
    try:
        # 构建文件路径
        filename = f"{pair.replace('/', '_')}_5m_processed.json"
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        
        if os.path.exists(filepath):
            # 加载处理后的数据
            data = pd.read_json(filepath)
            
            # 准备图表数据
            chart_data = {
                "dates": data.index.strftime("%Y-%m-%d %H:%M:%S").tolist(),
                "prices": data['close'].tolist(),
                "volumes": data['volume'].tolist(),
                "ma5": data.get('ma5', []).tolist(),
                "ma10": data.get('ma10', []).tolist(),
                "ma20": data.get('ma20', []).tolist()
            }
            
            return {
                "success": True,
                "data": chart_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 异步生成模拟数据
            chart_data = await generate_mock_chart_data()
            return {
                "success": True,
                "data": chart_data,
                "timestamp": datetime.now().isoformat(),
                "note": "使用模拟数据"
            }
    except Exception as e:
        logger.error(f"获取图表数据失败: {e}")
        # 返回默认模拟数据作为降级方案
        try:
            chart_data = await generate_mock_chart_data()
            return {
                "success": True,
                "data": chart_data,
                "timestamp": datetime.now().isoformat(),
                "note": "使用模拟数据（原数据获取失败）"
            }
        except:
            raise HTTPException(status_code=500, detail="获取图表数据失败")

async def generate_mock_chart_data():
    """
    异步生成模拟图表数据
    """
    dates = []
    prices = []
    volumes = []
    ma5 = []
    ma10 = []
    ma20 = []
    
    # 生成过去24小时的数据
    for i in range(288):  # 24小时 * 12个5分钟周期
        date = datetime.now() - timedelta(minutes=5 * i)
        dates.append(date.strftime("%Y-%m-%d %H:%M:%S"))
        # 生成随机价格
        price = 60000 + np.random.normal(0, 500)
        prices.append(price)
        volumes.append(np.random.uniform(10, 100))
    
    # 反转数据，使其按时间正序排列
    dates.reverse()
    prices.reverse()
    volumes.reverse()
    
    # 计算移动平均线
    prices_series = pd.Series(prices)
    ma5 = prices_series.rolling(window=5).mean().tolist()
    ma10 = prices_series.rolling(window=10).mean().tolist()
    ma20 = prices_series.rolling(window=20).mean().tolist()
    
    return {
        "dates": dates,
        "prices": prices,
        "volumes": volumes,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20
    }

@app.get("/api/strategy")
@cache
async def get_strategy_info():
    """
    获取策略信息
    """
    try:
        strategy_info = {
            "name": "AI Strategy",
            "description": "基于机器学习的交易策略",
            "parameters": {
                "max_open_trades": 3,
                "stake_currency": "USDT",
                "stake_amount": "unlimited",
                "timeframe": "5m",
                "stoploss": -0.03,
                "trailing_stop": True,
                "trailing_stop_positive": 0.01,
                "trailing_stop_positive_offset": 0.02
            },
            "performance": {
                "total_trades": 100,
                "win_rate": 60,
                "average_profit": 0.5,
                "max_drawdown": 5.0,
                "sharpe_ratio": 1.5
            }
        }
        
        return {
            "success": True,
            "data": strategy_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取策略信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略信息失败")

if __name__ == "__main__":
    """
    运行应用
    """
    # 启动监控任务
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(monitoring_task())
    
    # 配置uvicorn参数
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        workers=1,  # 2核CPU建议使用1个工作进程
        reload=False,  # 生产环境禁用自动重载
        timeout_keep_alive=30,  # 保持连接超时时间
        timeout_graceful_shutdown=10  # 优雅关闭超时时间
    )
    
    server = uvicorn.Server(config)
    server.run()
