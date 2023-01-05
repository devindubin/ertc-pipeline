
import os
import tabula
import pandas as pd
from flask import Flask, request
import io
from 



app = Flask(__name__)

@app.route('/upload',methods=['GET','POST'])
def upload_process_pdf():
    if request.method == 'POST':
        doc = request.files.get('file')
        return process_pdf([doc])
        
    else:
        return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


# payroll_files = []
# for root, dirs, files in os.walk('payrollexamples/'):
#     for file in files:
#         if 'payroll' in file:
#             payroll_files.append(os.path.join(root,file))

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



