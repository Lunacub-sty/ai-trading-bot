# AI交易机器人

基于Python和Freqtrade实现的AI驱动加密货币交易机器人，专门针对欧易交易所进行优化，可部署在阿里云服务器上，并通过Web界面查看交易数据。

## 项目概述

本项目使用机器学习算法分析市场数据，自动生成交易信号并执行交易。系统具有以下特点：

- 基于机器学习的交易策略
- 支持欧易交易所（OKX）
- 可部署在阿里云服务器
- 提供Web数据可视化界面
- 包含完整的风险管理机制

## 技术栈

- **核心框架**: Python 3.8+, Freqtrade
- **AI/ML库**: scikit-learn, pandas, numpy, TA-Lib
- **Web框架**: FastAPI, HTML/CSS/JavaScript, Tailwind CSS
- **数据处理**: pandas, ccxt
- **部署**: Docker, 阿里云ECS

## 安装与配置

### 本地开发环境

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/ai-trading-bot.git
   cd ai-trading-bot
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows: `venv\Scripts\activate
   - Linux/Mac: `source venv/bin/activate`

4. **安装依赖**
   ```bash
   pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
   ```

5. **配置交易所API**
   编辑 `user_data/config.json` 文件，填写欧易交易所的API密钥：
   ```json
   "exchange": {
       "name": "okx",
       "key": "your_api_key",
       "secret": "your_api_secret",
       "password": "your_api_password",
       ...
   }
   ```

### 阿里云服务器部署

1. **登录阿里云服务器**
   ```bash
   ssh root@your_server_ip
   ```

2. **运行部署脚本**
   ```bash
   wget https://raw.githubusercontent.com/yourusername/ai-trading-bot/main/deploy.sh
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **配置环境变量**
   编辑 `.env` 文件，填写相关配置：
   ```env
   # 交易所API配置
   EXCHANGE_KEY=your_api_key
   EXCHANGE_SECRET=your_api_secret
   EXCHANGE_PASSWORD=your_api_password

   # 策略配置
   MAX_OPEN_TRADES=3
   STAKE_CURRENCY=USDT
   STAKE_AMOUNT=unlimited
   TIMEFRAME=5m
   DRY_RUN=true
   DRY_RUN_WALLET=1000

   # API服务器配置
   API_USERNAME=freqtrader
   API_PASSWORD=your_api_password
   ```

4. **启动容器**
   ```bash
   docker run -d \
       --name ai-trading-bot \
       -p 8080:8080 \
       -v $(pwd)/user_data:/app/user_data \
       ai-trading-bot
   ```

## 使用方法

### 启动交易机器人

```bash
# 本地启动
freqtrade trade --config user_data/config.json --strategy AI_Strategy

# 服务器启动（Docker）
docker start ai-trading-bot
```

### 启动Web界面

```bash
# 本地启动
python user_data/webapp/app.py

# 服务器启动（Docker）
# Web界面已在容器中自动启动
```

### 访问Web界面

在浏览器中访问：
- 本地: `http://localhost:8001`
- 服务器: `http://your_server_ip:8001`

### Web界面功能

新的现代化仪表盘界面包含以下功能：

1. **左侧垂直导航菜单**：
   - 仪表盘主页
   - 分析页面（含AI回测报告分析）
   - 策略管理
   - 配置管理

2. **顶部导航栏**：
   - 搜索功能
   - 通知中心
   - 用户设置

3. **关键指标卡片**：
   - 账户余额
   - 总交易量
   - 胜率
   - 总收益

4. **数据可视化**：
   - 价格图表（BTC/USDT、ETH/USDT、BNB/USDT）
   - 权益趋势图表
   - 技术指标（MA5、MA10）

5. **最近交易记录**：
   - 交易对
   - 交易方向
   - 收益情况

6. **策略分析**：
   - 总交易次数
   - 平均收益
   - 夏普比率

7. **通知和活动面板**：
   - 交易信号通知
   - 策略表现通知
   - 系统活动记录

8. **AI回测报告分析**：
   - 智能分析回测数据，识别策略优势和劣势
   - 提供市场洞察和参数优化建议
   - 支持上传自定义回测报告进行分析
   - 生成详细的分析报告和改进方案

### 主题设置

Web界面采用深色主题设计，以绿色为主色调，提供了现代化、专业的交易监控体验。

## 新设备依赖安装

在新设备上开发或部署项目时，需要安装以下依赖：

### 1. Python依赖

```bash
# 使用pip安装Python依赖
python -m pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 或者使用标准pip源
python -m pip install -r requirements.txt
```

### 2. Web界面依赖

```bash
# 安装Node.js依赖（用于Tailwind CSS）
npm install

# 构建Tailwind CSS（如果需要）
npx tailwindcss build user_data/webapp/components/tailwind.css -o user_data/webapp/components/styles.css
```

### 3. 系统依赖

#### Windows系统

```powershell
# 安装Git
# 从官网下载并安装：https://git-scm.com/download/win

# 安装Node.js
# 从官网下载并安装：https://nodejs.org/en/download/

# 安装Python 3.8+
# 从官网下载并安装：https://www.python.org/downloads/
```

#### Linux系统

```bash
# Ubuntu/Debian
apt update && apt install -y git nodejs npm python3 python3-pip

# CentOS/RHEL
yum install -y git nodejs npm python3 python3-pip

# Arch Linux
pacman -Syu git nodejs npm python3 python-pip
```

#### macOS系统

```bash
# 使用Homebrew安装
brew install git node python

# 或者从官网下载安装包
```

### 4. 验证安装

```bash
# 验证Python安装
python --version
pip --version

# 验证Node.js安装
node --version
npm --version

# 验证Git安装
git --version
```

### 5. 首次运行步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/ai-trading-bot.git
   cd ai-trading-bot
   ```

2. **安装依赖**
   ```bash
   # 安装Python依赖
   python -m pip install -r requirements.txt
   
   # 安装Node.js依赖
   npm install
   ```

3. **配置交易所API**
   编辑 `user_data/config.json` 文件，填写OKX交易所的API密钥

4. **启动Web界面**
   ```bash
   python user_data/webapp/app.py
   ```

5. **访问Web界面**
   在浏览器中访问 `http://localhost:8001`

## 项目文件结构

以下是项目的主要文件结构，包含需要上传至GitHub的文件：

```
ai-trading-bot/
├── user_data/                  # 用户数据目录
│   ├── config.json             # 配置文件
│   ├── strategies/             # 交易策略
│   │   └── AI_Strategy.py      # AI交易策略
│   ├── utils/                  # 工具函数
│   │   ├── data_processor.py   # 数据处理
│   │   └── trade_executor.py   # 交易执行
│   └── webapp/                 # Web界面
│       ├── app.py              # Web后端
│       ├── components/         # Web组件
│       └── templates/          # Web模板
├── .gitignore                  # Git忽略文件
├── Dockerfile                  # Docker配置
├── README.md                   # 项目说明
├── deploy.sh                   # 部署脚本
├── package.json                # Node.js配置
├── postcss.config.js           # PostCSS配置
├── requirements.txt            # Python依赖
├── tailwind.config.js          # Tailwind配置
└── test_system.py              # 系统测试
```

## 需要上传至GitHub的文件

以下是需要上传至GitHub的文件和目录：

### 核心文件
- `.gitignore`
- `Dockerfile`
- `README.md`
- `deploy.sh`
- `package.json`
- `package-lock.json` (可选，但建议上传)
- `postcss.config.js`
- `requirements.txt`
- `tailwind.config.js`
- `test_system.py`
- `todoThing.md` (新增)

### 用户数据目录
- `user_data/config.json` (注意：需要移除敏感信息)
- `user_data/strategies/`
- `user_data/utils/`
- `user_data/webapp/`

### 不需要上传的文件
- `user_data/data/` (数据目录，可能包含大量数据)
- `user_data/hyperopts/` (超参数优化结果)
- `user_data/notebooks/` (Jupyter notebooks，可选)
- `.trae/` (IDE相关文件)
- `node_modules/` (Node.js依赖，由npm install生成)
- `venv/` (虚拟环境，由用户本地创建)
- `__pycache__/` (Python编译缓存)
- `*.pyc` (Python编译文件)
- `*.log` (日志文件)

## 安全注意事项

1. **API密钥保护**：不要将包含真实API密钥的 `config.json` 文件上传至GitHub
2. **敏感信息**：确保所有敏感信息都已从上传文件中移除
3. **环境变量**：建议使用环境变量存储敏感配置
4. **.gitignore**：确保 `.gitignore` 文件正确配置，避免上传不必要的文件
5. **权限设置**：确保脚本文件有正确的执行权限

## 策略说明

### AI交易策略

本项目使用基于随机森林的机器学习策略，主要特点：

1. **特征工程**：
   - 技术指标（RSI、MACD、布林带等）
   - 移动平均线（MA5、MA10、MA20）
   - 价格和交易量变化
   - 市场情绪指标

2. **模型训练**：
   - 使用历史数据训练随机森林分类器
   - 自动调整模型参数
   - 实时评估模型性能

3. **交易信号**：
   - 基于模型预测的市场方向
   - 结合技术指标确认信号
   - 包含完整的风险管理

### 风险管理

- **止损设置**：默认3%
- **追踪止损**：启用
- **最大开仓数量**：默认3个
- **单个持仓最大占比**：30%
- **每笔交易风险**：2%

## 目录结构

```
ai-trading-bot/
├── user_data/
│   ├── config.json          # 配置文件
│   ├── strategies/
│   │   └── AI_Strategy.py   # AI交易策略
│   ├── utils/
│   │   ├── data_processor.py    # 数据获取与处理
│   │   └── trade_executor.py     # 交易执行系统
│   └── webapp/
│       ├── app.py           # Web后端
│       └── templates/
│           └── index.html   # Web前端
├── Dockerfile               # Docker配置
├── requirements.txt         # 依赖列表
├── deploy.sh                # 部署脚本
└── test_system.py           # 系统测试脚本
```

## 测试

运行系统集成测试：

```bash
python test_system.py
```

测试结果将显示在终端中，包括各个模块的测试状态。

## 常见问题

1. **API连接失败**
   - 检查API密钥是否正确
   - 确保API权限设置正确
   - 检查网络连接

2. **数据下载失败**
   - 检查网络连接
   - 确认交易所API限制
   - 尝试使用代理

3. **Web界面无法访问**
   - 检查端口是否开放
   - 确认防火墙设置
   - 检查容器是否运行

4. **策略表现不佳**
   - 调整模型参数
   - 增加更多特征
   - 考虑使用其他机器学习算法

## 许可证

MIT License

## 免责声明

本项目仅供学习和研究使用，不构成投资建议。加密货币交易存在高风险，请谨慎使用。使用本项目造成的任何损失，作者不承担责任。