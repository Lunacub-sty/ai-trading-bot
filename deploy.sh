#!/bin/bash

# AI交易机器人部署脚本
# 用于在阿里云服务器上部署项目

echo "开始部署AI交易机器人..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，开始安装Docker..."
    # 安装Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    # 重新加载Docker服务
    sudo systemctl restart docker
    echo "Docker安装完成"
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose未安装，开始安装..."
    # 安装Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose安装完成"
fi

# 克隆项目代码（如果不存在）
if [ ! -d "ai-trading-bot" ]; then
    echo "克隆项目代码..."
    git clone https://github.com/yourusername/ai-trading-bot.git
    cd ai-trading-bot
else
    echo "项目代码已存在，进入目录..."
    cd ai-trading-bot
    # 更新代码
    git pull
fi

# 创建.env文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "创建.env文件..."
    cat > .env << EOF
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
EOF
    echo "请编辑.env文件，填写相关配置"
fi

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t ai-trading-bot .

# 运行容器
echo "运行容器..."
docker run -d \
    --name ai-trading-bot \
    -p 8080:8080 \
    -v $(pwd)/user_data:/app/user_data \
    ai-trading-bot

echo "部署完成！"
echo "Web界面地址: http://$(curl -s ifconfig.me):8080"
echo "请在浏览器中访问上述地址，使用配置的用户名和密码登录"
