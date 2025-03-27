import subprocess
import sys
import bpy

# install packages
package_name = 'pandas'  # Replace 'requests' with the package you want to install

# Installing the package
subprocess.check_call([sys.executable, '-m', 'ensurepip'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

# Check if the package is installed correctly
try:
    import requests  # Replace 'requests' with the package you installed
    print(f"'{package_name}' installed successfully.")
except ImportError:
    print(f"Failed to install '{package_name}'.")