# 阿里云Layer上传指南

## 手动创建Layer

1. 打开 https://fc.console.aliyun.com/ > Layers
2. 点击"创建层"
3. 填写：
   - 层名称：resume-deps
   - 描述：Python dependencies
   - 运行时：Python 3.10
4. 上传 zip 文件：`D:\gowork\题\resume-analysis\backend\layer\layer.zip`
5. 创建成功后，复制层的ARN

## 更新函数配置

1. 找到函数：resume-analysis-service > resume-api
2. 在"层配置"中添加刚才创建的层
3. 重新部署
