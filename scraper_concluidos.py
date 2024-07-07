from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.common.exceptions import NoSuchElementException
import requests
from lxml import html
import pandas as pd
from datetime import date
import re
import random
import shutil
import os


def timing_val(func):
    def wrapper(*arg, **kw):
        '''source: http://www.daniweb.com/code/snippet368.html'''
        t1 = time.time()
        func(*arg, **kw)
        t2 = time.time()
        segs = int(t2 - t1)
        return f"tardó {segs} segs..."
    return wrapper


def delete_files_from_dir(dir:str):
    print(f"Borrando el directorio: {dir}")
    for root, dirs, files in os.walk(dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
    
    if os.listdir(dir) > 0:
        raise Exception("Error borrando archivo descargado.")


def download_wait(directory:str, timeout:int, nfiles:int=1):
    """
    Wait for downloads to finish with a specified timeout.
    when the download is complete the file is send to s3 and 
    after that is deleted from local storage

    Args
    ----
    directory : str
        The path to the folder where the files will be downloaded.
    timeout : int
        How many seconds to wait until timing out.
    nfiles : int, defaults to None
        If provided, also wait for the expected number of files.

    """
    print("Esperando descarga")

    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1

    if seconds >= timeout:
        print("Error esperando descarga, se supero el tiempo de espera.")
        delete_files_from_dir("./temp")
    else:
        print("Archivo descargado.")
        if seconds < 15:
            time.sleep( random.randint(3, 6) )

        #Subir_File(AQUI DEBE IR LA FUNCIÓN QUE SUBE LOS ARCHIVOS)

        delete_files_from_dir("./temp")


def set_driver():
    """Initialize a webdriver to simulate chrome browser"""
    global driver

    #setea configuraciones por defecto para el driver
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1024,768")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("enable-automation")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("inicializando driver")
    driver = webdriver.Chrome(options=chrome_options)


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def paginate() -> list:
    """this function paginates the main page and gets all the links of the detail pages
    close de driver when finished and return the list of links"""

    global driver, main_url

    print(f"entrando a la pagina principal: {main_url}")
    driver.get(main_url)
    time.sleep( random.randint(3, 6) )

    #hace scroll hasta el componenete de paginacion
    print("buscando el boton de paginacion con scroll")
    footer = driver.find_element(By.XPATH, '//div[@class="footer-nav"]')
    ActionChains(driver).scroll_to_element(footer).perform()

    links = [link.get_attribute('href') for link in 
             driver.find_elements(By.XPATH, '//a[contains(@href,"id")]')]
    
    #paginacion
    while True:
        try:
            print("-----next page-----")
            driver.find_element(By.XPATH, '(//tr)[last()]/td/span/parent::td/following-sibling::td/a').click()

            print("durmiendo 5 segs")
            time.sleep(5)

            links += [link.get_attribute('href') for link in driver.find_elements(By.XPATH, '//a[contains(@href,"id")]')]
                
        except NoSuchElementException:
            print("no hay mas paginas")
            break

    driver.quit()
    return links


def main():
    """
    """
    global main_url, df, today, file_name, driver

    today = date.today().strftime("%d/%m/%Y")
    file_name = '../oportunidades.csv'
    main_url = 'https://jobs.unops.org/Pages/ViewVacancy/VAListing.aspx'
    
    print("\nIniciando driver...")
    set_driver()

    print("\nhaciendo paginacion...")
    links = paginate()

    print("\nCargando el dataset de oportunidades guardadas...")
    df = load_csv(file_name)
    
    print("\nBuscando nuevas oportunidades...")
    find_new_jobs(links)


if __name__ == "__main__":
    main()
