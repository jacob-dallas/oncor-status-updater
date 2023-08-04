# oncor-status-updater
A simple program to update the status of oncor equipment



### Steps to just run `threaded_update.py` and not the rest of the app:
- Copy the repository and set up a virtual environment
- Create a `.env` file for environment variables or replace calls to environment variables in the program. This will mainly be found in `controller_snmp.py`
- Add a data folder and include the json containing signal/powermeter data
- Change the file path under `if __name__ == '__main__'` to the file path of the data you just inserted 


### Steps for installing and running python files
#### Prerequisites for installation
- [python 3.10][1]
- [git][2]
[1]: https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5
[2]: https://git-scm.com/downloads

#### Steps for Installation
1. Download the repository either through git or from github. If you download with git, simply type `git clone git@github.com:jacob-dallas/oncor-status-updater.git` (if you are using ssh). If you download the zip file, extract it somewhere you can easily find.

2. Once the code has been downloaded through git or from github, navigate to that folder in you preferred terminal and run `python -m venv .venv`, where `.venv` can be whatever you wish. 

3. Once this is complete, activate the virtual environment. If you are using powershell on windows, this can be done by entering `.\.venv\Scripts\Activate.ps1`

4. Install the projects depedencies by running `pip install -r requirements.txt`. At this point, you can run app.py and the program will run in an unconfigured mode. Please follow the next set of steps for configuration.

#### Steps for configuration
In general, configuration will include setting up environment variables, providing databases, and providing any certificates that might be needed for TLS.
##### Setting up Environment variables
The app will look for a .env file in the folder signified by python's APPDATA variable. If you have already ran app.py, it will have copied .env-template into this directory as .env, but it will be unconfigured. To find this folder and modify .env, start an instance of the python interpreter and run the following commands.

1. `import os`
2. `os.path.realpath(os.getenv('APPDATA'))`

For python installations downloaded from the python website, the displayed path will be the normal appdata path, but if python was download from the microsoft store or some other repository, it could be in a strange place.

Navigating to this folder will show you its contents, including a log folder, two json databases, and a .env file. Open the .env file in any text editor to configure it. The most important variables to set are:
- IP: set equal to the internal or external IP you want the server to be hosted on
- PORT: the port for the server
- COMMUNITY: This has to do with communicating with controllers through SNMP. If you controller supports this, provide an acceptable community name for communication with it.
- SNMPVER: The version of SNMP your traffic signal controllers use.
- CERT_PATH: If you need to provide a certificate for http requests, put the path to it here. Otherwise, leave blank
- CP_USER: Cradlepoint username for communication with modems. If you do not use cradlepoint modems or dont plan to use the modem portal, ignore this.
- CP_PASS: Cradlepoint password for communication with modems. If you do not use cradlepoint modems or dont plan to use the modem portal, ignore this.

##### Setting up Databases
Databases can either be set up by copying the json format provided in the database templates or by using the app's import from excel feature. To determine the format required by for an excel document, first use the export to excel feature, and it will generate a template for either database.

There are two databases used in this application: the main database `db.json` and the modem database `modem_db.json`. The main database has a unique ID for each traffic signal. This id is the COG_ID. This value is used as the primary key of the database. This database contains information on the traffic signal's power meters and radar brains, which both have a many-to-one relationship with the traffic signals, The modem database uses IP addresses as primary keys because this app can change which signal is associated with each IP. 


### Generally how this application works
This application employs a server-client architecture, where the server and the
client can be the same machine. The server handles mostly all requests to external 
sources of information, like oncor's database, radar brains, or traffic signal controlers. The client is responsible for user interface. When you click on something on the user interface, the client side will process your click and may or may not communicate with the server to get any necessary information. 

The main function of this application is to grab information from external sources and display it all in one centralized place. It does this quickly by employing multiple threads to generate multiple requests for information at once. Each thread makes a request for a given resource (power outage information) and waits for a response. The fact that each thread must wait for a network response makes this thread-based approach efficient. The server's main job is to run these threads and provide the information, when requested, to the client/user interface.

Overall, this application can have up to 3 instances of the same database and synchronizes them regularly. One instance resides on the file system in the folder designated by Python's APPDATA variable. One instance resides in memory while the server is running, and one instance resides on the client while the user is in one of the portals. When on the main page, there is no database on the client, the client database is only available when in one of the portals. 

Threads may have to be specially configured to work with other systems. These threads were designed to work with a remote modem network that establishes a lan network with all devices at a signalized intersection.

For more information on the specific implementation of these threads and user interface, look at the source code.

### How to Use This Application
After the program has been installed and configured, you can start to gather information. To start gathering information, you can click the start buttons on one of the portals. This will cause a window to appear and lets you configure how you want to gather information. There is a simple run option, and a complex run option. The simple run option lets you decide how many threads to use while updating and lets you export recordings to the configured directory. Keep in mind the application will need permission to write in any directory you selected in configuration. Additionally, you shouldn't select too many threads. At some point, more threads will make the information gathering slower because of each thread's overhead. The optimal number of threads will depend on the power of the machine running it's network speed/response times. The Advanced option adds the ability to run the threads for a specified amount of time, whereas the simple case runs indefinitely until manually stopped. 

Once the threads have been started, they will continuously iterate through the database provided during configuration. To view the status of these updates, click the "Go" button on the respective portal. On this page, you will see a list of filters to the left that can be selected, and clicking each column header will sort by it. You can perform advanced sorts by clicking one header, then the next. This will sort entries first by the first clicked header, and then if there are any in the first column that match, the entries that match will be sorted by the second clicked header. The search box can be used to isolate entries by name, COG ID, ESI ID, or IP. The import and export buttons can be used to interact and change the database.

Each portal may have special features. The radar portal was designed so that each entry is clickalbe. Clicking an entry brings up a window with more information about that entry, such as the number of CCU's found and sensors belonging to them. Also displayed on this page is the number of CCU's and radar panels expected to be found at the respective intersection. By using this, you can determine if some radar panels or CCU's are not communicating.

The modem portal has features that allow you to view and configure port-forwarding tables. Simply click the view button to examine licenses, connected clients, and open ports. From here ports can be added, deleted, edited and viewed.