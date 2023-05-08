from difflib import SequenceMatcher

class PowerMeter():
    

    def __init__(self,dict_in=None):
        if (dict_in):
            self.dict_in = dict_in
            self.esi = dict_in['esi_id']
            self.cog = dict_in['cog_id']
            self.name = dict_in['name']
            
            self.meters = [dict_in['meter_number']]
            if dict_in['meter_number_2']!= '-':
                self.meters.append(dict_in['meter_number_2'])

            assert len(self.meters) == dict_in['num_meters'],f'the number of valid meter numbers does not match number of meters recorded for esi_id {self.esi}'

            self.street = dict_in['street']
            self.zip_code = dict_in['zip_code']

    def verify_address(self,driver):
        driver.get("https://www.oncor.com/outages/check_status/identify/esi")


        id_input = driver.find_element(value='esi_id_text')
        next_button = driver.find_element(value='next')
        id_input.clear()
        id_input.send_keys(self.esi) #truncate id
        next_button.click()
        address = driver.find_element(value='address_text').text
        self.oncor_address = address

        ind = address.index('...')
        comp = address[0:ind]
        trim = self.street[0:len(comp)]

        sim = SequenceMatcher(None,trim,comp).ratio()
        self.sim = sim

        return sim
    def to_dict(self):
        dict_out = self.dict_in
        dict_out['esi_id'] = self.esi
        dict_out['cog_id'] = self.cog
        dict_out['name'] = self.name

        dict_out['meter_number'] = self.meters[0]
        if len(self.meters)>1:
            dict_out['meter_number_2'] = self.meters[1]

        dict_out['street'] = self.street
        dict_out['zip_code'] = self.zip_code

        if self.oncor_address is not None:
            dict_out['oncor_address'] = self.oncor_address
            dict_out['address_sim'] = self.sim

        return dict_out