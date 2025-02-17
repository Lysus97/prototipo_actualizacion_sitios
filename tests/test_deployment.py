import sys
import os
import logging

# Añadir el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Imprimir rutas para depuración
print(f"Python Path: {sys.path}")

# Importaciones
from src.config_reader import read_sites_excel, validate_environment_config
from src.deployment_executor import DeploymentExecutor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_deployment():
    try:
        # Ruta al archivo Excel de configuración
        excel_path = os.path.join(project_root, 'config', 'sites_config.xlsx')
        
        # Verificar existencia del archivo Excel
        if not os.path.exists(excel_path):
            print(f"Error: Archivo Excel no encontrado en {excel_path}")
            return
        
        # Leer configuraciones de sitios
        sites_configs = read_sites_excel(excel_path)
        
        # Probar cada configuración de sitio
        for site_config in sites_configs:
            print("\n--- Probando configuración de sitio ---")
            # Validar y añadir prefijos
            validated_config = validate_environment_config(site_config)
            
            # Imprimir configuración validada para verificación
            print("Configuración validada:")
            for key, value in validated_config.items():
                print(f"{key}: {value}")
            
            # Inicializar ejecutor de despliegue
            executor = DeploymentExecutor()
            
            # Simular despliegue (puedes comentar pasos reales si no quieres ejecutarlos)
            result = executor.execute_site_deployment(validated_config)
            
            # Imprimir resultado
            print("\nResultado de despliegue:")
            print(f"Éxito: {result.get('success', False)}")
            
            # Mostrar detalles de los pasos
            for step, step_result in result.get('steps', {}).items():
                print(f"{step}: {step_result}")
    
    except Exception as e:
        print(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_deployment()