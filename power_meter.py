from difflib import SequenceMatcher
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException,TimeoutException
from account_disconnect import check_active, check_restored

class PowerMeter():
    

    def __init__(self,dict_in:dict =None):
        for key in dict_in:
            setattr(self,key,dict_in[key])

    def verify_address(self,driver):
        driver.get("https://www.oncor.com/outages/check_status/identify/esi")


        id_input = driver.find_element(value='esi_id_text')
        next_button = driver.find_element(value='next')
        id_input.clear()
        id_input.send_keys(self.id)
        next_button.click()
        try:
            address = WebDriverWait(driver,timeout=2).until(lambda d: d.find_element(value='address_text').text)
            self.status = 'registered'
            self.oncor_address = address

            ind = address.index('...')
            comp = address[0:ind].lower()
            trim = self.street[0:len(comp)].lower()

            sim = SequenceMatcher(None,trim,comp).ratio()
        except (ElementClickInterceptedException,TimeoutException) as error:
            msg = check_active(driver)
            self.status = msg
            print(msg)
            self.oncor_address = ''
            sim = 0
        self.address_sim = sim

        return sim
    
    @property
    def id(self):
        return str(self.esi_id)[-10:]
    
    @property
    def address(self):
        zip_code = str(int(self.zip_code))
        return f"{self.street}, Dallas, TX {zip_code}"