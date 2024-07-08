from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from datetime import date, datetime
import time
import os
import time
import shutil
import random
import pandas as pd



def timing_val(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        func(*arg, **kw)
        t2 = time.time()
        segs = int(t2 - t1)
        return f"tardó {segs} segs..."
    return wrapper


def duerme(a:int, b:int=0):
    "Sleeps for @a seconds, if b is given it'll sleep for a random between @a, @b"
    time_to_sleep = random.uniform(a, b) if b else a
    time.sleep(time_to_sleep)


def delete_files():
    global anexos_dir
    #print(f"Borrando el directorio: {anexos_dir}")
    for root, dirs, files in os.walk(anexos_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
    
    if len(os.listdir(anexos_dir)) > 0:
        raise Exception("Error borrando archivo descargado.")


def upload_files():
    global today, anexos_dir, anuncio, anexos_file_name
    for file_name in os.listdir(anexos_dir):
        print(f"  agregando archivo: {file_name}")
        cod_exp = anuncio['cod_exp']
        num_proc = anuncio['num_proc']
        new_row = {'cod_exp':cod_exp, 'num_proc':num_proc, 'anexo':file_name, 'scrapped_day':today}
        df = pd.DataFrame([new_row])
        df.to_csv(anexos_file_name, index=False, header=False, encoding='utf-8', mode='a')


def download_wait(timeout:int, nfiles:int=1):
    """"""
    global anexos_dir, anuncio

    def rename_files(prefix:str):
        dir = anexos_dir
        for filename in os.listdir(dir):
            new_filename = f"{prefix}_{filename}"
            new_filename = new_filename.replace(" ","_").strip()
            os.rename(dir+"/"+filename, dir+"/"+new_filename)

    #print("Esperando descarga")

    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(anexos_dir)
        if len(files) < nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1

    if seconds >= timeout:
        #print("Error esperando descarga, se superó el tiempo de espera.")
        delete_files()
    else:
        #print("Archivo descargado")
        if seconds < 15:
            duerme(3, 7)

        #print("Renombrando archivo")
        prefix = anuncio['cod_exp'].rsplit("-", 1)[1]
        rename_files(prefix)

        #print(f"Subiendo Archivos")
        upload_files()

        delete_files()


def set_driver():
    """Initialize a webdriver to simulate chrome browser"""
    global driver, anexos_full_dir
    
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": anexos_full_dir,
        "download.directory_upgrade": True,
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    #options.add_argument("--headless")
    options.add_argument("--window-size=1024,768")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")


    driver = webdriver.Chrome(options=options,
                service=Service(executable_path=ChromeDriverManager().install()),
            )


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def espera_carga_componenete(a:int=5, b:int=120):
    global driver
    try:
        xp = '//div[@class="spinner"]'
        WebDriverWait(driver, a).until(EC.visibility_of_element_located((By.XPATH, xp)))
    except TimeoutException:
        print("OJO, no apareció la leyenda de carga")
    try:
        WebDriverWait(driver, b).until(EC.invisibility_of_element_located((By.XPATH, xp)))
    except TimeoutException:
        print("Error: No desaparece leyenda cargando")
    
    time.sleep(1)


def click(xp:str, dormir:bool=True):
    global driver

    element = driver.find_element(By.XPATH, xp)
    ActionChains(driver).scroll_to_element(element)\
        .move_to_element(element).pause(1).click().perform()

    if dormir:
        duerme(1,5)


def fill(xp:str, txt:str):
    global driver
    element = driver.find_element(By.XPATH, xp)
    for letter in txt:
        element.send_keys(letter)
        duerme(.25, 1)


def set_filters():
    global claves
    print("-> proceso: PROCEDIMIENTO DE CONTRATACIÓN")
    click('//*[@name="proceso"]')
    click('//*[text()="PROCEDIMIENTO DE CONTRATACIÓN"]')

    print("-> ley: LEY DE ADQUISICIONES, ARRENDAMIENTOS Y SERVICIOS DEL SECTOR PÚBLICO")
    click('//*[@name="ley"]')
    click('//*[text()="LEY DE ADQUISICIONES, ARRENDAMIENTOS Y SERVICIOS DEL SECTOR PÚBLICO"]')

    print("-> contratación: ADQUISICIONES")
    click('//*[@name="contratacion"]')
    click('//*[text()="ADQUISICIONES"]')

    print("más filtros")
    click('//*[@label="Filtros"]/button')

    print(f"-> claves: {claves}")
    click('//*[@name="claves"]')
    for clave in claves:
        xp = '//p-multiselect[@name="claves"]//input[contains(@class,"filter")]'
        fill(xp=xp, txt=clave)
        duerme(1, 2)

        click(f'//*[contains(text(),"{clave}")]', dormir=False)
        duerme(.5, 1.5)

        driver.find_element(By.XPATH, xp).clear()
        duerme(.5,2)

    print("buscar")
    click(xp='//span[text()="Buscar"]', dormir=False)
    espera_carga_componenete()


def get_text_by_xpath(xp:str, required:bool=False, join:bool=False):
    try:
        if not join:
            txt = driver.find_element(By.XPATH, xp).text
        else:
            finds = driver.find_elements(By.XPATH, xp)
            txt = ",".join([i.text for i in finds])

        return txt
    
    except:
        if required:
            return False
        else:
            return ""


def extraer_anexos():
    global driver, anexos_dir
    for i in range(0, 10):
        anexos = driver.find_elements(By.XPATH,'//*[@ptooltip="Descargar archivo"]')
        for anexo in anexos:
            anexo.click()
            download_wait(timeout=120)
        
        next_page_btn = driver.find_element(By.XPATH,'//*[@key="anexos"]/following-sibling::div//button[contains(@class,"p-paginator-next")]')
        if "p-disabled" in next_page_btn.get_attribute("class"):
            print("No hay más páginas de anexos disponibles")
            break
        else:
            ActionChains(driver).scroll_to_element(next_page_btn)\
                .pause(1).click(next_page_btn).perform()
            espera_carga_componenete()
            duerme(2, 4)


def get_page_info() -> dict:
    global driver, anuncio

    #Código del expediente
    cod_exp = get_text_by_xpath(xp='//label[text()="Código del expediente:"]/following-sibling::label', required=True)
    #Número de procedimiento de contratación
    num_proc = get_text_by_xpath(xp='//label[text()="Número de procedimiento de contratación:"]/following-sibling::label', required=True)
    #Dependencia (SOLO TEXTO DESPUÉS DEL GUIÓN “-”)
    dependencia = get_text_by_xpath(xp='//label[text()="Dependencia o Entidad:"]/following-sibling::label')
    #Unidad Compradora (SOLO CÓDIGO IDENTIDICADOR)
    unidad_comp = get_text_by_xpath(xp='//label[text()="Unidad compradora"]/following-sibling::label')
    #Correo electrónico Unidad compradora
    correo = get_text_by_xpath(xp='//label[text()="Correo electrónico unidad compradora:"]/following-sibling::label')
    # Nombre del procedimiento de contratación
    nombre_procedimiento = get_text_by_xpath(xp='//label[text()="Nombre del procedimiento de contratación:"]/following-sibling::label')
    # Tipo de procedimiento
    tipo_proc = get_text_by_xpath(xp='//label[text()="Tipo de procedimiento de contratación:"]/following-sibling::label')
    # Entidad Federativa
    entidad_fed = get_text_by_xpath(xp='//label[text()="Entidad Federativa donde se llevará a cabo la contratación:"]/following-sibling::label')
    # Año del ejercicio presupuestal
    anio_ej = get_text_by_xpath(xp='//label[text()="Año del ejercicio presupuestal:"]/following-sibling::label')
    # Procedimiento exclusivo para MiPymes
    proc_exc = get_text_by_xpath(xp='//label[text()="Procedimiento exclusivo para MIPYMES:"]/following-sibling::label')
    # Lista de Claves
    claves_list = get_text_by_xpath(xp='//th[text()="Clave"]/ancestor::thead/following-sibling::tbody/tr/td[1]', join=True)
    # Participación de Testigo Social
    part_testigo = get_text_by_xpath(xp='//label[text()="Participación de Testigo Social:"]/following-sibling::label')
    # Abastecimiento simultaneo
    abastecimiento_sim = get_text_by_xpath(xp='//label[text()="Abastecimiento simultáneo:"]/following-sibling::label')
    # Plurianual
    plurianual = get_text_by_xpath(xp='//label[text()="Es plurianual:"]/following-sibling::label')
    # Tipo de contratación
    tipo_cont = get_text_by_xpath(xp='//label[text()="Tipo de contratación:"]/following-sibling::label')
    # Anticipo
    anticipo = get_text_by_xpath(xp='//label[text()="Anticipo:"]/following-sibling::label')
    # Forma de Pago
    forma_pago = get_text_by_xpath(xp='//label[text()="Forma de pago:"]/following-sibling::label')
    # Plazo para entrega de garantía
    plazo_garant = get_text_by_xpath(xp='//label[text()="Plazo en días para entregar la garantía:"]/following-sibling::label')
    # Número de meses para la garantía
    meses_garant = get_text_by_xpath(xp='//label[text()="Número de meses que debe cumplir la garantía:"]/following-sibling::label')
    #Garantía de cumplimiento
    garant_cump = get_text_by_xpath(xp='//label[text()="Garantía de cumplimiento:"]/following-sibling::label')
    # Carácter
    caracter = get_text_by_xpath(xp='//label[text()="Carácter:"]/following-sibling::label')
    # Caso fortuito o fuerza mayor
    caso_fort  = get_text_by_xpath(xp='//label[text()="Caso fortuito o fuerza mayor:"]/following-sibling::label')
    # Tipo de contrato abierto
    tipo_cont_abierto = get_text_by_xpath(xp='//label[text()="Tipo de contrato abierto:"]/following-sibling::label')
    #oportunnity url
    uri = driver.current_url

    # Fecha y hora de publicación:
    fecha_pub = get_text_by_xpath(xp='//label[text()="Fecha y hora de publicación:"]/following-sibling::label', required=True)
    if fecha_pub:
        try:
            fecha_pub = datetime.strptime(fecha_pub, "%d/%m/%Y %H:%M").strftime("%d/%m/%Y %H:%M")
        except:
            print(f"Error formateando la fecha {fecha_pub} de la op:\n{uri}")
            fecha_pub = False

    anuncio = {'cod_exp':cod_exp, 'num_proc':num_proc}

    extraer_anexos()

    return {'cod_exp':cod_exp, 'num_proc':num_proc, 'dependencia':dependencia, 'unidad_comp':unidad_comp, 
            'correo':correo, 'nombre_procedimiento':nombre_procedimiento, 'tipo_proc':tipo_proc, 
            'entidad_fed':entidad_fed, 'anio_ej':anio_ej, 'proc_exc':proc_exc, 'fecha_pub':fecha_pub, 
            'claves_list':claves_list, 'part_testigo':part_testigo, 'abastecimiento_sim':abastecimiento_sim, 
            'plurianual':plurianual, 'tipo_cont':tipo_cont, 'anticipo':anticipo, 'forma_pago':forma_pago, 
            'plazo_garant':plazo_garant, 'meses_garant':meses_garant, 'caracter':caracter, 'caso_fort ':caso_fort , 
            'tipo_cont_abierto':tipo_cont_abierto, 'uri':uri, 'scrapped_day':today
        }


@timing_val
def scrape_page():
    global driver,  gobernanza, conc_file_name, procedimientos_guardados

    rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
    ops_found = len(rows)
    print(f"  se encontraron {ops_found} oportunidades en está página")
    for i in range(0, ops_found):
        rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
        n_proc = rows[i].text
        if procedimientos_guardados['num_proc'].str.contains(n_proc).any():
            print(f"procedimiento: {n_proc} ya está en la bdd")
            continue
        rows[i].click()
        espera_carga_componenete()

        print(f"  Extrayendo inf anuncio {i}")
        new_row = get_page_info()

        if not new_row['cod_exp'] or not new_row['num_proc'] or not new_row['fecha_pub']:
            print(f"Error recuperando informacón básica del anuncio: {new_row['uri']}") 
            print(f"codigo de expediente: {new_row['cod_exp']}")
            print(f"numero de exp: {new_row['num_proc']}")
            print(f"fecha publicación: {new_row['fecha_pub']}")
            continue
        
        df = pd.DataFrame([new_row])
        df.to_csv(conc_file_name, index=False, header=False, encoding='utf-8', mode='a')
        print("  Se extrajo y guardó información de anuncio de manera correcta.")

        driver.back()
        espera_carga_componenete()


def paginate():
    global driver, main_url, gobernanza

    print(f"Entrando a la pagina principal: {main_url}")
    driver.get(main_url)
    espera_carga_componenete()

    print("Anuncios concluidos")
    click('//*[text()="Anuncios concluidos"]', dormir=False)
    espera_carga_componenete()

    print("\nSeteando filtros")
    set_filters()
    
    #PAGINACIÓN
    for i in range(1, 10):
        print(f"\nObteniendo información pag {i}")
        scrape_page()

        next_page_btn = driver.find_element(By.XPATH,'//button[contains(@class,"p-paginator-next")]')
        if "p-disabled" in next_page_btn.get_attribute("class"):
            print("Se acabaron las páginas disponibles")
            break
        else:
            print(f"Cambiando a página: {i+1}")
            ActionChains(driver).scroll_to_element(next_page_btn)\
                .pause(1).click(next_page_btn).perform()
            espera_carga_componenete()
            duerme(2, 6)

    driver.close()


def main():
    """
    """
    global main_url, today, driver, anexos_dir, anexos_full_dir,\
    anuncio, gobernanza, claves, conc_file_name, anexos_file_name,\
    rows_aded, procedimientos_guardados

    anuncio = {}
    rows_aded = 0
    today = date.today().strftime("%d/%m/%Y")
    conc_file_name = './concluidos.csv'
    anexos_file_name = './anexos.csv'
    anexos_dir = './temp'
    anexos_full_dir = r"C:\Users\juan-\Desktop\CNET Scrapping 2024\temp\\"
    main_url = 'https://upcp-compranet.hacienda.gob.mx/sitiopublico/#/'
    gobernanza = 120
    claves = ["25401","25301","25501","32401","53101","53201"]
    
    print("\nCargando el dataset de oportunidades guardadas...")
    procedimientos_guardados = pd.read_csv(conc_file_name, usecols = ['num_proc'])

    print("\nIniciando driver----")
    set_driver()

    print("\nInicia proceso de scrapping paginacion----")
    paginate()


if __name__ == "__main__":
    main()
    driver.close()
    try:
        #main()
        pass
    except Exception as e:
        print(f"error: {e}")
        if driver:
            driver.close()
