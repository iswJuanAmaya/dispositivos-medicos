import pandas as pd

#CUIDADO ESTO ES PARA REFERENCIA, EJECUTAR ESTE SCRIPT PUEDE BORRAR ARCHIVOS YA CON INFORMACIÓN.

#crea el layout del csv de oportunidades
df = pd.DataFrame(columns=['cod_exp','num_proc','dependencia','unidad_comp','correo','nombre_procedimiento',
                        'tipo_proc','entidad_fed','anio_ej','proc_exc','fecha_pub','claves_list','part_testigo',
                        'abastecimiento_sim','plurianual','tipo_cont','anticipo','forma_pago','plazo_garant',
                        'meses_garant','garant_cump','caracter','caso_fort ','tipo_cont_abierto','uri','scrapped_day'])
df.to_csv('concluidos.csv', index=False, encoding='utf-8', header=True)
del df

#crea el csv con el layout final de 
df = pd.DataFrame(columns=['cod_exp','num_proc','anexo','scrapped_day'])
df.to_csv('anexos.csv', index=False, encoding='utf-8', header=True)

"""
'cod_exp','num_proc','dependencia','unidad_comp','correo','nombre_procedimiento',
'tipo_proc','entidad_fed','anio_ej','proc_exc','fecha_pub','claves_list','part_testigo',
'abastecimiento_sim','plurianual','tipo_cont','anticipo','forma_pago','plazo_garant',
'meses_garant','caracter','caso_fort ','tipo_cont_abierto','uri'

-Código del expediente
-Número de procedimiento de contratación
-Dependencia (SOLO TEXTO DESPUÉS DEL GUIÓN “-”)
-Unidad Compradora (SOLO CÓDIGO IDENTIDICADOR)
-Correo electrónico Unidad compradora
-Nombre del procedimiento de contratación
-Tipo de procedimiento
-Entidad Federativa
-Año del ejercicio presupuestal
-Procedimiento exclusivo para MiPymes
-Fecha de Publicación
-Lista de Claves
-Participación de Testigo Social
-Abastecimiento simultaneo
-Plurianual
-Tipo de contratación
-Anticipo
-Forma de Pago
-Plazo para entrega de garantía
-Número de meses para la garantía
-Carácter
-Caso fortuito o fuerza mayor
-Tipo de contrato abierto
-Garantía de cumplimiento
"""

