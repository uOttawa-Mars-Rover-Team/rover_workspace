<div align="center">
  <img src="docs/logo.png">
</div>

# uOttawa Rover Workspace [![](https://gitlab.com/uorover/rover_workspace/badges/master/pipeline.svg)](https://gitlab.com/uorover/rover_workspace/pipelines)

uoRover development workspace. Currently using ROS2 Humble.

## Installing docker container

0. Install [docker](https://www.docker.com) on your machine

1. Run the command on terminal:
    ```bash
    docker compose up -d
    ```

- **Note: this must be run from the directory containing docker-compose.yal, which is located in the current branch at the time of writing.**

</br>

2. Start rover workspace from terminal:
    ```bash
    docker exec -it rover_ws bash
    ```
    ![](/docs/screenshot_1.png)
    
3. Make sure the packages are up to date:
    ```bash
    sudo apt-get update
    ```

4. Change to directory "rover_workspace":
    ```bash
    cd ~/rover_workspace
    ```

5. Install dependencies:
    ```bash
    rosdep install --from-paths src --ignore-src -r -y
    ```

6. Build ROS packages on directory "rover_workspace":
    ```bash
    colcon build
    ```