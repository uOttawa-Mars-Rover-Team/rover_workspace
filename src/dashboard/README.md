# Rover Dashboard

Gives you an overview of the sensors, images, and other ROS information (topics, services, params, nodes) with [roslibjs](https://github.com/RobotWebTools/roslibjs).

![screenshot](./public/screenshot.png)

## Prerequisites

> If you already have __Node.js__ and __npm__ installed or is running the Docker version, you can go straight to [Run the code](#run-the-code) (installed if you ran the `full_setup.sh` script).

### Verify dependency installed

Make sure that __Node.js__ and __npm__ is installed. 

* To check if __Node.js__ is installed, try running `node -v` it should return the version, ex: `v10.16.0`.
* To check if __npm__ is installed, try running `npm -v` it should return the version number, ex: `6.14.13`.

### Install Node.js and NPM

To install Node.js, run the following commands :

```bash
sudo apt-get install curl python-software-properties
curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt install -y nodejs
```

## Run the code

> Make sure the ROS webserver is running. To run it, make sure _roscore_ is running by running `roscore`, and launch the webserver by executing this command in another terminal from the root of the rover workspace `roslaunch src/dashboard/websocket.launch`.

At the root of this directory, to install the React dependencies of the dashboard:

```bash
npm install
```

### Development

To run the React app:

```bash
npm start
```

### Production (or when we want optimal performance)

Build the application:

```bash
npm run build
```

Then serve the application (run a local HTTP server serving the build):

```bash
npm run serve
```

### Docker

If you want to run the dashboard in Docker without needing to install __Node.js__, simply run the following command at the root of this directory:

```bash
docker-compose up
```

> You may need to use `host.docker.internal` instead of `localhost` to connect to the ROS webserver, so the address to connect to ROS within the dashboard would be `ws://host.docker.internal:9090` instead of `ws://localhost:9090`

## Development

A [React](https://reactjs.org/) web application communicating with ROS ([ROSLIBjs documentation](http://robotwebtools.org/jsdoc/roslibjs/current/index.html)) using the Ant Design ([Ant Design documentation](https://ant.design/components/overview/)) React UI library.

Project structure:

* `/src`
    * `/assets`: static documents
    * `/components`: reusable React components
    * `/contexts`: React contexts responsible for the state
    * `/hooks`: useful React hooks, most just wrappers on ROSlibjs library
    * `/pages`: page React components
    * `/utils`: other useful files

### Useful tools

* If you ever need to debug a React app, using the DevTools extension is useful ([Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi?hl=en) or [Firefox](https://addons.mozilla.org/en-CA/firefox/addon/react-devtools/))

## Debug

If you get a similar error

```
Error from chokidar (/home/.../dashboard/src/utils): Error: ENOSPC: System limit for number of file watchers reached, watch '/home/.../dashboard/src/utils/Provider.tsx
```

Run the following command to increase the limit of file watchers ([stackoverflow](https://stackoverflow.com/questions/55763428/react-native-error-enospc-system-limit-for-number-of-file-watchers-reached))

```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```