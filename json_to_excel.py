import os
import pandas as pd
import json
import io
import copy


def export_sig(signals):
    signals = copy.deepcopy(signals)
    meters = []
    for signal in signals:
        meters_i = signal.pop('meters')
        for meter in meters_i:
            meter['cog_id'] = signal['cog_id']
            meters.append(meter)

    df_sig = pd.DataFrame(signals)
    df_met = pd.DataFrame(meters)
    df_met['esi_id'] = df_met['esi_id'].astype(str)

    file = io.BytesIO()
    with pd.ExcelWriter(file) as writer:
        df_sig.to_excel(writer,'signals')
        df_met.to_excel(writer,'meters')

    file.seek(0,0)
    return file