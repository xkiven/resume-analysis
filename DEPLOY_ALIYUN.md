# 阿里云函数计算部署指南

## 前置条件
1. 阿里云账号
2. 已开通函数计算服务

## 步骤1：配置阿里云CLI

```bash
npm install -g @serverless-devs/s
```

配置凭证（替换为您的实际值）：
```bash
s config add \
  --AccessKeyID 您的AccessKeyID \
  --AccessKeySecret 您的AccessKeySecret \
  --AccountID 您的阿里云账户ID
```

## 步骤2：修改配置

编辑 `backend/serverless.yml`，将 `${env:xxx}` 替换为实际值：
- ALIYUN_ACCOUNT_ID: 您的阿里云账户ID

## 步骤3：部署

```bash
cd backend
s deploy
```

## 步骤4：配置环境变量

在阿里云控制台为函数配置环境变量：
- DASHSCOPE_API_KEY: 您的通义千问API Key

## 步骤5：获取API地址

部署成功后，会显示HTTP触发器地址

## 步骤6：更新前端

将获取的API地址更新到 `app.js` 中的 `API_BASE_URL`
