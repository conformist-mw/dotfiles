import os
import subprocess


def install_requirements():
    req_file = "/tmp/requirements.txt"
    if os.path.exists(req_file):
        print(f"Installing dependencies from {req_file}...")
        subprocess.run(["pip", "install", "-r", req_file], check=True)
    else:
        print("No requirements.txt found, skipping installation.")


c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.open_browser = False
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.notebook_dir = "/home/jovyan/work"

# disable unused kernels
c.MappingKernelManager.cull_idle_timeout = 60 * 20  # 20 minute
# disable even if the browser tab is open
c.MappingKernelManager.cull_connected = True
# do not disable on long-running tasks
c.MappingKernelManager.cull_busy = False

install_requirements()
