#!/bin/bash

# AI交易机器人 - GitHub上传控制脚本
# 此脚本用于确保只上传需要的文件到GitHub

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== AI交易机器人 - GitHub上传控制脚本 ===${NC}"
echo

# 检查Git是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}错误: Git未安装${NC}"
    echo -e "请先安装Git: https://git-scm.com/downloads"
    exit 1
fi

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}警告: 当前目录不是Git仓库${NC}"
    echo -e "请先初始化Git仓库:
  git init
  git remote add origin https://github.com/yourusername/ai-trading-bot.git"
    exit 1
fi

# 检查config.json是否包含敏感信息
echo -e "${GREEN}检查配置文件...${NC}"
if grep -q '"key": "[^"]\+' user_data/config.json; then
    echo -e "${YELLOW}警告: config.json可能包含API密钥${NC}"
    echo -e "建议移除敏感信息后再上传"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ config.json未包含敏感信息${NC}"
fi

echo

# 显示需要上传的文件
echo -e "${GREEN}需要上传的文件:${NC}"
echo "核心文件:"
echo "  .gitignore"
echo "  Dockerfile"
echo "  README.md"
echo "  deploy.sh"
echo "  package.json"
echo "  package-lock.json (可选)"
echo "  postcss.config.js"
echo "  requirements.txt"
echo "  tailwind.config.js"
echo "  test_system.py"
echo "  todoThing.md"
echo "  upload_to_github.sh"
echo
echo "用户数据目录:"
echo "  user_data/config.json"
echo "  user_data/strategies/"
echo "  user_data/utils/"
echo "  user_data/webapp/"
echo
echo -e "${YELLOW}忽略的文件:${NC}"
echo "  user_data/data/"
echo "  user_data/hyperopts/"
echo "  user_data/notebooks/"
echo "  .trae/"
echo "  node_modules/"
echo "  venv/"
echo "  __pycache__/"
echo "  *.pyc"
echo "  *.log"
echo

# 询问是否继续
read -p "是否开始上传? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 执行Git操作
echo -e "${GREEN}开始上传...${NC}"
echo

# 添加文件
echo -e "${GREEN}添加文件...${NC}"
git add \
    .gitignore \
    Dockerfile \
    README.md \
    deploy.sh \
    package.json \
    package-lock.json \
    postcss.config.js \
    requirements.txt \
    tailwind.config.js \
    test_system.py \
    todoThing.md \
    upload_to_github.sh \
    user_data/config.json \
    user_data/strategies/ \
    user_data/utils/ \
    user_data/webapp/

# 检查是否有文件需要提交
git_status=$(git status --porcelain)
if [ -z "$git_status" ]; then
    echo -e "${YELLOW}没有文件需要提交${NC}"
    exit 0
fi

# 提交文件
echo -e "${GREEN}提交文件...${NC}"
git commit -m "更新项目文件"

# 推送文件
echo -e "${GREEN}推送文件...${NC}"
git push origin main

echo
echo -e "${GREEN}✓ 上传完成!${NC}"
echo
echo -e "${GREEN}后续步骤:${NC}"
echo "1. 在新设备上克隆仓库:
   git clone https://github.com/yourusername/ai-trading-bot.git"
echo "2. 安装依赖:
   python -m pip install -r requirements.txt
   npm install"
echo "3. 配置API密钥:
   编辑 user_data/config.json"
echo "4. 启动Web界面:
   python user_data/webapp/app.py"
echo