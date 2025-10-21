# AI-Learning-Assistant-RPG-Archive
ai跑团助手，根据输入query生成一张可以导入酒馆sillytavern的角色卡

## 开发环境搭建

1. 仓库克隆

    ```bash
    git clone https://github.com/ai-learning-assistant-dev/AI-Learning-Assistant-RPG-Archive.git
    ```

2. 检查必要依赖
    - UV (一个python包管理器)
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. 设置开发环境
    ```bash
    make install-dev
    make pre-commit-install
    source .venv/bin/activate  //激活venv
    ```
4. 配置api-key//TODO ，目前配置在config/settings.py中
