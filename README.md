# oncor-status-updater
A simple program to update the status of oncor equipment



### Steps to just run `threaded_update.py` and not the rest of the app:
- Copy the repository and set up a virtual environment
- Create a `.env` file for environment variables or replace calls to environment variables in the program. This will mainly be found in `controller_snmp.py`
- Add a data folder and include the json containing signal/powermeter data
- Change the file path under `if __name__ == '__main__'` to the file path of the data you just inserted 


### Steps for installing and running python files
#### Prerequisites for installation
- python 3.10

### Steps for installing and running executable
#### Prerequisites for installation
- Windows
- x86 processor
