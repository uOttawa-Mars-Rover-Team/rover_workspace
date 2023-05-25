FROM node:14.17.3-alpine3.14

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
CMD npm start