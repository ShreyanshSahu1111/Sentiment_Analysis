#executable_path= r'C:\Users\USER\Desktop\home\chromedriver.exe'
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time

path=r'my\\path\\to\\chromedriver.exe'
url=r'https://www.worldbank.org/en/home'#to test the aquired ip
proxies_url=r'https://sslproxies.org/'
ip_check_url=r'https://whatismyipaddress.com/'
proxies={}

options=ChromeOptions()
options.add_argument('start-maximized')
options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'] )
options.add_experimental_option('useAutomationExtension', False)


with Chrome(chrome_options=options, executable_path=path) as driver:
    driver.get(proxies_url)
    print(f"title={driver.title}")
    for i in range(0,5): driver.execute_script("window.scrollBy(0,5000)") 
    WebDriverWait(driver, timeout=5).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, r'#proxylisttable > tbody > tr')))
    tbody_el=driver.find_element_by_css_selector('#proxylisttable > tbody')
    with open('proxy1.txt', 'wt', encoding='utf-8') as file:
        for row_elem in tbody_el.find_elements_by_css_selector('tr '):
            td_elems=row_elem.find_elements_by_css_selector('td')
            if 'elite proxy' in td_elems[4].text :
                proxies[td_elems[0].text+':'+td_elems[1].text]=[td_elems[x].text for x in (3,5,6)]
                file.write(td_elems[0].text+" ")

#getting proxies DONE
for proxy in proxies:
    options.add_argument(f"--proxy-server={proxy}")
    with Chrome(chrome_options=options, executable_path=path) as driver:
        driver.minimize_window()
        try:
            driver.get(ip_check_url)
            WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located((By.CSS_SELECTOR,r'#ipv4 > a')))
            current_ip=driver.find_element_by_css_selector(r'#ipv4 > a').text
            print(current_ip)
            if current_ip==proxy.split(':')[0]:
                print("success")
                break
        except:
            continue
else:
    print("unsuccess")