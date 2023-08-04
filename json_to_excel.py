import os
import pandas as pd
import json
import io
import copy
import numpy as np
import model

def rec_get_sheets(data,sheet,sheet_data,converter,fk_str,parent,fks_old=None):
    # compensates for one-to-one relationships
    if isinstance(data,dict):
        data=[data]
    
    # for every entry in the spreadsheet, add it to the sheet data
    for entry in data:
        if isinstance(entry,list):
            continue
        # This section is all about defining the fk's that will be added to sheet
        # fks will be recursively defined
        if fks_old==None:
            fks = []
        else:
            fks = copy.deepcopy(fks_old) # dont overwrite original parent fk
        sub_fk = []
        l = fk_str.split(',')
        for i in l:
            p = i.split('.')
            if isinstance(entry,dict):
                val = entry.get(p[-1],{})
            else:
                continue

            # if val is a nested object, wait until next recursion to get its properties
            if len(p)>1:
                sub_fk.append('.'.join(p[1:]))
            # otherwise, store it to be added to the sheet later
            else:
                # at this point, there shouldn't be any more '.' in the key
                key = p[0]
                if val:
                    fks.append({'key':key,'val':val,'parent':parent})
                else: 
                    fks.append({'key':key,'val':val,'parent':parent})
        
        # rejoin all sub fk so they look like fks_old when it came in
        sub_fk = ','.join(sub_fk)

        # this section focuses on collating the data into one 'sheet'
        if entry.get(sheet,False):

            sub_entries = entry.pop(sheet)
            #one-to-one management
            if isinstance(sub_entries,dict):
                sub_entries=[sub_entries]
            for sub in sub_entries:
                if isinstance(sub,list):
                    sub = {str(n):x for n,x in enumerate(sub)}
                for fk in fks:
                    # have to make it so there isn't any name collision between 
                    # fk and attributes
                    if fk['key'] in list(sub.keys()):
                        fk['key']=f"{fk['parent']}.{fk['key']}"
                    sub[fk['key']]=fk['val']
                sheet_data.append(converter(sub))
        else:
            for k,v in entry.items():
                if isinstance(v,list) or isinstance(v,dict):

                    rec_get_sheets(v,sheet,sheet_data,converter,sub_fk,k,fks)


def export_to_excel(db):
    
    sheets = {}
    for sheet in db.sheets:
        sheets[sheet]=[]
    for i,(k,v) in enumerate(sheets.items()):

        rec_get_sheets(db.data,k,v,db.out_converters[i],db.fk[i],db.name)

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
    rels = {}
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
        rels[sheet]=db.relationship[ind]

    # Last key in Fks is always the merge key. Iteratively merge all sheets
    for i in range(depth):
        for k,v in sheets.items():
            key_list = fks[k]
            rel = rels[k]
            depth_i = len(key_list[-1].split('.'))
            if not depth_i==depth:
                continue
            if depth==1 and db.pk in key_list[-1]:
                main = df_dict_merge(k,v,main,key_list,rel)
                continue

            keys = key_list[-1].split('.')
            parent = sheets[keys[-2]]
            parent = df_dict_merge(k,v,parent,key_list,rel)
            sheets[keys[-2]]=parent
        depth-=1
    with db.lock:
        db.data=list(main.to_dict('index').values())
    

    return db

def df_dict_merge(sheet,child,parent,key_list,rel):
    key_list=copy.deepcopy(key_list)
    # Get main foriegn key, drop the rest
    main_fk = key_list.pop()
    for key in key_list:
        sub_keys = key.split('.')
        dup_key = '.'.join(sub_keys[-2:])
        if dup_key in list(child.columns):
            child = child.drop(dup_key,axis=1)
        else:
            child = child.drop(key.split('.')[-1],axis=1)

        

    # Get fields unique to this sheet
    sub_keys = main_fk.split('.')   
    fields = list(child.columns)
    if '.' in ''.join(fields):
        merge_key = '.'.join(sub_keys[-2:])
    else:
        merge_key = sub_keys[-1]
    fields.remove(merge_key)
    
    # Make sure parent and childe have unique name spaces
    parent_fields = list(parent.columns)
    for field in fields:
        if field in parent_fields:
            child = child.rename(columns={field:f'{sheet}.{field}'})

    # Redefine child field after any renaming
    fields = list(child.columns)
    fields.remove(merge_key)

    # merge child and parent into a family
    family = pd.merge(parent,child,'left',left_on=sub_keys[-1],right_on=merge_key)

    # Reformat so that child is a list of dicts in parent dataframe
    grp = family.set_index(merge_key).groupby(merge_key)[fields]
    dict_list = []
    for name,group in grp:

        # revert renames if any occured
        for field in fields:
            if '.' in field:
                field = field.split('.')[-1]
                group = group.rename(columns={f'{sheet}.{field}':field}) 
        temp_dicts = group.to_dict('records')
        out = []
        if '0' in list(group.columns):
            for temp_dict in temp_dicts:
                sub_out = []
                for i in range(len(list(temp_dict.keys()))):
                    sub_out.append(temp_dict[str(i)])
                out.append(sub_out)
        else:
            out = temp_dicts
        if rel==1:
            out=out[0]
        dict_list.append({sub_keys[-1]:name,sheet:out})

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
        #support indexing if data was a list of lists
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

    

    db = model.Network( [{
        "ip": "172.22.0.7",
        "cog_id": 0,
        "intersection": "cannot locate",
        "lat": 0,
        "long": 0,
        "modem": {
            "clients": [
                {
                    "mac": "-",
                    "ip_address": "192.168.0.10"
                },
                {
                    "mac": "-",
                    "ip_address": "192.168.0.5"
                },
                {
                    "mac": "-",
                    "ip_address": "192.168.0.9"
                }
            ],
            "os_ver": "-",
            "fw_ver": "-",
            "device_name": "-",
            "lat": 0.0,
            "lon": 0.0,
            "upgradeable": False,
            "dbm": "-73",
            "sn": "357926103083155",
            "model": "IBR900-1200M-B",
            "mac": "00:30:44:6c:79:86",
            "cpu": 0.03364827266403895,
            "temp": 48,
            "licenses": [
                [
                    "ecf1a864-ef3b-4136-b2c5-e1b65528a0c5",
                    "NetCloud Manager (NCM)",
                    249,
                    201
                ],
                [
                    "46a03bd2-91ae-11e2-a305-002564cb1fdc",
                    "Extended Enterprise License",
                    1863,
                    1557
                ]
            ]
        },
        "updated_at": "2023-07-28 08:18:13.771536"
    }]
    )
    print(import_from_excel(export_to_excel(db),model.Network()).data)