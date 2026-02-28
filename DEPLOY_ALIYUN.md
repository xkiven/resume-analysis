# 阿里云函数计算部署指南

## 步骤1：配置凭证

运行以下命令（替换为您的实际值）：

```bash
s config add -a aliyun --AccessKeyID 您的AccessKeyID --AccessKeySecret 您的AccessKeySecret
```

或使用环境变量：
```bash
set ALIYUN_ACCESS_KEY_ID=您的AccessKeyID
set ALIYUN_ACCESS_KEY_SECRET=您的AccessKeySecret
```

## 步骤2：修改配置

编辑 `backend/serverless.yml`，移除或简化 vpcConfig（新手建议先不加VPC）：

```yaml
provider:
  name: aliyun
  runtime: python3.10
  memorySize: 512
  timeout: 60
  region: cn-shanghai
  # 移除 vpcConfig 相关配置
```

## 步骤3：部署

```bash
cd backend
s deploy
```

## 步骤4：配置环境变量

在阿里云控制台为函数添加环境变量：
- DASHSCOPE_API_KEY: 您的通义千问API Key

## 步骤5：更新前端

部署完成后，将 API 地址更新到 `app.js`
