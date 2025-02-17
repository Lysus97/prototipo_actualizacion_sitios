from typing import List, Dict
import pandas as pd
import logging

def read_sites_excel(excel_path: str) -> List[Dict]:
    """
    Lee y valida el archivo Excel con las configuraciones de los sitios.
    
    Args:
        excel_path (str): Ruta al archivo Excel
        
    Returns:
        List[Dict]: Lista de diccionarios con la configuración de cada sitio
    """
    try:
        # Leer el Excel
        df = pd.read_excel(excel_path)
        
        # Lista de columnas requeridas
        required_columns = [
            'dao.db',
            'jdbc.URL',
            'tomcat.url',
            'tomcat.host',
            'war.name',          # Nombre del WAR a desplegar
            'context.path',      # Path en Tomcat (ej: /sitios_uno)
            'db.user',           # Usuario BD
            'db.password'        # Password BD
        ]
        
        # Verificar columnas requeridas
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Columnas faltantes en el Excel: {missing_columns}")
            
        # Convertir DataFrame a lista de diccionarios
        sites_config = df.to_dict('records')
        
        return sites_config
        
    except Exception as e:
        raise Exception(f"Error al leer el archivo Excel: {str(e)}")

def validate_environment_config(site_config: Dict) -> Dict:
    """
    Valida y clasifica la configuración de un sitio.
    
    Args:
        site_config (Dict): Diccionario con la configuración del sitio
        
    Returns:
        Dict: Configuración validada y con prefijos añadidos
    """
    try:
        # Determinar tipo de base de datos
        db_type = site_config.get('dao.db', '').upper()
        if 'ORACLE' in db_type:
            prefix = 'upd.environment1'
            db_scripts_path = 'src/main/resources/db/oracle'
        elif 'SQLSERVER' in db_type or 'MSSQL' in db_type:
            prefix = 'upd.environment2'
            db_scripts_path = 'src/main/resources/db/sqlserver'
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
            
        # Añadir prefijos a las propiedades
        prefixed_config = {
            f"{prefix}.{key}": value 
            for key, value in site_config.items()
        }
        
        # Agregar ruta de scripts
        prefixed_config['db.scripts.path'] = db_scripts_path
        
        return prefixed_config
        
    except Exception as e:
        raise Exception(f"Error al validar la configuración: {str(e)}")