import matplotlib.pyplot as plt
import json
import power_meter

with open('new_power.json') as f:
    meters = json.load(f)

sig_meters = meters['Traffic Signals']
zip_file = open('zip.txt','w')
add_file = open('add.txt','w')
inactive_file = open('inactive.txt','w')
no_zip = []
bad_address = []
not_active = []
for meter_dict in sig_meters:
    meter = power_meter.PowerMeter(meter_dict)
    if meter.zip_code == '11111':
        no_zip.append(meter)
        zip_file.write(f"Meter at {meter.address} is missing a zip code \n")
    if meter.status != 'registered':
        not_active.append(meter)
        inactive_file.write(f"the esi id {meter.id} with address {meter.address} is not active with oncor.\n")
    else:
        if meter.sim < 1:
            bad_address.append(meter)
            add_file.write(f"The address provided for the meter ({meter.address}) does not match the oncor provided address ({meter.oncor_address})\n")
            
zip_file.close()
add_file.close()
inactive_file.close()
plt.show()
plt.hist(x = [meter.zip_code for meter in no_zip])
