<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-cross--platform-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <a href="#english">English</a> • 
  <a href="#简体中文">简体中文</a> • 
  <a href="#繁體中文">繁體中文</a>
</p>

---

<a name="english"></a>
# 🔐 EnvPilot

## 🎉 Project Introduction

**EnvPilot** is a lightweight environment variables intelligent management engine designed for developers who need secure, organized, and multi-environment variable management. It solves the common pain points of `.env` file chaos, sensitive data leaks, and difficult environment switching.

### 💡 Inspiration
Inspired by the need for a simple yet powerful environment variable management tool that doesn't require complex setup or external dependencies. EnvPilot brings enterprise-grade security features to individual developers and small teams.

### ✨ Key Features

- 🔒 **AES-256-GCM Encryption** - Military-grade encryption for sensitive variables
- 📁 **Multi-Project Support** - Manage unlimited projects with isolated environments
- 🔄 **Multi-Environment Management** - Seamlessly switch between development, staging, production
- 🔍 **Security Leak Scanner** - Detect exposed secrets in your codebase
- 📥 **Import/Export** - Support for `.env`, JSON, and shell formats
- 💻 **Interactive TUI** - Beautiful terminal interface for easy management
- 🚀 **Zero External Dependencies** - Only requires `cryptography` package
- 🛡️ **Sensitive Auto-Detection** - Automatically encrypt password, key, token variables

---

## 🚀 Quick Start

### Requirements
- Python 3.8 or higher
- pip package manager

### Installation

```bash
# Install from PyPI
pip install envpilot

# Or install from source
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot
pip install -e .
```

### Basic Usage

```bash
# Create a new project
envpilot init myproject

# Set a variable
envpilot set DATABASE_URL "postgres://localhost/mydb"

# Set an encrypted variable
envpilot set API_KEY "sk-secret123" --encrypt

# Get a variable
envpilot get DATABASE_URL

# List all variables
envpilot list

# Switch environment
envpilot switch production

# Launch interactive TUI
envpilot tui
```

---

## 📖 Detailed Usage Guide

### Project Management

```bash
# List all projects
envpilot project list

# Switch to a different project
envpilot project switch another-project

# Delete a project
envpilot project delete old-project
```

### Environment Management

```bash
# List environments
envpilot env list

# Add a new environment
envpilot env add testing

# Copy environment
envpilot env copy --source development staging

# Delete environment
envpilot env delete old-env
```

### Variable Operations

```bash
# Set with description and tags
envpilot set API_KEY "secret" --description "External API key" --tags "api,external"

# Search variables
envpilot search "database"

# Delete variable
envpilot delete OLD_VAR

# List with tag filter
envpilot list --tag api
```

### Import & Export

```bash
# Import from .env file
envpilot import .env.example

# Export to .env file
envpilot export .env

# Export to JSON
envpilot export env.json --format json

# Export shell commands
envpilot export --format shell --shell bash
```

### Security Scanning

```bash
# Scan current directory
envpilot scan

# Scan specific path
envpilot scan ./src --format json

# Generate markdown report
envpilot scan . --format markdown > security-report.md
```

### Master Password Management

```bash
# Set master password for encryption
envpilot password

# Verify existing password
envpilot password --verify
```

---

## 💡 Design Philosophy & Roadmap

### Design Philosophy
EnvPilot is built with these principles in mind:
- **Simplicity First** - Minimal setup, maximum productivity
- **Security by Default** - Encryption at rest, leak detection built-in
- **Developer Experience** - Beautiful TUI, intuitive CLI commands
- **Zero Lock-in** - Standard formats, easy export, portable storage

### Future Roadmap
- [ ] Cloud sync support (optional)
- [ ] Team collaboration features
- [ ] Browser extension for web apps
- [ ] VS Code extension
- [ ] Docker image for CI/CD integration
- [ ] REST API server mode

---

## 📦 Build & Deployment

### Build from Source

```bash
# Clone repository
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot

# Install build dependencies
pip install build

# Build package
python -m build

# Built packages will be in dist/
```

### Deploy in CI/CD

```bash
# Load variables in your CI script
eval $(envpilot export --format shell)

# Or load to environment
envpilot export --format shell >> $GITHUB_ENV
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Add tests for new features
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

---
---

<a name="简体中文"></a>
# 🔐 EnvPilot

## 🎉 项目介绍

**EnvPilot** 是一款轻量级环境变量智能管理引擎，专为需要安全、有序、多环境变量管理的开发者设计。它解决了 `.env` 文件混乱、敏感数据泄露、环境切换困难等常见痛点。

### 💡 灵感来源
灵感来源于对简单而强大的环境变量管理工具的需求——无需复杂配置或外部依赖。EnvPilot 将企业级安全特性带给个人开发者和小型团队。

### ✨ 核心特性

- 🔒 **AES-256-GCM 加密** - 军用级加密保护敏感变量
- 📁 **多项目支持** - 管理无限项目，环境隔离
- 🔄 **多环境管理** - 开发、测试、生产环境无缝切换
- 🔍 **安全泄露扫描** - 检测代码库中的暴露密钥
- 📥 **导入导出** - 支持 `.env`、JSON、Shell 格式
- 💻 **交互式 TUI** - 美观的终端界面，轻松管理
- 🚀 **零外部依赖** - 仅需 `cryptography` 包
- 🛡️ **敏感自动检测** - 自动加密 password、key、token 变量

---

## 🚀 快速开始

### 环境要求
- Python 3.8 或更高版本
- pip 包管理器

### 安装方式

```bash
# 从 PyPI 安装
pip install envpilot

# 或从源码安装
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot
pip install -e .
```

### 基本使用

```bash
# 创建新项目
envpilot init myproject

# 设置变量
envpilot set DATABASE_URL "postgres://localhost/mydb"

# 设置加密变量
envpilot set API_KEY "sk-secret123" --encrypt

# 获取变量
envpilot get DATABASE_URL

# 列出所有变量
envpilot list

# 切换环境
envpilot switch production

# 启动交互式 TUI
envpilot tui
```

---

## 📖 详细使用指南

### 项目管理

```bash
# 列出所有项目
envpilot project list

# 切换到其他项目
envpilot project switch another-project

# 删除项目
envpilot project delete old-project
```

### 环境管理

```bash
# 列出环境
envpilot env list

# 添加新环境
envpilot env add testing

# 复制环境
envpilot env copy --source development staging

# 删除环境
envpilot env delete old-env
```

### 变量操作

```bash
# 设置带描述和标签的变量
envpilot set API_KEY "secret" --description "外部API密钥" --tags "api,external"

# 搜索变量
envpilot search "database"

# 删除变量
envpilot delete OLD_VAR

# 按标签筛选列表
envpilot list --tag api
```

### 导入导出

```bash
# 从 .env 文件导入
envpilot import .env.example

# 导出到 .env 文件
envpilot export .env

# 导出为 JSON
envpilot export env.json --format json

# 导出 Shell 命令
envpilot export --format shell --shell bash
```

### 安全扫描

```bash
# 扫描当前目录
envpilot scan

# 扫描指定路径
envpilot scan ./src --format json

# 生成 Markdown 报告
envpilot scan . --format markdown > security-report.md
```

### 主密码管理

```bash
# 设置加密主密码
envpilot password

# 验证现有密码
envpilot password --verify
```

---

## 💡 设计理念与迭代规划

### 设计理念
EnvPilot 基于以下原则构建：
- **简单优先** - 最小配置，最大生产力
- **默认安全** - 静态加密，内置泄露检测
- **开发者体验** - 美观 TUI，直观 CLI 命令
- **零锁定** - 标准格式，易于导出，便携存储

### 后续迭代规划
- [ ] 云同步支持（可选）
- [ ] 团队协作功能
- [ ] 浏览器扩展
- [ ] VS Code 扩展
- [ ] Docker 镜像用于 CI/CD 集成
- [ ] REST API 服务模式

---

## 📦 打包与部署

### 从源码构建

```bash
# 克隆仓库
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot

# 安装构建依赖
pip install build

# 构建包
python -m build

# 构建产物在 dist/ 目录
```

### CI/CD 部署

```bash
# 在 CI 脚本中加载变量
eval $(envpilot export --format shell)

# 或加载到环境
envpilot export --format shell >> $GITHUB_ENV
```

---

## 🤝 贡献指南

欢迎贡献！请遵循以下指南：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 代码规范
- 遵循 PEP 8 规范
- 为新功能添加测试
- 按需更新文档

---

## 📄 开源协议

本项目采用 MIT 协议开源 - 详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  由 <a href="https://github.com/gitstq">gitstq</a> 用 ❤️ 制作
</p>

---
---

<a name="繁體中文"></a>
# 🔐 EnvPilot

## 🎉 專案介紹

**EnvPilot** 是一款輕量級環境變數智慧管理引擎，專為需要安全、有序、多環境變數管理的開發者設計。它解決了 `.env` 檔案混亂、敏感資料外洩、環境切換困難等常見痛點。

### 💡 靈感來源
靈感來自於對簡單而強大的環境變數管理工具的需求——無需複雜設定或外部依賴。EnvPilot 將企業級安全特性帶給個人開發者和小型團隊。

### ✨ 核心特性

- 🔒 **AES-256-GCM 加密** - 軍用級加密保護敏感變數
- 📁 **多專案支援** - 管理無限專案，環境隔離
- 🔄 **多環境管理** - 開發、測試、正式環境無縫切換
- 🔍 **安全外洩掃描** - 偵測程式碼庫中的暴露金鑰
- 📥 **匯入匯出** - 支援 `.env`、JSON、Shell 格式
- 💻 **互動式 TUI** - 美觀的終端介面，輕鬆管理
- 🚀 **零外部依賴** - 僅需 `cryptography` 套件
- 🛡️ **敏感自動偵測** - 自動加密 password、key、token 變數

---

## 🚀 快速開始

### 環境要求
- Python 3.8 或更高版本
- pip 套件管理器

### 安裝方式

```bash
# 從 PyPI 安裝
pip install envpilot

# 或從原始碼安裝
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot
pip install -e .
```

### 基本使用

```bash
# 建立新專案
envpilot init myproject

# 設定變數
envpilot set DATABASE_URL "postgres://localhost/mydb"

# 設定加密變數
envpilot set API_KEY "sk-secret123" --encrypt

# 取得變數
envpilot get DATABASE_URL

# 列出所有變數
envpilot list

# 切換環境
envpilot switch production

# 啟動互動式 TUI
envpilot tui
```

---

## 📖 詳細使用指南

### 專案管理

```bash
# 列出所有專案
envpilot project list

# 切換到其他專案
envpilot project switch another-project

# 刪除專案
envpilot project delete old-project
```

### 環境管理

```bash
# 列出環境
envpilot env list

# 新增環境
envpilot env add testing

# 複製環境
envpilot env copy --source development staging

# 刪除環境
envpilot env delete old-env
```

### 變數操作

```bash
# 設定帶描述和標籤的變數
envpilot set API_KEY "secret" --description "外部API金鑰" --tags "api,external"

# 搜尋變數
envpilot search "database"

# 刪除變數
envpilot delete OLD_VAR

# 按標籤篩選列表
envpilot list --tag api
```

### 匯入匯出

```bash
# 從 .env 檔案匯入
envpilot import .env.example

# 匯出到 .env 檔案
envpilot export .env

# 匯出為 JSON
envpilot export env.json --format json

# 匯出 Shell 命令
envpilot export --format shell --shell bash
```

### 安全掃描

```bash
# 掃描當前目錄
envpilot scan

# 掃描指定路徑
envpilot scan ./src --format json

# 產生 Markdown 報告
envpilot scan . --format markdown > security-report.md
```

### 主密碼管理

```bash
# 設定加密主密碼
envpilot password

# 驗證現有密碼
envpilot password --verify
```

---

## 💡 設計理念與迭代規劃

### 設計理念
EnvPilot 基於以下原則構建：
- **簡單優先** - 最小設定，最大生產力
- **預設安全** - 靜態加密，內建外洩偵測
- **開發者體驗** - 美觀 TUI，直觀 CLI 命令
- **零鎖定** - 標準格式，易於匯出，可攜儲存

### 後續迭代規劃
- [ ] 雲端同步支援（可選）
- [ ] 團隊協作功能
- [ ] 瀏覽器擴充功能
- [ ] VS Code 擴充功能
- [ ] Docker 映像檔用於 CI/CD 整合
- [ ] REST API 服務模式

---

## 📦 打包與部署

### 從原始碼建置

```bash
# 複製儲存庫
git clone https://github.com/gitstq/EnvPilot.git
cd EnvPilot

# 安裝建置相依性
pip install build

# 建置套件
python -m build

# 建置產物在 dist/ 目錄
```

### CI/CD 部署

```bash
# 在 CI 腳本中載入變數
eval $(envpilot export --format shell)

# 或載入到環境
envpilot export --format shell >> $GITHUB_ENV
```

---

## 🤝 貢獻指南

歡迎貢獻！請遵循以下指南：

1. Fork 本儲存庫
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 程式碼規範
- 遵循 PEP 8 規範
- 為新功能新增測試
- 按需更新文件

---

## 📄 開源授權

本專案採用 MIT 授權條款開源 - 詳見 [LICENSE](LICENSE) 檔案。

---

<p align="center">
  由 <a href="https://github.com/gitstq">gitstq</a> 用 ❤️ 製作
</p>
