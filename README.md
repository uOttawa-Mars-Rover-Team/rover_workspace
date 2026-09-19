<div align="center">
  <img src="docs/logo.png">
</div>

# uOttawa Rover Workspace [![](https://gitlab.com/uorover/rover_workspace/badges/master/pipeline.svg)](https://gitlab.com/uorover/rover_workspace/pipelines)

uORover development workspace. Currently using ROS2 Jazzy 

## Getting Started (Docker Dev Container - Recommended)

The workspace ships with a [dev container](.devcontainer) that builds a ROS2 Jazzy image with all required dependencies, so you don't need to install ROS or manage a VM yourself.

1. Install [Docker](https://docs.docker.com/get-docker/) (or Docker Desktop on Windows/Mac) and [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
2. Clone this repository: `git clone https://gitlab.com/uorover/rover_workspace.git`
3. Open the cloned folder in VS Code, then run **Dev Containers: Reopen in Container** from the command palette (`Ctrl+Shift+P`). This builds the image from `.devcontainer/Dockerfile` and installs any remaining ROS dependencies automatically via `postCreateCommand`.
4. Once the container is up, build our ROS packages from the integrated terminal: `colcon build`
5. Open a new terminal window (to automatically source the setup script). Now you can use the ROS packages in this repo (using commands like `ros2 run`, `ros2 launch`, etc.)!

Make sure to repeat steps 4-5 to rebuild the code after making changes.

Notes:
- The container forwards ports for Foxglove Bridge (`8765`), a web desktop via noVNC (`6080`), and the dashboard (`3000`, `5173`).
- `build/`, `install/`, `log/`, and `.ccache/` are mounted as named Docker volumes so they persist across container rebuilds without touching your host filesystem.
- On Windows/macOS, X11 GUI apps (e.g. RViz) are forwarded through the noVNC web desktop at `http://localhost:6080` (DISPLAY=:1); on native Linux or WSLg they can also render directly (DISPLAY=:0)

## Getting Started (Manual / Native Install)

If you'd rather not use Docker, you can still set up ROS2 directly on a Linux machine or VM.

1. Create a Ubuntu 24.01 LTS virtual machine or dual boot your computer.
2. Install git on your machine `sudo apt install git`
3. Clone this repository at your home location `cd ~ && git clone https://gitlab.com/uorover/rover_workspace.git`
4. Run the setup script with `cd ~/rover_workspace/scripts && ./full_setup.sh`
5. Build our ROS packages. Open a new terminal window and run the following: `cd ~/rover_workspace && colcon build`
6. Open a new terminal window (to automatically source the setup script). Now you can use the ROS packages in this repo (using commands like `ros2 run`, `ros2 launch`, etc.)!

Make sure to repeat steps 5-6 to rebuild the code after making changes.

## Dashboard

The web dashboard (`src/dashboard`) has its own Docker Compose setup, independent of the main dev container. From `src/dashboard`, run `docker compose up --build` to build and serve it on `http://localhost:5173`.

## New Features

As we add new features to the build keep new developments on a seperate branch from the master. This way the master branch will
stay functional while we work on individual systems.

## Installing New Project Dependencies

To install any new dependencies added to this workspace, you can run the following command at the root of the workspace at any point in time:

```bash
rosdep install --from-paths src -i -r -y
```
