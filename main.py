import argparse
from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
import pandas as pd
from azure.core.exceptions import HttpResponseError

def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--getlogs", action="store_true", help="Get logs")
    group.add_argument("--deletelogs", action="store_true", help="Delete logs")
    group.add_argument("--status", action="store_true", help="Get the status of deletion request")

    parser.add_argument("--subscriptionid", type=str, help="Subscription id")
    parser.add_argument("--workspace", type=str, help="Log Analytics workspace name")
    parser.add_argument("--resourcegroup", type=str, help="Resource group name")
    parser.add_argument("--starttime", type=str, help="Start time in yyyy-mm-dd-hh-mm-ss format (UTC)")
    parser.add_argument("--endtime", type=str, help="End time in yyyy-mm-dd-hh-mm-ss format (UTC)")
    parser.add_argument("--useremail", type=str, help="User email")
    parser.add_argument("--workspaceid", type=str, help="Add comma separated Log Analytics workspace ids")
    parser.add_argument("--purgeid", type=str, help="Add comma separated purge ids")

    return parser.parse_args()

def validate_datetime_format(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d-%H-%M-%S')
    except ValueError as e:
        print(f"Invalid date format for {date_str}: {e}")
        exit()
        
def convert_to_iso_format(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')

def get_credential():
    return DefaultAzureCredential()

def handle_get_logs(args, credential):
    if not all([args.starttime, args.endtime]):
        print("ERROR: Please provide all required parameters for getting logs.")
        print("Usage: python3 main.py --getlogs --starttime <starttime> --endtime <endtime> --workspaceid <workspaceid> --useremail <useremail>")
        exit()

    client = LogsQueryClient(credential)
    starttime = validate_datetime_format(args.starttime).replace(tzinfo=timezone.utc)
    endtime = validate_datetime_format(args.endtime).replace(tzinfo=timezone.utc)
    
    if args.workspaceid is None or args.useremail is None:
        print("Please provide workspace id(s) and user email.")
        exit()
    
    workspaceid = args.workspaceid.split(",")
    #Modify the query based on your log format.
    query = f"""AppEvents | where tostring(Properties["email"]) =~ "{args.useremail}" """
    
    run_queries(client, workspaceid, query, starttime, endtime)

def run_queries(client, workspaceids, query, starttime, endtime):
    total_rows = 0
    for workspaceid in workspaceids:
        try:
            response = client.query_workspace(workspace_id=workspaceid, query=query, timespan=(starttime, endtime))
            
            if response.status == LogsQueryStatus.SUCCESS:
                data = response.tables
            else:
                print(response.partial_error)
                data = response.partial_data

            for table in data:
                df = pd.DataFrame(data=table.rows, columns=table.columns)
                print(f"Logs in Workspace ID: {workspaceid}\n")
                print(df.loc[:, ['TimeGenerated', 'Name', 'OperationName']])
                total_rows += len(df)
                
        except (HttpResponseError, Exception) as err:
            print("Error:", err)

    print(f"\nTotal rows with user data: {total_rows}\n")

def handle_delete_logs(args, credential):
    if not all([args.subscriptionid, args.workspace, args.resourcegroup, args.starttime, args.endtime, args.useremail]):
        print("ERROR: Please provide all required parameters for deleting logs.")
        print("Usage: python3 main.py --deletelogs --subscriptionid <subscriptionid> --workspace <workspace> --resourcegroup <resourcegroup> --starttime <starttime> --endtime <endtime> --useremail <useremail>")
        exit()
    
    client = LogAnalyticsManagementClient(credential, subscription_id=args.subscriptionid)
    starttime = convert_to_iso_format(validate_datetime_format(args.starttime))
    endtime = convert_to_iso_format(validate_datetime_format(args.endtime))
    
    try:
        response = client.workspace_purge.purge(
            resource_group_name=args.resourcegroup,
            workspace_name=args.workspace,
            #Modify the filters based on your log format.
            body={
                "filters": [
                    {"column": "TimeGenerated", "operator": ">", "value": starttime},
                    {"column": "TimeGenerated", "operator": "<", "value": endtime},
                    {"column": "Properties", "key": "email", "operator": "=~", "value": args.useremail},
                ],
                "table": "AppEvents",
            },
        )
        
        response_purgeid = response.operation_id
        append_to_file("purgeid.txt", response_purgeid + "\n")
        print(f"Purge request submitted. Purge ID: {response_purgeid}\n")
        
    except (HttpResponseError, Exception) as err:
        print("Error:", err)

def append_to_file(filename, text):
    print(f"Saving purge id to {filename} file...")
    with open(filename, "a") as f:
        f.write(text)

def handle_status(args, credential):
    if not all([args.purgeid, args.subscriptionid, args.workspace, args.resourcegroup]):
        print("ERROR: Please provide all required parameters for checking the status.")
        print("Usage: python3 main.py --status --subscriptionid <subscriptionid> --workspace <workspace> --resourcegroup <resourcegroup> --purgeid <purgeid>")
        exit()
    
    client = LogAnalyticsManagementClient(credential, subscription_id=args.subscriptionid)
    purgeids = args.purgeid.split(",")

    for purgeid in purgeids:
        try:
            response = client.workspace_purge.get_purge_status(
                resource_group_name=args.resourcegroup,
                workspace_name=args.workspace,
                purge_id=purgeid,
            )
            print(f"Purge ID: {purgeid}, Status: {response.status}\n")
        
        except (HttpResponseError, Exception) as err:
            print("Error:", err)

def main():
    print("\n INFO: Run 'az login' before running this script.\n")
    args = parse_args()
    credential = get_credential()

    if args.getlogs:
        handle_get_logs(args, credential)
    elif args.deletelogs:
        handle_delete_logs(args, credential)
    elif args.status:
        handle_status(args, credential)

    print("Operation completed. Exiting...")

if __name__ == "__main__":
    main()