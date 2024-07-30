from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date, datetime
from colorama import Fore
import time
import os
import time
import shutil
import random
import pandas as pd
import re

def timing_val(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        func(*arg, **kw)
        t2 = time.time()
        segs = int(t2 - t1)
        print(f"tardó {segs} segs...")
        return segs
    return wrapper


def duerme(a:int, b:int=0):
    "Sleeps for @a seconds, if b is given it'll sleep for a random between @a, @b"
    time_to_sleep = random.uniform(a, b) if b else a
    time.sleep(time_to_sleep)


def delete_files(is_retry:bool=False):
    global anexos_dir
    try:
        #print(f"Borrando el directorio: {anexos_dir}")
        for root, dirs, files in os.walk(anexos_dir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        
        if len(os.listdir(anexos_dir)) > 0:
            raise Exception("Error borrando archivo descargado.")
    except Exception as e:
        if is_retry:
            raise Exception(f"Error borrando archivos\n{e}")
        else:
            duerme(17)
            delete_files(is_retry=True)


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
        for i, filename in enumerate(os.listdir(dir)):
            new_filename = f"{i+1}_{prefix}_{filename}"
            new_filename = new_filename.replace(" ","_").strip()
            os.rename(dir+"/"+filename, dir+"/"+new_filename)

    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(anexos_dir)
        if len(files) < nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload') or fname.endswith('.temp') or fname.endswith('tmp'):
                dl_wait = True

        seconds += 1

    if seconds >= timeout:
        print("  Error esperando descarga, se superó el tiempo de espera.")
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
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--window-size=1920, 1080")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    executable_path = ChromeDriverManager().install()
    executable_path = executable_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe")
    driver = webdriver.Chrome(options=options,
                service=Service(executable_path=executable_path),
            )

    print("driver correctamente inicializado.")


def load_csv(file_name:str) -> pd.DataFrame:
    #lee la tabla de la pagina
    return pd.read_csv(file_name, encoding='utf-8')


def espera_carga_componenete(a:int=5, b:int=180):
    "Espera que aparezca y desaparezca el loading... de la página."
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
    "Hace scroll a un elemento, se mueve a el  y le da click "
    global driver

    element = driver.find_element(By.XPATH, xp)
    ActionChains(driver).scroll_to_element(element)\
        .move_to_element(element).pause(1).perform()
    element.click()

    if dormir:
        duerme(2, 5)


def fill(xp:str, txt:str):
    global driver
    element = driver.find_element(By.XPATH, xp)
    for letter in txt:
        element.send_keys(letter)
        duerme(.1, 1)


def persist_click():
    "este click fallaba porque tardaba en cargar la lista de opciones"
    tries = 0
    while tries < 5:
        print(f"Falló click de adquisiciones, parece que el submenú desplegable de opciones no ha cargado,\
               reintento {tries+1}...")
        try:
            click('//*[text()="ADQUISICIONES"]')
            return
        except:
            duerme(4.2, 8.7)
            tries += 1


def set_filters():
    global claves
    print("-> proceso: PROCEDIMIENTO DE CONTRATACIÓN")
    click('//*[@name="proceso"]')
    click('//*[text()="PROCEDIMIENTO DE CONTRATACIÓN"]')

    print("-> ley: LEY DE ADQUISICIONES, ARRENDAMIENTOS Y SERVICIOS DEL SECTOR PÚBLICO")
    click('//*[@name="ley"]')
    click('//*[text()="LEY DE ADQUISICIONES, ARRENDAMIENTOS Y SERVICIOS DEL SECTOR PÚBLICO"]')

    print("-> contratació: ADQUISICIONES")
    click('//*[@name="contratacion"]')
    try:
        click('//*[text()="ADQUISICIONES"]')
    except:
        persist_click()

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
            try:
                anexo.click()
            except ElementClickInterceptedException:
                duerme(4, 7)
                anexo.click()
            download_wait(timeout=120)
        
        next_page_btn = driver.find_element(By.XPATH,'//*[@key="anexos"]/following-sibling::div//button[contains(@class,"p-paginator-next")]')
        if "p-disabled" in next_page_btn.get_attribute("class"):
            print("  No hay más páginas de anexos disponibles")
            break
        else:
            ActionChains(driver).scroll_to_element(next_page_btn)\
                .pause(1).click(next_page_btn).perform()
            espera_carga_componenete()
            duerme(2, 4)


def get_page_info() -> dict:
    global driver, anuncio, today

    #oportunnity url
    uri = driver.current_url
    print(f"  {uri}")

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

    # Fecha y hora de publicación:
    fecha_pub = get_text_by_xpath(xp='//label[text()="Fecha y hora de publicación:"]/following-sibling::label')
    if fecha_pub:
        try:
            fecha_pub = datetime.strptime(fecha_pub, "%d/%m/%Y %H:%M").strftime("%d/%m/%Y %H:%M")
        except:
            print(f"Error formateando la fecha {fecha_pub} de la op:\n{uri}")
            fecha_pub = today

    # anuncio = {'cod_exp':cod_exp, 'num_proc':num_proc}
    # extraer_anexos()

    return {'cod_exp':cod_exp, 'num_proc':num_proc, 'dependencia':dependencia, 'unidad_comp':unidad_comp, 
            'correo':correo, 'nombre_procedimiento':nombre_procedimiento, 'tipo_proc':tipo_proc, 
            'entidad_fed':entidad_fed, 'anio_ej':anio_ej, 'proc_exc':proc_exc, 'fecha_pub':fecha_pub, 
            'claves_list':claves_list, 'part_testigo':part_testigo, 'abastecimiento_sim':abastecimiento_sim, 
            'plurianual':plurianual, 'tipo_cont':tipo_cont, 'anticipo':anticipo, 'forma_pago':forma_pago, 
            'plazo_garant':plazo_garant, 'meses_garant':meses_garant,'garant_cump':garant_cump, 'caracter':caracter, 'caso_fort ':caso_fort , 
            'tipo_cont_abierto':tipo_cont_abierto, 'uri':uri, 'scrapped_day':today
        }


def get_text_from_column(columns, indice:int, required:bool=False):
    try:
        txt = columns[indice].text.strip()
        return txt
    
    except:
        if required:
            return False
        else:
            return "falló"


def get_page_prices():
    global driver, anuncio, today
    
    #Esto debido a que a veces economicos no cargaba, y aveces trae un layout distinto
    
    xp_1 = '//th[text()="Descripción CUCoP+"]/ancestor::div[contains(@class,"header")]/following-sibling::div/table//tr'
    xp_2 = '//th[text()="Descripción CUCoP+"]/ancestor::thead/following-sibling::tbody/tr'
    xp_economicos = xp_1
    economicos = driver.find_elements(By.XPATH, xp_1)
    iterations = 0
    if len(economicos)<1:
        print(Fore.YELLOW + '  No cargaron economicos, se esperará')
        while True:
            economicos = driver.find_elements(By.XPATH, xp_2)
            if len(economicos)>0:
                xp_economicos = xp_2
                print(Fore.YELLOW + f"   economicos tipo 2")
                break

            duerme(3)

            economicos = driver.find_elements(By.XPATH, xp_1)
            if len(economicos)>0:
                xp_economicos = xp_1
                break
            
            iterations += 1
            if iterations>10:
                print(Fore.YELLOW + '   No cargaron.')
                break

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    duerme(.7, 1.5)
    #oportunnity url
    uri = driver.current_url
    #Código del expediente
    cod_exp = get_text_by_xpath(xp='//label[text()="Código del expediente:"]/following-sibling::label', required=True)
    #Número de procedimiento de contratación
    num_proc = get_text_by_xpath(xp='//label[text()="Número de procedimiento de contratación:"]/following-sibling::label', required=True)
    #Dependencia (SOLO TEXTO DESPUÉS DEL GUIÓN “-”)
    dependencia = get_text_by_xpath(xp='//label[text()="Dependencia o Entidad:"]/following-sibling::label')
    # Año del ejercicio presupuestal
    anio_ej = get_text_by_xpath(xp='//label[text()="Año del ejercicio presupuestal:"]/following-sibling::label')
    # Lista de Claves
    claves_list = get_text_by_xpath(xp='//th[text()="Clave"]/ancestor::thead/following-sibling::tbody/tr/td[1]', join=True)
    #Unidad Compradora (SOLO CÓDIGO IDENTIDICADOR)
    unidad_comp = get_text_by_xpath(xp='//label[text()="Unidad compradora"]/following-sibling::label')
    try:
        num_uc = unidad_comp.split(" ", 1)[0]
        nom_uc = unidad_comp.split(" ", 1)[1]
    except:
        num_uc = ""
        nom_uc = unidad_comp

    # Fecha y hora de publicación:
    fecha_pub = get_text_by_xpath(xp='//label[text()="Fecha y hora de publicación:"]/following-sibling::label')
    if fecha_pub:
        try:
            fecha_pub = datetime.strptime(fecha_pub, "%d/%m/%Y %H:%M").strftime("%d/%m/%Y %H:%M")
        except:
            print(f"Error formateando la fecha {fecha_pub} de la op:\n{uri}")
            fecha_pub = today
        
    # --ECONOMICOS--
    print("  Obteniendo economicos")
    economicos_list = []
    economicos = driver.find_elements(By.XPATH, xp_economicos)
    for row_economic in economicos:
        col = row_economic.find_elements(By.XPATH,"./td")
        partida_esp = col[1].text
        clave_cucop = col[2].text
        desc_cucop = col[3].text
        desc_det = col[4].text
        unidades_medida = col[5].text
        cantidad_solicitada = col[6].text if len(col)>6 else ""
        claves_compendio = re.findall(r"\d{3,4}.{1}\d{3,4}.{1}\d{3,4}.?\d{0,2}", desc_cucop)#CUCOP
        clave_compendio = claves_compendio[0].strip().replace(" ",".") if len(claves_compendio)>0 else ""
        
        economicos_list.append({
            "Clave compendio":clave_compendio, "Codigo del expediente":cod_exp, "Número del procedimiento o contratación":num_proc,
            "Partida específica":partida_esp, "Clave CUCoP+":clave_cucop, "Descripción CUCoP+": desc_cucop, 
            "Descripción detallada":desc_det, "Unidad de medida":unidades_medida, "Cantidad solicitada":cantidad_solicitada,
            "uri":uri, "scrapped_day":today
        })
    
    # --DATOS RELEVANTES DE CONTRATO - PRECIOS--
    print("  Obteniendo precios")
    datos_relevantes_cont = []
    xp = '//th[text()="Número de contrato"]/ancestor::div[contains(@class,"header")]/following-sibling::div/table//tr'
    datos_cont_rows = driver.find_elements(By.XPATH, xp )
    for dato in datos_cont_rows:
        col = dato.find_elements(By.XPATH,"./td")
        proveedor = col[1].text
        num_cont = col[2].text
        fecha_ini = col[5].text
        fecha_fin = col[6].text
        #titulo_cont = col[3].tex
        
        ActionChains(driver).scroll_to_element(col[2]).move_to_element(col[2])\
                            .pause(1).click().perform()
        try:
            xp = '//*[contains(text(),"Código de contrato: ")]/parent::label/following-sibling::p-table'
            WebDriverWait(driver, 120).until(EC.visibility_of_element_located((By.XPATH, xp)))
        except TimeoutException:
            print(Fore.YELLOW + f"no cargó {num_cont}")
            continue

        #Obtiene las filas de la tabla de detalle(cada fila se dividide en dos columnas grandotas)
        detalles = driver.find_elements(By.XPATH, 
            '//*[contains(text(),"Código de contrato: ")]/parent::label/following-sibling::p-table//div[contains(@class,"unfrozen")]//tbody/tr')
        detalles_p = driver.find_elements(By.XPATH, 
            '//*[contains(text(),"Código de contrato: ")]/parent::label/following-sibling::p-table//div[contains(@class,"-frozen")]//tbody/tr')
        for clave, detalle in zip(detalles_p, detalles):
            col = clave.find_elements(By.XPATH,"./td")
            clave_cucop = col[1].text

            col = detalle.find_elements(By.XPATH,"./td")
            try:
                desc_det = col[0].text
                prec_unit_sin_impuestos = col[3].text
                subtotal = col[4].text
                total = col[7].text 
            except IndexError:
                columnas_anormales = driver.find_elements(By.XPATH, 
                    '//*[contains(text(),"Código de contrato: ")]/parent::label/following-sibling::p-table//div[contains(@class,"unfrozen")]//thead/tr/th')
                anormal_columns = ",".join([c.text for c in columnas_anormales])
                dependencia = "Error::: " + anormal_columns
                desc_det = ""
                prec_unit_sin_impuestos = ""
                subtotal = ""
                total = ""
            
            claves_compendio = [i['Clave compendio'] for i in economicos_list if clave_cucop in i["Clave CUCoP+"]]
            clave_compendio = claves_compendio[0].replace(" ",".") if len(claves_compendio)>0 else ""

            datos_relevantes_cont.append({
                "Clave compendio":clave_compendio, "Clave Cucop":clave_cucop, "Descripción detallada":desc_det,
                "Codigo del expediente":cod_exp,"Número del procedimiento o contratación":num_proc,
                "Dependencia":dependencia,"Número Unidad Compradora":num_uc,"Nombre Unidad Compradora":nom_uc,
                "Fecha y hora de la publicación":fecha_pub,"Año del ejercicio presupuestal":anio_ej,
                "Clave partidas":claves_list,"Proveedor":proveedor,"Número de contrato":num_cont,"Fecha de inicio":fecha_ini,
                "Fecha de fin":fecha_fin, "Importe Unitario sin Impuestos":prec_unit_sin_impuestos,
                "Total Sin IVA":subtotal, "Total con IVA":total,"uri":uri,"scrapped_day":today
            })

        driver.find_element(By.XPATH,'//span[text()="Cerrar"]').click()
        duerme(.5,1.5)

    return economicos_list, datos_relevantes_cont


@timing_val
def scrape_page(page_numb):
    "Itera todos los renglones del landing page"
    global driver,  gobernanza, conc_file_name, procedimientos_guardados,\
        economicos_file_name, precios_file_name, num_proc_added, rows_aded

    # Itera filas del landing page
    rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
    ops_found = len(rows)
    print(f"se encontraron {ops_found} oportunidades en está página")
    for i in range(0, ops_found):
        """ Itera fila por fila del LP,
        busca el numero de procedimiento en la bdd, si ya existe lo omite
        si no le da click para ir a la página de detalle, 
        ahí extrae la información de cada oportunidad, cuando termina
        vuelve al LP, y repite fila por fila.
        """
        rows = driver.find_elements(By.XPATH, '//td[@class="p-link2"]')
        n_proc = rows[i].text

        if procedimientos_guardados['num_proc'].str.contains(n_proc).any() or n_proc in num_proc_added:
            print(f"\nprocedimiento:{i} - {n_proc} ya está en la bdd")
            continue

        # Entra a la página de detalle
        rows[i].click()
        espera_carga_componenete()
        
        print(f"\nExtrayendo información del anuncio {i} - {n_proc}")

        # Extrae información de concluidos.csv
        new_row = get_page_info()

        #Extrae informacion de Economicos.csv y Precios.csv
        try:
            economic_list, datos_relevantes_cont = get_page_prices()
        except Exception as e:
            print(f"  error: {e}")
            new_row['dependencia'] = e[0:55]
            driver.save_screenshot(f"./{str(page_numb)}_{i}_error.png")

        if not new_row['cod_exp'] or not new_row['num_proc']:
            print(f"Error recuperando informacón básica del anuncio: {new_row['uri']}") 
            print(f"codigo de expediente: {new_row['cod_exp']}")
            print(f"numero de exp: {new_row['num_proc']}")
            driver.save_screenshot(f"./{str(page_numb)}_{i}_error.png")
        else:
            df = pd.DataFrame([new_row])
            df.to_csv(conc_file_name, index=False, header=False, encoding='utf-8', mode='a')

            if economic_list:
                df = pd.DataFrame(economic_list)
                df.to_csv(economicos_file_name, index=False, header=False, encoding='utf-8', mode='a')
                print("  SE EXTRAJO Y GUARDÓ INFORMACIÓN DE ECONOMICOS.")
            else:
                print("  ", economic_list)

            if datos_relevantes_cont:                
                df = pd.DataFrame(datos_relevantes_cont)
                df.to_csv(precios_file_name, index=False, header=False, encoding='utf-8', mode='a')
                print("  SE EXTRAJO Y GUARDÓ INFORMACIÓN DE PRECIOS.")
            else:
                print("  ", datos_relevantes_cont)
                
            num_proc_added.append(new_row['num_proc'])
            rows_aded += 1

        driver.back()
        espera_carga_componenete()

        if rows_aded > gobernanza:
            raise Exception("Se alcanzo el númeor máximo de oportunidades por ejecución.")
        
        duerme(.5, 2)


def paginate():
    global driver, main_url, gobernanza

    print(f"Entrando a la pagina principal: {main_url}")
    driver.get(main_url)
    espera_carga_componenete()

    print("\nAnuncios concluidos")
    click('//*[text()="Anuncios concluidos"]', dormir=False)
    espera_carga_componenete()

    print("\nSeteando filtros")
    set_filters()
    
    #PAGINACIÓN
    for i in range(1, 10):
        print(f"\nObteniendo información pag {i}")
        scrape_page(i)

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
    global main_url, today, driver, anexos_dir,anuncio, gobernanza, claves, conc_file_name,\
           rows_aded, procedimientos_guardados, economicos_file_name, precios_file_name,\
            anexos_full_dir, anexos_file_name, num_proc_added
    
    num_proc_added = []
    anuncio = {} #Sirve para anexos
    anexos_full_dir = r"C:\Users\juan-\Desktop\CNET Scrapping 2024\temp\\"

    rows_aded = 0
    gobernanza = 220
    today = date.today().strftime("%d/%m/%Y")
    conc_file_name = './concluidos.csv'
    anexos_file_name = './anexos.csv'
    economicos_file_name = './economicos.csv'
    precios_file_name = './precios.csv'
    anexos_dir = './temp'
    
    main_url = 'https://upcp-compranet.hacienda.gob.mx/sitiopublico/#/'
    
    claves = ["25401","25301","25501","32401","53101","53201"]
    #claves = ["25401"]#Para ahorrar tiempo en pruebas !Borrar!
    
    print("\nCargando el dataset de oportunidades guardadas...")
    procedimientos_guardados = pd.read_csv(conc_file_name, usecols = ['num_proc'])

    print("\nInicializando driver <----")
    set_driver()

    print("\nInicia proceso de scrapping - paginacion <----")
    paginate()


if __name__ == "__main__":
    print(datetime.today().strftime("%d/%m/%Y %H:%M:%S"))

    prueba = True
    if prueba:
        main()
        print(datetime.today().strftime("%d/%m/%Y %H:%M:%S"))
        driver.close()
    else:
        try:
            main()
            driver.close()
        except Exception as e:
            print(datetime.today().strftime("%d/%m/%Y %H:%M:%S"))
            print(f"error: {e}")
            if driver:
                driver.save_screenshot("./MAIN_error.png")
                driver.close()
