import os
import requests
import re
from dotenv import load_dotenv
import pandas as pd
import tabula
load_dotenv()



def authWrapper(func):
    def inner(*args,**kwargs):
        authheader=zoho_workdrive_refresh()
        authheader.update({"Accept":"application/vnd.api+json"})
        return func(authheader=authheader,*args,**kwargs)
    return inner

def zoho_workdrive_refresh() -> dict:
    client_id = os.getenv("CLIENT_ID")
    refresh_token = os.getenv("REFRESH_TOKEN")
    client_secret = os.getenv("CLIENT_SECRET")
    
    url = f"https://accounts.zoho.com/oauth/v2/token?refresh_token={refresh_token}&client_secret={client_secret}&grant_type=refresh_token&client_id={client_id}"
    
    with requests.Session() as s:
        response = s.post(url)
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            return {"Authorization": "Zoho-oauthtoken " + access_token}
        else:
            
            return 401, "Error generating access token" 

@authWrapper
def download_file(resource_id: str,*args,**kwargs):
    
    url = f"https://download.zoho.com/v1/workdrive/download/{resource_id}"
    with requests.Session() as s:
        print(kwargs.get('authheader'))
        s.headers.update(kwargs.get('authheader'))
        print(url)
        
        response = s.get(url)
        
        print(response.status_code)
        
        if response.status_code == 200:
            pdf_name = re.findall(r"\w+(?=.pdf)",response.headers.get('Content-Disposition'))
            if pdf_name:
                pdf_name = pdf_name.pop()
            else:
                pdf_name = "Unknown"
            with open(f"{pdf_name}.pdf",'wb') as f:
                f.write(response.content)


@authWrapper
def get_file_details(resource_id:str,*args,**kwargs):
    url = f"https://www.zohoapis.com/workdrive/api/v1/files/{resource_id}"
    with requests.Session() as s:
        s.headers.update(kwargs.get('authheader'))
        response = s.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code,response.text)

def process_pdf(payroll_files: list()) -> list(pd.DataFrame):

    output = []
    for filename in payroll_files:
        print(filename)
        try:
            df_array = tabula.read_pdf(filename,pages='all',multiple_tables=False)
        except:
            df_array = tabula.read_pdf(filename,pages='all',multiple_tables=True)
        core = pd.DataFrame()
        for df in df_array:
            if not df.empty and 'Unnamed' not in df.columns:
                core = pd.concat([core,df],axis=0)

        

        core = core.reset_index(drop=True)
        columns_to_drop = []
        for name in core.columns:
            if 'Unnamed' in name:
                columns_to_drop.append(name)
            
        core = core.drop(columns=columns_to_drop).dropna(how='all')
        core.payroll_name = filename.name
        output.append(core)


    new_array = []
    for df in output:
        pay_name = df.payroll_name
        df = df.set_index(df.columns[0])
        df1 = df.apply(lambda x: x.apply(lambda x: x.replace("$", "").replace(",","")
                                        if
                                        hasattr(x, 'replace')
                                        else x))
        #df = df.apply(lambda x: x.apply())
        df1.payroll_name = pay_name                                
        new_array.append(df1)

        #df.apply(lambda x: x.apply(lambda x: x.replace('$','') if type(x) == str else x))


    summary_array = []
    for df in new_array:
        pay_name = df.payroll_name
        df1=df[df.apply(lambda x: x.apply(lambda x: any([i.isdigit() for i in x])))]
        
        df1.payroll_name = pay_name
        summary_array.append(df1)
        
        
        
    agg_array = []

    for df in summary_array:
        pay_name = df.payroll_name
        df1 = df.apply(lambda x: x.apply(lambda x: float(x))).groupby(
            'Employee Name'
        ).agg('sum')
        df1.payroll_name = pay_name
        agg_array.append(df1)


    return agg_array



