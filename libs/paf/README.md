# IGNORE INSTRUCTIONS - old

# To install:

1. Setup the venv
```bash
pipenv --three
```

2. In `trader/paf`, run:
```bash
pipenv shell
pipenv install
```

# Dev Workflow

Follow the workflow outlined in https://github.com/nayefc/trader_ops/tree/master/deploy.

1. Sync code as you develop:
From trader/ run:
```bash
~/path/to/trader_ops/deploy/watch_project
```

2. Compile C++ binary
On the server:
```bash
cd ~/trader/bin
make -j2 python_bitmex
```

3. Run the C++ binary
On the server:
```bash
./python_bitmex -c ../trader.cfg
```

4. Run the python code
In a different tmux pane/window or terminal tab/window:
```bash
 ./paf.py <STRATEGY_FILE_NAME>
```

So for example, we have a basic.py strategy file:
```bash
 ./paf.py basic
```

# Installing Packages

To install packages, it is recommended you follow the following steps:

1. Make sure your `watch_project` is running so you can sync the package changes from your local Mac to the server

2. Install the package on your local Mac:
```bash
cd trader/paf
pipenv install <PACKAGE>
```
This will update Pipfile. If you're running `watch_project`, you'll automatically have your Pipfile synced to the server. If not, run `sync_project` to update the Pipfile on the server.

3. Commit the Pipfile changes

4. On the server, update pipenv with the latest Pipfile changes (the new package):
```bash
pipenv sync
```

# Updating Packages
``` bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
ssh -A dev
ssh -T git@github.com
pipenv sync
```
