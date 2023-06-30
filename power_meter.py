from difflib import SequenceMatcher
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import ElementClickInterceptedException,TimeoutException,StaleElementReferenceException,NoSuchElementException
from selenium.webdriver.common.by import By
import datetime
import requests
from urlib3.exceptions import InsecureRequestWarning
import json
from urllib3.connection import ConnectTimeoutError

requests.packages.urlib3.diable_warnings(category =  InsecureRequestsWarning)
response = requests.get("https://ors-svc.aws.cloud.oncor.com", verify = False)
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
    
    def next(self,driver):

        next_button = driver.find_element(value='next')
        next_button.click()
        return True

    def grab_status(self,driver):
        status = driver.find_element(value='label_no_omscall_fault')
        return status.text
    
    def check_active(self,driver):
        try:
            error_msg = driver.find_element(By.ID,'error')
            return error_msg.text
        except NoSuchElementException as error:
            return 'acount_active'

    def check_restored_or_out(self, driver):
        try:
            msg = driver.find_element(By.ID,'power_outage').text
            date = driver.find_element(By.ID,'outage_report_date').text
            status = f"{msg} {date}"
        except NoSuchElementException as error:  
            status = "device offline"
        return status
    
    def selenium_get(self,driver):
        try:    

            driver.get(
                "https://www.oncor.com/outages/check_status/identify/esi"
            )

            # interaction for first Oncor page
            id_input = driver.find_element(value='esi_id_text')
            next_button = driver.find_element(value='next')
            id_input.clear()
            id_input.send_keys(self.id)
            next_button.click()

            # Proper wait strategy to allow page to load before more interaction
            WebDriverWait(
                driver, 
                5,
                ignored_exceptions=[StaleElementReferenceException]
            ).until(
                self.next
            )


            try:
                # Proper wait strategy to allow page to load before more interaction
                status = WebDriverWait(
                    driver, 
                    3,
                    ignored_exceptions=[StaleElementReferenceException,NoSuchElementException]
                ).until(
                    self.grab_status
                )
                log_str = f"ESI ID \"{self.id}\": [SUCCESS] status was updated\n"
                return status,log_str

            # if element isnt present, power is out or has just been restored
            except (TimeoutException) as error:
                status = self.check_restored_or_out(driver)
                log_str = f'{datetime.datetime.now()}: ESI ID \"{self.id}\" status: {status}\n'
                return status,log_str

        # This exception shouldnt trigger because of proper wait strategy, but it is
        # left in for redundancy
        except StaleElementReferenceException as error:
            status = 'unupdated'
            log_str = f'{datetime.datetime.now()}: ESI ID \"{self.id}\": [ERROR] search was too fast, status was not updated\n'
            return status,log_str

        # This exception triggers if the account is not registered with Oncor
        except ElementClickInterceptedException as error:

            # Double checks the error was that the account wasn't active
            msg = self.check_active(driver)

            # Throws another error if the account is active

            
            status=msg
            log_str = f'{datetime.datetime.now()}: ESI ID \"{self.id}\": [ERROR] {msg}\n'
            return status,log_str

        # Handles any unexpected exceptions so the program will mostly continue to 
        # run        
        except Exception as error:
            print("an error occured\n")
            print(error)
            status = 'An unknown error occured; status update cannot be guaranteed'
            log_str = f'{datetime.datetime.now()}: ESI ID \"{self.id}\": [ERROR] a fatal error occured\n'
            return status,log_str
        
    def http_get(self):
        try:
            if self.id == '0000000000' or self.id == '0000000':
                if self.number == '-':
                    return 'no_id'
                else:
                    esi_url = f'https://ors-svc.aws.cloud.oncor.com/customerOutage/identifyLocation/meter?meter={self.number[0:9]}'
                    res = json.loads(requests.get(esi_url).text)
                    if res.get('validateMeterResponse',False):
                        self.esi_id = res['validateMeterResponse']['account'][0]['number']
                    else:
                        return 'bad_id'
            # json parse error on 1823
            # pars error is because of bad response but there is only a bad response some of the time when accouts are inactive or temporarily disabled
            # nevermind, that had something to do with caches
            # even error codes come back with 200 response
            response = requests.get("https://ors-svc.aws.cloud.oncor.com/customerOutage/identifyLocation/esiId?esiid={self.id}", verify = False)
            validate_url = f'https://ors-svc.aws.cloud.oncor.com/customerOutage/identifyLocation/esiId?esiid={self.id}'
            url = f"https://ors-svc.aws.cloud.oncor.com/customerOutage/outage/checkStatus?esiid={self.id}&source=ORS"

            res = json.loads(requests.get(validate_url).text)
            if res.get('Error',False):
                return 'bad_id'
            if res.get('validateAccountResponse',False):
                if res['validateAccountResponse']['account']['status'] =='ACTIVE':
                    
                    res = json.loads(requests.get(url).text)
                    return res['getOutageStatusResponse']['powerStatus']['status']
                else:
                    return res['validateAccountResponse']['account']['status']
            else:
                return 'unknown'
        except (requests.Timeout, TimeoutError, ConnectTimeoutError) as e:
            print(e)
            return 'update failed'
        except Exception as e:
            print(e)
            return 'update failed'
