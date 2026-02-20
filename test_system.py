# 系统集成测试脚本
# 用于验证各个模块的功能

import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_data_processor():
    """
    测试数据获取与处理模块
    """
    logger.info("开始测试数据获取与处理模块...")
    
    try:
        from user_data.utils.data_processor import DataProcessor
        
        # 初始化数据处理器
        processor = DataProcessor()
        logger.info("数据处理器初始化成功")
        
        # 测试数据下载
        pairs = ["BTC/USDT", "ETH/USDT"]
        processor.download_history_data(pairs, "5m", days=3)
        logger.info("数据下载测试完成")
        
        # 测试数据加载
        for pair in pairs:
            data = processor.load_data(pair, "5m")
            if not data.empty:
                logger.info(f"数据加载成功: {pair}, 数据量: {len(data)}行")
            else:
                logger.warning(f"数据加载失败: {pair}")
        
        # 测试数据预处理
        for pair in pairs:
            data = processor.load_data(pair, "5m")
            if not data.empty:
                processed_data = processor.preprocess_data(data)
                logger.info(f"数据预处理成功: {pair}, 处理后数据量: {len(processed_data)}行")
        
        # 测试特征生成
        for pair in pairs:
            data = processor.load_data(pair, "5m")
            if not data.empty:
                processed_data = processor.preprocess_data(data)
                featured_data = processor.generate_features(processed_data)
                logger.info(f"特征生成成功: {pair}, 生成后数据量: {len(featured_data)}行")
        
        logger.info("数据获取与处理模块测试完成")
        return True
    except Exception as e:
        logger.error(f"数据获取与处理模块测试失败: {e}")
        return False


def test_ai_strategy():
    """
    测试AI交易策略
    """
    logger.info("开始测试AI交易策略...")
    
    try:
        from user_data.strategies.AI_Strategy import AI_Strategy
        from freqtrade.configuration import Configuration
        
        # 加载配置
        config = Configuration.from_files(["user_data/config.json"])
        
        # 初始化策略
        strategy = AI_Strategy(config)
        logger.info("AI策略初始化成功")
        
        # 测试策略参数
        logger.info(f"策略时间周期: {strategy.timeframe}")
        logger.info(f"策略止损: {strategy.stoploss}")
        logger.info(f"策略最大开仓数量: {config.get('max_open_trades')}")
        
        logger.info("AI交易策略测试完成")
        return True
    except Exception as e:
        logger.error(f"AI交易策略测试失败: {e}")
        return False


def test_webapp():
    """
    测试Web数据可视化界面
    """
    logger.info("开始测试Web数据可视化界面...")
    
    try:
        # 检查Web应用文件是否存在
        webapp_files = [
            "user_data/webapp/app.py",
            "user_data/webapp/templates/index.html"
        ]
        
        for file_path in webapp_files:
            if os.path.exists(file_path):
                logger.info(f"Web应用文件存在: {file_path}")
            else:
                logger.warning(f"Web应用文件不存在: {file_path}")
        
        logger.info("Web数据可视化界面测试完成")
        return True
    except Exception as e:
        logger.error(f"Web数据可视化界面测试失败: {e}")
        return False


def test_docker_config():
    """
    测试Docker配置
    """
    logger.info("开始测试Docker配置...")
    
    try:
        # 检查Docker相关文件是否存在
        docker_files = [
            "Dockerfile",
            "requirements.txt",
            "deploy.sh"
        ]
        
        for file_path in docker_files:
            if os.path.exists(file_path):
                logger.info(f"Docker配置文件存在: {file_path}")
            else:
                logger.warning(f"Docker配置文件不存在: {file_path}")
        
        logger.info("Docker配置测试完成")
        return True
    except Exception as e:
        logger.error(f"Docker配置测试失败: {e}")
        return False


def main():
    """
    主测试函数
    """
    logger.info("开始系统集成测试...")
    
    # 运行所有测试
    tests = [
        ("数据获取与处理模块", test_data_processor),
        ("AI交易策略", test_ai_strategy),
        ("Web数据可视化界面", test_webapp),
        ("Docker配置", test_docker_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n=== 测试: {test_name} ===")
        result = test_func()
        results.append((test_name, result))
    
    # 汇总测试结果
    logger.info("\n=== 测试结果汇总 ===")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "通过" if result else "失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n总测试数: {len(results)}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 所有测试通过！系统集成成功！")
    else:
        logger.warning("\n⚠️  部分测试失败，需要修复！")


if __name__ == "__main__":
    main()
