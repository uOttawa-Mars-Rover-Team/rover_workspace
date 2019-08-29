# external_packages
ROS external packages are added via _git submodule_ and the list of external packages are located in the .gitmodules file at the root of this project.

## Add external package
To add an external package, use the git submodule CLI. You would use the following command and replace **git_link** with the link of the external package repository and **exernal_package_name** with the name of the external package.

<pre>
git submodule add <b>git_link</b> ~/rover_workspace/src/external_packages/<b>exernal_package_name</b>
</pre>

## Installing the external packages
To install the external packages, you will need to run the following command. This command needs to be run after you clone the repository or see that this folder only contains this file.

```
git submodule update
```

> Note: the previous command has already been run by the _[setup.sh](./../../scripts/setup.sh)_ script