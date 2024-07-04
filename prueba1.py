from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import time


def esperar_carga_componenete(driver):
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="spinner"]')))
    except TimeoutException:
        print("OJO, no apareció la leyenda de carga")
    try:
        WebDriverWait(driver, 120).until(EC.invisibility_of_element_located((By.XPATH, '//div[@class="spinner"]')))
    except TimeoutException:
        print("Error: No desaparece leyenda cargando")
    
    time.sleep(1)


def main():
    print("Iniciando Driver...")
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": r"C:\Users\juan-\Desktop\CNET Scrapping 2024\temp\\",
        "download.directory_upgrade": True,
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    #options.add_argument("--headless")
    options.add_argument("--window-size=1024,768")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("--disable-infobars")

    driver = webdriver.Chrome(options=options,
                service=Service(executable_path=ChromeDriverManager().install()),
            )
    
    print("get...")
    driver.get("https://upcp-compranet.hacienda.gob.mx/sitiopublico/#/")
    esperar_carga_componenete(driver)

    driver.find_element(By.XPATH, '//*[text()="Anuncios concluidos"]').click()
    esperar_carga_componenete(driver)
    
    driver.find_element(By.XPATH, '//*[@name="proceso"]').click()
    time.sleep(2)

    driver.find_element(By.XPATH,'//*[text()="PROCEDIMIENTO DE CONTRATACIÓN"]').click()
    time.sleep(2)

    driver.find_element(By.XPATH,'//*[@name="ley"]').click()
    time.sleep(2)

    driver.find_element(By.XPATH,'//*[contains(text(),"LEY DE ADQUISICIONES")]').click()
    time.sleep(2)

    driver.find_element(By.XPATH,'//*[@name="contratacion"]').click()
    time.sleep(2)

    driver.find_element(By.XPATH,'//*[(text()="ADQUISICIONES")]').click()
    time.sleep(2)


    click = lambda xpath: driver.find_element(By.XPATH, xpath).click()

    click('//*[@label="Filtros"]/button')
    time.sleep(5)

    click('//*[@name="claves"]')
    time.sleep(2)

    claves = ["25401","25301","25501","32401","53101","53201"]

    for clave in claves:
        driver.find_element(By.XPATH,'//p-multiselect[@name="claves"]//input[contains(@class,"filter")]').send_keys(clave)
        time.sleep(2)
        
        click(f'//*[contains(text(),"{clave}")]')
        time.sleep(2)
        
        driver.find_element(By.XPATH,'//p-multiselect[@name="claves"]//input[contains(@class,"filter")]').clear()
        time.sleep(1)
    

    click('//span[text()="Buscar"]')
    esperar_carga_componenete(driver)



    rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
    ops_found = len(rows)
    print(f"se encontraron {ops_found} oportunidades en está página")
    for i in range(0, ops_found):
        rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
        rows[i].click()
        esperar_carga_componenete(driver)


        print(f"\n-> Extrayendo inf de la oportunidad {i+1}...")

        #Código del expediente
        cod_exp = driver.find_element(By.XPATH, '//label[text()="Código del expediente:"]/following-sibling::label').text
        #Número de procedimiento de contratación
        proc_cont = driver.find_element(By.XPATH, '//label[text()="Número de procedimiento de contratación:"]/following-sibling::label').text
        #Dependencia (SOLO TEXTO DESPUÉS DEL GUIÓN “-”)
        dependencia = driver.find_element(By.XPATH, '//label[text()="Dependencia o Entidad:"]/following-sibling::label').text
        #Unidad Compradora (SOLO CÓDIGO IDENTIDICADOR)
        unidad_comp = driver.find_element(By.XPATH, '//label[text()="Unidad compradora"]/following-sibling::label').text
        #Correo electrónico Unidad compradora
        correo = driver.find_element(By.XPATH, '//label[text()="Correo electrónico unidad compradora:"]/following-sibling::label').text
        
        print(" -", cod_exp, proc_cont, dependencia, unidad_comp, correo)

        print(f"    -Extrayendo anexos")
        anexos = driver.find_elements(By.XPATH,'//*[@ptooltip="Descargar archivo"]')
        for anexo in anexos:
            anexo.click()
            time.sleep(7)
            break

        driver.back()
        esperar_carga_componenete(driver)





if __name__ == "__main__":
    main()
