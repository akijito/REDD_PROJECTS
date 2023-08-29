#Importar todas las librerias implementadas en el código
import geopandas as gpd
import pandas as pd
import os
import psutil
#Definir la función con las variables consideradas para el multitemporal
#Se define un máximo de 10 años o coberturas para analizar, sí se poseen más coberturas se debe agregar el año tanto en la función como definir en el archivo "Ejemplo1.ipynb"
def multitemporal(direccion_carpeta, carpeta_salida, year1, year2, year3, year4, year5, year6, year7, year8, year9, year10):
    #Se define un diccionario donde cada uno de los años o coberturas se  trabajan como parametros
    dict_path = {"year1" : year1, "year2" : year2, "year3" : year3, "year4" : year4, "year5" : year5,
                 "year6" : year6, "year7" : year7, "year8" : year8, "year9" : year9, "year10" : year10}
    dict_files = dict()
    #El siguiente bucle lo que hace es usar la información definida en el diccionario "dict_path", abrir cada uno de los archivos
    #Cambiar el formato y seleccionar las columnas que se necesitan para el multitemporal
    for year, path in dict_path.items():
        if len(path[0]) > 0:
            file = gpd.read_file(os.path.join(direccion_carpeta, path[0]))
            file[year] = file[path[1]].str.upper().str.strip()
            columns = [year, 'geometry']
            filtered = file[columns]
            dict_files[year] = filtered
    #La variable "counter" se utiliza para contabilizar los errores detectados y se utiliza igualmente para correr el resto del codigo, donde
    #si se detecta algún error no se procesara y se le dira al usuario donde se encuentra cada uno de los errores
    counter = 0
    for year, file in dict_files.items():
        coberturas_esperadas = ['BOSQUE', 'NO BOSQUE']
        for indice, fila in dict_files[year].iterrows():
            cobertura_fila = fila[year]
            if cobertura_fila not in coberturas_esperadas:
                counter += 1
                print(f"Inconsistencia en la fila {indice}: valor {cobertura_fila} no esperado. Se debe corregir las inconsistencias encontradas en el archivo {year}")
    if counter == 0:
        print("Las coberturas se definieron correctamente.")
        multitemporal = dict()
        #En "tabla_excel" se definen las distintas posibilidades que tiene cada análisis con el fin de exportar en formato excel un resumen 
        tabla_excel = {'BOSQUE ESTABLE':[], 'DEFORESTACION':[], 'REGENERACION':[], 'NO BOSQUE ESTABLE':[], 
                 'BOSQUE ESTABLE 2':[], 'DEFORESTACION 2':[], 'REGENERACION 2':[], 'NO BOSQUE ESTABLE 2':[], 'SIN INFORMACION':[]}
        indices = []
        #"overlay" es una función de geopandas que cumple las mismas funciones que "intersect" en ArcGIS
        traslape = gpd.overlay(dict_files['year1'], dict_files['year2'], how='intersection', keep_geom_type = False)
        traslape = traslape.explode(index_parts = True)
        #La función "primer_periodo" se debe definir incialmente ya que el análisis de los dos primeros años es particular porque se evaluan unicamente
        #coberturas BOSQUE y NO BOSQUE. La función contiene la lógica de las diferentes posibles iteraciones
        def primer_periodo(traslape):
            if traslape['year1'] == "BOSQUE" and traslape['year2'] == "BOSQUE":
                return "BOSQUE ESTABLE"
            if traslape['year1'] == "BOSQUE" and traslape['year2'] == "NO BOSQUE":
                return "DEFORESTACION"
            if traslape['year1'] == "NO BOSQUE" and traslape['year2'] == "BOSQUE":
                return "REGENERACION 2" #Cambiar el nombre
            if traslape['year1'] == "NO BOSQUE" and traslape['year2'] == "NO BOSQUE":
                return "NO BOSQUE ESTABLE 2" #Cambiar el nombre
            else:
                return "SIN INFORMACION"
        #Luego de definr la función se ejecuta, se calcula el área, se filtran las entidades unicamente póligonales
        #igualmente se saca el resumen de la tabla para anexarlo como información dentro del excel final
        traslape['CATEGORIA1'] = traslape.apply(primer_periodo, axis = 1)
        traslape['AREA1_HA'] = traslape['geometry'].area/10000.0
        filtrado1 = traslape[traslape['geometry'].geom_type == 'Polygon']
        filtrado1 = filtrado1[filtrado1['AREA1_HA']>0.0001]
        multitemporal['Periodo1'] = filtrado1
        resumen1 = filtrado1.groupby("CATEGORIA1")['AREA1_HA'].sum()
        resumen1_indices = []
        for i in resumen1.index:
            resumen1_indices.append(i)
        for j, item in tabla_excel.items():
            if j in resumen1_indices:
                tabla_excel[j].append(resumen1[j])
            else:
                tabla_excel[j].append(0)
        indices.append('Periodo1')
        #El siguiente bucle realiza un filtrado de las coberturas generadas con el año a analizar, y recorre cada uno de los años agregados 
        #y los compara con los periodos generados
        for i in range(2, len(dict_files),1):
            periodo_file = 'Periodo{}'.format(i-1)
            filtered_rows = multitemporal[periodo_file]['geometry'].apply(lambda geom: geom.geom_type == 'Polygon')
            result = multitemporal[periodo_file][filtered_rows]
            traslape = gpd.overlay(result, dict_files['year{}'.format(i+1)],
                                   how='intersection', keep_geom_type = False)
            traslape = traslape.explode(index_parts = True)
            #Esta función es para evaluar más de un periodo o más de dos años
            def n_periodos(traslape):
                if traslape['CATEGORIA{}'.format(i-1)] == "BOSQUE ESTABLE" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "BOSQUE ESTABLE"
                if traslape['CATEGORIA{}'.format(i-1)] == "BOSQUE ESTABLE" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "DEFORESTACION"
                if traslape['CATEGORIA{}'.format(i-1)] == "DEFORESTACION" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "REGENERACION"
                if traslape['CATEGORIA{}'.format(i-1)] == "DEFORESTACION" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "NO BOSQUE ESTABLE"
                if traslape['CATEGORIA{}'.format(i-1)] == "REGENERACION" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "BOSQUE ESTABLE"
                if traslape['CATEGORIA{}'.format(i-1)] == "REGENRACION" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "DEFORESTACION"
                if traslape['CATEGORIA{}'.format(i-1)] == "NO BOSQUE ESTABLE" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "REGENERACION"
                if traslape['CATEGORIA{}'.format(i-1)] == "NO BOSQUE ESTABLE" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "NO BOSQUE ESTABLE"
                if traslape['CATEGORIA{}'.format(i-1)] == "BOSQUE ESTABLE 2" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "BOSQUE ESTABLE 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "BOSQUE ESTABLE 2" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "DEFORESTACION 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "DEFORESTACION 2" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "REGENERACION 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "DEFORESTACION 2" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "NO BOSQUE ESTABLE 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "REGENERACION 2" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "BOSQUE ESTABLE 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "REGENERACION 2" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "DEFORESTACION 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "NO BOSQUE ESTABLE 2" and traslape['year{}'.format(i+1)] == "BOSQUE":
                    return "REGENERACION 2"
                if traslape['CATEGORIA{}'.format(i-1)] == "NO BOSQUE ESTABLE 2" and traslape['year{}'.format(i+1)] == "NO BOSQUE":
                    return "NO BOSQUE ESTABLE 2"
                else:
                    return "SIN INFORMACION"
            traslape['CATEGORIA{}'.format(i)] = traslape.apply(n_periodos, axis = 1)
            traslape['AREA{}_HA'.format(i)] = traslape['geometry'].area/10000.0
            filtrado = traslape[traslape['geometry'].geom_type == 'Polygon']
            filtrado = filtrado[filtrado['AREA{}_HA'.format(i)]>0.001]
            multitemporal['Periodo{}'.format(i)] = filtrado
            #Esta parte del código genera la información resumen para la tabla de excel final
            resumen = filtrado.groupby("CATEGORIA{}".format(i))['AREA{}_HA'.format(i)].sum()
            resumen_indices = []
            indices.append('Periodo{}'.format(i))
            for i in resumen.index:
                resumen_indices.append(i)
            for j, item in tabla_excel.items():
                if j in resumen_indices:
                    tabla_excel[j].append(resumen[j])
                else:
                    tabla_excel[j].append(0)
        salida = os.path.join(carpeta_salida, "Multitemporal")
        #Esta función revisa si el archivo se puede sobreescribir, y sí no, le recomienda al usuarión cerrar el archivo donde lo tenga abierto
        #y que vuelva a ejecutar el código
        def archivo_en_uso(file_path):
            for process in psutil.process_iter():
                try:
                    for file in process.open_files():
                        if file_path == file.path:
                            return True
                except(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False
        #Esta parte del código guarda las capas intersectadas
        for key, file in multitemporal.items():
            if not os.path.exists(salida):
                os.mkdir(salida)
            output_file_path = os.path.join(salida, key)
            if archivo_en_uso(output_file_path):
                print(f"El archivo {output_file_path} está en uso. Ciérrelo y ejecute nuevamente el código.")
            else:
                multitemporal[key].to_file(output_file_path, driver='ESRI Shapefile')
                print(f"Archivo guardado exitosamente: {output_file_path}")
        #En esta parte del código se guarda el excel final tipo tabla resumen de las categorias evaluadas
        tabla_resumen = pd.DataFrame(tabla_excel, index=indices)
        tabla_resumen.to_excel(f'{carpeta_salida}/Resumen.xlsx', index=True)
    else:
        print('Revisar las coberturas y corregir las inconsistencias en cuanto a escritura. Se encontraron {} errores'.format(counter))
        multitemporal = None
    return multitemporal
    

        

