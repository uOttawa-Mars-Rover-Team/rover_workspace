t=ultralytics/ultralytics:latest-jetson-jetpack6

sudo docker pull $t && sudo docker run -it --ipc=host --runtime=nvidia -v $(pwd):/rover_workspace $t