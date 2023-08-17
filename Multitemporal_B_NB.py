import geopandas as gpd
import pandas as pd
import os
import psutil
def multitemporal(direccion_carpeta, carpeta_salida, year1, year2, year3, year4, year5, year6, year7, year8, year9, year10):
    dict_path = {"year1" : year1, "year2" : year2, "year3" : year3, "year4" : year4, "year5" : year5,
                 "year6" : year6, "year7" : year7, "year8" : year8, "year9" : year9, "year10" : year10}
    dict_files = dict()
    for year, path in dict_path.items():
        if len(path[0]) > 0:
            file = gpd.read_file(os.path.join(direccion_carpeta, path[0]))
            file[year] = file[path[1]].str.upper().str.strip()
            columns = [year, 'geometry']
            filtered = file[columns]
            dict_files[year] = filtered
    multitemporal = dict()
    traslape = gpd.overlay(dict_files['year1'], dict_files['year2'], how='intersection', keep_geom_type = False)
    traslape = traslape.explode()
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
    traslape['CATEGORIA1'] = traslape.apply(primer_periodo, axis = 1)
    traslape['AREA1_HA'] = traslape['geometry'].area/10000.0
    filtrado1 = traslape[traslape['geometry'].geom_type == 'Polygon']
    multitemporal['Periodo1'] = filtrado1
    for i in range(2, len(dict_files),1):
        periodo_file = 'Periodo{}'.format(i-1)
        filtered_rows = multitemporal[periodo_file]['geometry'].apply(lambda geom: geom.geom_type == 'Polygon')
        result = multitemporal[periodo_file][filtered_rows]
        traslape = gpd.overlay(result, dict_files['year{}'.format(i+1)],
                               how='intersection', keep_geom_type = False)
        traslape = traslape.explode()
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
        multitemporal['Periodo{}'.format(i)] = filtrado
    salida = os.path.join(carpeta_salida, "Multitemporal")
    def archivo_en_uso(file_path):
        for process in psutil.process_iter():
            try:
                for file in process.open_files():
                    if file_path == file.path:
                        return True
            except(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    for key, file in multitemporal.items():
        if not os.path.exists(salida):
            os.makedir(salida)
        output_file_path = os.path.join(salida, key)
        if archivo_en_uso(output_file_path):
            print(f"El archivo {output_file_path} está en uso. Ciérrelo para continuar.")
        else:
            multitemporal[key].to_file(output_file_path)
            print(f"Archivo guardado exitosamente: {output_file_path}")
    return multitemporal
    

        

