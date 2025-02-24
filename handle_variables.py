import pandas as pd
import time
from datetime import datetime
from classes import RequestLog
from config import Config as config
import Google as drive
import asyncio
    
async def add_account(name : str, api_key : str, api_secret : str):
    # Download the .csv files from Google Drive
    # service = await asyncio.create_task(drive.Create_Service())
    # await asyncio.create_task(drive.Download_File(service, config.DRIVE_FILE_NAME_ACCOUNTS))

    accounts = pd.read_csv(f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', sep=',')
    
    if name in accounts['api_name'].unique():
        return f'Account with that name ({name}) already exists.'

    new_account = pd.DataFrame({
        'api_name' : [name], 
        'api_key' : [api_key], 
        'api_secret' : [api_secret]
    })

    # Update Local Version
    accounts = pd.concat([accounts, new_account], axis=0, ignore_index=True)
    accounts.to_csv('./database/accounts.csv', index=False)
    accounts.to_csv(f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', index=False)

    # # Upload Changes to Drive
    # await asyncio.create_task(drive.Upload_File(service, config.DRIVE_FOLDER_NAME, config.DRIVE_FILE_NAME_ACCOUNTS, \
    #     f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', 'csv'))
    
    return f'Account ({name}) added.'

async def remove_account(name : str):
    # Download the .csv files from Google Drive
    # service = await asyncio.create_task(drive.Create_Service())
    # await asyncio.create_task(drive.Download_File(service, config.DRIVE_FILE_NAME_ACCOUNTS))

    accounts = pd.read_csv(f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', sep=',')

    if name not in accounts['api_name'].unique():
        return f'Account with that name ({name}) does not exist.'

    accounts = accounts[accounts['api_name'] != name]
    accounts.to_csv('./database/accounts.csv', index=False)
    accounts.to_csv(f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', index=False)

    # # Upload Changes to Drive
    # await asyncio.create_task(drive.Upload_File(service, config.DRIVE_FOLDER_NAME, config.DRIVE_FILE_NAME_ACCOUNTS, \
    #     f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', 'csv'))

    return f'Account ({name}) removed.'

def get_accounts():
    accounts = pd.read_csv('./database/accounts.csv', sep=',')
    dict_accounts = accounts.to_dict()

    list_accounts = []
    list_accounts_safe = []

    for index in range(accounts.shape[0]):
        name = dict_accounts['api_name'][index]
        key = dict_accounts['api_key'][index]
        secret = dict_accounts['api_secret'][index]

        list_accounts.append((name, key, secret))
        list_accounts_safe.append((name, key))

        list_accounts.sort()
        list_accounts_safe.sort()

    return list_accounts, list_accounts_safe

def add_log(log : RequestLog, management=False):
    log_file = './database/logs.csv' if (not management) else './database/management_logs.csv'
    logs = pd.read_csv(log_file, sep='|')
    
    new_log = log.getLog()
    timestamp = new_log['timestamp'] 
    command = new_log['command'] 
    response = new_log['response'] 

    new_log = pd.DataFrame({
        'timestamp' : [timestamp], 
        'command' : [command], 
        'response' : [response]
    })

    logs = pd.concat([new_log, logs], axis=0, ignore_index=True)
    logs.to_csv(log_file, index=False, sep='|')
    
    return 

def get_logs():
    logs = pd.read_csv('./database/logs.csv', sep='|')
    # logs['timestamp'] = pd.to_datetime(logs['timestamp'], unit='s') # Convert Integer timestamp to datetime

    dict_logs = logs.to_dict()

    list_logs = []

    for index in range(logs.shape[0]):
        timestamp = dict_logs['timestamp'][index]
        command = dict_logs['command'][index]
        response = dict_logs['response'][index]

        list_logs.append((datetime.fromtimestamp(int(timestamp/1000)).strftime('%Y-%m-%d %H:%M:%S'),
         command, response))
    return list_logs[:20]

async def update_database(accounts_only : bool = False):
    # Download the .csv files from Google Drive
    service = await asyncio.create_task(drive.Create_Service())
    await asyncio.create_task(drive.Download_File(service, config.DRIVE_FILE_NAME_ACCOUNTS))
    await asyncio.create_task(drive.Download_File(service, config.DRIVE_FILE_NAME_LOGS))

    # Merge The Dataframes
    df_local_accounts = pd.read_csv('./database/accounts.csv', sep=',')
    df_local_logs = pd.read_csv('./database/logs.csv', sep='|')

    df_drive_accounts = pd.read_csv('./database/drive_accounts.csv', sep=',')
    df_drive_logs = pd.read_csv('./database/drive_logs.csv', sep='|')

    df_accounts_merged = merge_df(df_local_accounts, df_drive_accounts)
    df_logs_merged = merge_df(df_local_logs, df_drive_logs)

    # Save Merged Documents
    df_accounts_merged.to_csv('./database/accounts.csv', index=False)
    df_accounts_merged.to_csv('./database/drive_accounts.csv', index=False)
    df_logs_merged.to_csv('./database/logs.csv', index=False, sep='|')
    df_logs_merged.to_csv('./database/drive_logs.csv', index=False, sep='|')
    
    # Upload Updated Database
    upload_accounts = asyncio.create_task(drive.Upload_File(service, config.DRIVE_FOLDER_NAME, config.DRIVE_FILE_NAME_ACCOUNTS, \
        f'./database/{config.DRIVE_FILE_NAME_ACCOUNTS}', 'csv'))

    upload_logs = asyncio.create_task(drive.Upload_File(service, config.DRIVE_FOLDER_NAME, config.DRIVE_FILE_NAME_LOGS, \
        f'./database/{config.DRIVE_FILE_NAME_LOGS}', 'csv'))

    await asyncio.wait([upload_accounts, upload_logs])

def merge_df(df1, df2):
    return pd.concat([df1, df2]).drop_duplicates()
