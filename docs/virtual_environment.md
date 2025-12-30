
# Setup and Use Python Virtual Environment

It is HIGHLY encourage to use a Python Virtual Environment to run this application in for easier management and less likely concern for any form of application library conflicts and issues.

- NOTE:  This is setup in Python 3.x

## Initial setup of Virtual Environment

Change to directory
   ```bash
   cd local_llm_framework
   ```

Create Python virtual environment
   ```bash
   python -m venv llf_venv
   ```
NOTE:  The create virtual environment will be stored in a directory called `llf_venv`

## Start / Use Virtual Environment

Change to directory
   ```bash
   cd local_llm_framework
   ```

Change over to the virtual environment
   ```bash
   source llf_venv/bin/activate
   ```
   NOTE:  Remember to always be in the virtual environment

## Verify if you are in Virtual Environment

Verify you are in the virtual environment
   ```bash
   echo $VIRTUAL_ENV
   ```
If the above command returns "nothing", then you are not running in a virtual environment.

Another option to check if you are in the virtual environment
   ```bash
   python -c "import sys; print(sys.prefix != sys.base_prefix)"
   ```
NOTE:  If the above command returns "True" then you are in a Virtual Environment

## Exit the Virtual Environment

Exit the Virtual Environment
   ```bash
   deactivate
   ```





