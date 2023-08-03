import os
import pandas as pd
import json
import io
import copy
import numpy as np
import model

def rec_get_sheets(data,sheet,sheet_data,converter,fk_str,fks_old=None):
    
    for entry in data:
        if fks_old==None:
            fks = []
        else:
            fks = copy.deepcopy(fks_old)
        sub_fk = []
        l = fk_str.split(',')
        for i in l:
            p = i.split('.')
            val = entry.get(p[0],{})
            if isinstance(val,list):
                sub_fk.append('.'.join(p[1:]))
            else:
                key = p[0]
                if val:
                    fks.append({'key':key,'val':val})
                else: 
                    fks.append({'key':key,'val':'error'})
        
        sub_fk = ','.join(sub_fk)
        if entry.get(sheet,False):

            sub_entries = entry.pop(sheet)
            for sub in sub_entries:
                for fk in fks:
                    sub[fk['key']]=fk['val']
                sheet_data.append(converter(sub))
        else:
            for k,v in entry.items():
                if isinstance(v,list):

                    rec_get_sheets(v,sheet,sheet_data,converter,sub_fk,fks)
                    

def export_to_excel(db):
    db = copy.deepcopy(db)
    sheets = {}
    for sheet in db.sheets:
        sheets[sheet]=[]
    for i,(k,v) in enumerate(sheets.items()):

        rec_get_sheets(db.data,k,v,db.out_converters[i],db.fk[i])

    main = pd.DataFrame(db.data)
    for k,v in sheets.items():
        sheets[k]=pd.DataFrame(v)

    file = io.BytesIO()
    with pd.ExcelWriter(file) as writer:
        main.to_excel(writer,db.name,index=False)
        for k,v in sheets.items():
            sheets[k].to_excel(writer,k,index=False)

    file.seek(0,0)
    return file

def import_from_excel(file,db):
    if isinstance(file,io.BytesIO):
        input_file = file
    else:
        input_file = file.stream._file

    main = excel_safe_load(input_file,db.name,db.na_values[0],db.types[0])

    # Load all DataFrames before merging. doesn't necessarily need to be reversed
    sheets = {}
    fks = {}
    depth = 0
    for i,sheet in enumerate(reversed(db.sheets)):
        ind = -(i+1)

        temp = excel_safe_load(
            input_file,
            sheet,
            db.na_values[ind],
            db.types[ind],
            db.in_converters[ind]
        )

        sheets[sheet]=temp
        key_list = db.fk[ind].split(',')
        for key in key_list:
            depth=max(len(key.split('.')),depth)
        fks[sheet]=key_list

    # Last key in Fks is always the merge key. Iteratively merge all sheets
    for i in range(depth):
        for k,v in sheets.items():
            key_list = fks[k]
            depth_i = len(key_list[-1].split('.'))
            if not depth_i==depth:
                continue
            if depth==1 and db.pk in key_list[-1]:
                main = df_dict_merge(k,v,main,key_list)
                continue

            keys = key_list[-1].split('.')
            parent = sheets[keys[-2]]
            parent = df_dict_merge(k,v,parent,key_list)
            sheets[keys[-2]]=parent
        depth-=1

    db.data=list(main.to_dict('index').values())
    

    return db

def df_dict_merge(sheet,child,parent,key_list):
    
    # Get main foriegn key, drop the rest
    main_fk = key_list.pop()
    for key in key_list:
        child = child.drop(key.split('.')[-1],axis=1)

    # Get fields unique to this sheet
    sub_keys = main_fk.split('.')   
    fields = list(child.columns)
    fields.remove(sub_keys[-1])
    
    # Make sure parent and childe have unique name spaces
    parent_fields = list(parent.columns)
    for field in fields:
        if field in parent_fields:
            child = child.rename(columns={field:f'{sheet}.{field}'})

    # Redefine child field after any renaming
    fields = list(child.columns)
    fields.remove(sub_keys[-1])

    # merge child and parent into a family
    family = pd.merge(parent,child,'left',on=sub_keys[-1])

    # Reformat so that child is a list of dicts in parent dataframe
    grp = family.set_index(sub_keys[-1]).groupby(sub_keys[-1])[fields]
    dict_list = []
    for name,group in grp:

        # revert renames if any occured
        for field in fields:
            if '.' in field:
                field = field.split('.')[-1]
                group = group.rename(columns={f'{sheet}.{field}':field}) 

        dict_list.append({sub_keys[-1]:name,sheet:group.to_dict('records')})

    # Return final DF
    temp_df = pd.DataFrame(dict_list)
    merged_parent = pd.merge(parent,temp_df,'left',on=sub_keys[-1])
    return merged_parent

def excel_safe_load(
        file,
        sheet,
        nan_dict,
        type_dict,
        converters=None,
        ignore=False
    ):

    if converters==None:
        converters = {}

    # Pre-load xl to get info about safe importing
    df = pd.read_excel(
        file,
        sheet,
        na_values='-'
    )
    
    # Get relevant fields if imported data isn't doesn't contain all fields. Also
    # check if there are unexpected columns
    fields = list(df.columns)
    type_subset = {}
    nan_subset = {}
    for field in fields:
        if type_dict.get(field,False):
            type_subset[field]=type_dict.get(field)
            nan_subset[field]=nan_dict.get(field)
        else:
            if ignore:
                continue
            raise Exception(f'column \"{field}\" is an unrecognized field in {sheet} sheet')
    
    # Load xl with safety
    try:
        df = pd.read_excel(
            file,
            sheet,
            na_values='-'
        ).fillna(nan_subset).astype(type_subset)
        return df
    except Exception as e:
        print(e.with_traceback)
        raise Exception(f'One or more columns in {sheet} contain values that are unconvertable by either custom converters or type definitions')


if __name__ == '__main__':
    db = model.Signal(
        [{
            'cog_id':1,
            'ip':1,
            'name':1,
            'street':1,
            'zip_code':1,
            'signal_system':1,
            'cut_service_id':1,
            'cut_id':1,
            'modem_online':1,
            'controller_online':1,
            'controller_status':1,
            'updated_at':1,
            'n_ccu':1,
            'n_matrix':1,
            'n_advance':1,

            'meters':[
                {
                    'esi_id':10,
                    'comment':10,
                    'oncor_address':10,
                    'address_sim':10,
                    'status':10,
                    'bbu':10,
                    'owner':10,
                    'pole_num':10,
                    'checked':10,
                    'number':10,
                    'online_status':10,
                }
            ],
            'radar_ccus':[
                {
                    'serial':123,
                    'mac':123,
                    'port':123,
                    'version':123,
                    'name':123,

                    'sensors':[
                        {
                            'channels':[True,True,False],
                            'name':'foo',
                            'type':1,
                            'id':1,
                            'serialNumber':1,
                            'location':1,
                            'description':1,
                            'approach':1,
                            'port':1,
                        },
                        {'channels':[True,True,True],'name':'bar'}
                    ]
                    
                },
                {
                    'serial':348,
                    'mac':114723,
                    'sensors':[
                        {'channels':[True,True,False],'name':'baz'},
                        {'channels':[True,True,True],'name':'test'}
                    ]
                    
                },
            ]
        }]
    )

    print(import_from_excel(export_to_excel(db),model.Signal()).data)