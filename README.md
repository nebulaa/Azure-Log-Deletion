# Example-Azure-Log-Deletion-Script

## Overview

Example Python script to automate the process of deleting logs in Azure Log Analytics workspace.

The script can be query logs based on their email address and delete those logs for the purpose of GDPR compliance.

The script can also be used to check the status of a purge request.

## Purpose

The purpose of the script is to ensure that the applications hosted on Azure cloud environment is compliant with Art. 17 GDPR – Right to erasure ('right to be forgotten') regulation.

## Prerequisites

Before running the script, ensure that you have the following:

- Azure CLI installed and logged in with the appropriate credentials.
- Python 3.10 or higher installed on your system.
- The script requires the user to have the 'Data Purger' role in the subscription to delete logs.
- Modify the query in the main.py - `handle_get_logs` function to match your specific requirements.
- Modifythe filter in the main.py - `handle_delete_logs` function to match your specific requirements.

## Usage

To run the script, follow these steps:

1. Create a new Python virtual environment (venv) and activate it.

```
python3 -m venv venv
```

2. Install the required dependencies by running the following command in the terminal:

```
pip install -r requirements.txt
```

3. Run the script with the appropriate parameters:

- To get logs for a specific user:

```
python3 main.py --getlogs \
--starttime 2024-10-04-08-00-00 \
--endtime 2024-10-04-10-00-00 \
--workspaceid b152f67b-5678-408f-b708-8943264822d6,18328920-8765-4521-9aa5-2fe0aaec1c6b \
--useremail user@domain.com
```

- To delete logs for a specific user:

```
python3 main.py --deletelogs \
--starttime 2024-10-04-08-00-00 \
--endtime 2024-10-04-10-00-00 \
--subscriptionid 0e121138-80e8-1234-bacc-c7e0b3cd8aa \
--workspace workspace-name \
--resourcegroup rg-test \
--useremail user@domain.com
```
The purge request will be submitted and the purge ID will be saved to a file named `purgeid.txt`.

- To get the status of a purge request:

```
python3 main.py --status \
--subscriptionid 0e641138-90e8-1234-bacc-c7e0b3c8d8aa \
--workspace workspace-name \
--resourcegroup rg-test \
--purgeid purge-97380f07-1235-4a21-8ff7-cc092303662a
```

