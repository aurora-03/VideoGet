FROM node:20-slim

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 构建应用
RUN npm run build

# 暴露端口
EXPOSE 3000

# 启动预览服务器（生产环境应使用 nginx）
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
