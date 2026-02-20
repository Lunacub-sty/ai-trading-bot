# Web数据可视化界面后端
# 基于FastAPI

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

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

@app.get("/ai-strategy")
async def ai_strategy_page():
    """
    AI策略创建页面
    """
    return FileResponse("user_data/webapp/templates/ai-strategy.html")

@app.get("/api/trades")
async def get_trades():
    """
    获取交易数据
    """
    try:
        # 这里可以从数据库或文件中获取真实交易数据
        # 暂时返回模拟数据
        return {
            "success": True,
            "data": mock_trades
        }
    except Exception as e:
        logger.error(f"获取交易数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取交易数据失败")

@app.get("/api/account")
async def get_account():
    """
    获取账户数据
    """
    try:
        # 这里可以从数据库或文件中获取真实账户数据
        # 暂时返回模拟数据
        return {
            "success": True,
            "data": mock_account
        }
    except Exception as e:
        logger.error(f"获取账户数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取账户数据失败")

@app.get("/api/chart/{pair}")
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
                "data": chart_data
            }
        else:
            # 返回模拟数据
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
            
            chart_data = {
                "dates": dates,
                "prices": prices,
                "volumes": volumes,
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20
            }
            
            return {
                "success": True,
                "data": chart_data
            }
    except Exception as e:
        logger.error(f"获取图表数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取图表数据失败")

@app.get("/api/strategy")
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
            "data": strategy_info
        }
    except Exception as e:
        logger.error(f"获取策略信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取策略信息失败")

if __name__ == "__main__":
    """
    运行应用
    """
    # 确保目录存在
    os.makedirs("user_data/webapp/static", exist_ok=True)
    os.makedirs("user_data/webapp/templates", exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
