FROM node:18.17-alpine

# Set working directory
RUN mkdir /rover-dashboard
WORKDIR /rover-dashboard

# Copy app dependencies
COPY package.json package-lock.json ./

# Runs install script
RUN npm install

# Copy app
COPY . .

# Runs start script
CMD ["npm", "run", "dev"]

EXPOSE 5173
