import boto3
from datetime import datetime
import os
import csv

def get_users():
    is_truncated = True
    marker = None
    user_list = []
    while is_truncated != False:
        if marker == None:
            response = iam.list_users(
            )
        else:
            response = iam.list_users(
                Marker=marker
            )

        if "Marker" in response:
            marker = response["Marker"]
        else:
            marker = None

        if "IsTruncated" in response:
            is_truncated = response["IsTruncated"]
        else:
            is_truncated = False
       
        for a in response["Users"]:
           
            user_dict = {}
            user_dict["UserName"] = a["UserName"]
            user_dict["CreateDate"] = convert_datetime(a["CreateDate"])

            if "PasswordLastUsed" in a:
                user_dict["PasswordLastUsed"] = convert_datetime(a["PasswordLastUsed"])
                user_dict["PasswordAge"] = days_old(a["PasswordLastUsed"])
            else:
                user_dict["PasswordLastUsed"] = "n/a"
                user_dict["PasswordAge"] = "n/a"

            user_dict["MfaEnabled"] = list_mfa_devices(a["UserName"])
            

            access_keys = get_access_keys(a["UserName"])

            for b in access_keys:
                index = str(access_keys.index(b))
                
                user_dict["AccessKeyId" + index] = b["AccessKeyId"]
                user_dict["Status" + index] = b["Status"]
                user_dict["CreateDate" + index] = convert_datetime(b["CreateDate"])
                user_dict["DaysOld" + index] = days_old(b["CreateDate"])

            for b in [0,1]:
                index = str([0,1].index(b))
                if ("AccessKeyId"+ index) not in user_dict:
                    user_dict["AccessKeyId" + index] = "n/a"
                    user_dict["Status" + index] = "n/a"
                    user_dict["CreateDate" + index] = "n/a"
                    user_dict["DaysOld" + index] = "n/a"
                
            user_list.append(user_dict)
    return user_list

def convert_datetime(date_src):
    timestampStr = date_src.strftime("%Y/%m/%d %H:%M")
    return timestampStr
def get_access_keys(username):
    response = iam.list_access_keys(
        UserName=username,
    )
    
    return response["AccessKeyMetadata"]
def get_password_profile(username):
    try:

        response = iam.get_login_profile(
            UserName=username
        )
        print(response)
        return days_old(response["LoginProfile"]["CreateDate"])
    except:
        return "disabled"
    
def days_old(date_src):
    return (datetime.today() - date_src.replace(tzinfo=None)).days

def list_mfa_devices(username):
    
    response = iam.list_mfa_devices(
        UserName=username
    )
    if response["MFADevices"] != []:
        mfa_enabled = "True"
    else:
        mfa_enabled = "False"
    
    return mfa_enabled

def get_account_info():
    response = iam.list_account_aliases()
    if response["AccountAliases"] != []:
        return response["AccountAliases"][0]
    else:
        return boto3.client('sts').get_caller_identity().get('Account')

def write_csv(data):
    csv_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"iam_audit.csv")
    keys = data[0].keys()
    
    with open(csv_file, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    
if __name__ == "__main__":
    user_list_merged = []
    for aws_account in ["dev","test","qa","prod"]:
        session = boto3.Session(region_name="eu-west-1",profile_name=aws_account)
        iam = session.client("iam")
        account_id = get_account_info()
        for a in get_users():
            a["AwsAccount"] = get_account_info()
            user_list_merged.append(a)
    write_csv(user_list_merged)

