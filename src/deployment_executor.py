import sys
import os
import subprocess
import logging
from typing import Dict, Any

# Añadir la ruta del proyecto al sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Importación absoluta
from src.svn_manager import SVNManager

class DeploymentExecutor:
    def __init__(self, logger: logging.Logger = None):
        """
        Inicializa el ejecutor de despliegues.
        
        :param logger: Logger opcional. Si no se proporciona, se crea uno por defecto.
        """
        # Configurar logging
        self.logger = logger or self._create_default_logger()

    def _create_default_logger(self) -> logging.Logger:
        """
        Crea un logger por defecto si no se proporciona uno.
        
        :return: Instancia de logging.Logger configurada
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def execute_site_deployment(self, site_config: Dict) -> Dict:
        """
        Ejecuta el proceso completo de despliegue de un sitio.
        
        :param site_config: Diccionario con la configuración del sitio
        :return: Diccionario con resultados del despliegue
        """
        deployment_result = {
            'success': False,
            'steps': {}
        }

        try:
            # 1. Gestionar operaciones de SVN
            svn_result = self._manage_svn_operations(site_config)
            deployment_result['steps']['svn_operations'] = svn_result

            # 2. Preparar despliegue en Tomcat
            tomcat_result = self._prepare_tomcat_deployment(site_config)
            deployment_result['steps']['tomcat_deployment'] = tomcat_result

            # 3. Gestionar operaciones de Tomcat
            tomcat_operations_result = self._manage_tomcat_operations(site_config)
            deployment_result['steps']['tomcat_operations'] = tomcat_operations_result

            # Si todos los pasos son exitosos
            deployment_result['success'] = (
                svn_result.get('success', False) and 
                tomcat_result.get('success', False) and 
                tomcat_operations_result
            )

            self.logger.info(f"Despliegue completado {'exitosamente' if deployment_result['success'] else 'con errores'}")

        except Exception as e:
            self.logger.error(f"Despliegue fallido: {str(e)}")
            deployment_result['error'] = str(e)
        
        return deployment_result

    def _manage_svn_operations(self, site_config: Dict) -> Dict:
        """
        Maneja las operaciones de SVN para el despliegue.
        
        :param site_config: Configuración del sitio
        :return: Resultado de las operaciones de SVN
        """
        try:
            # Inicializar SVNManager con el logger
            svn_manager = SVNManager(logger=self.logger)
            
            # Realizar checkout/update
            checkout_result = svn_manager.handle_svn_operations(site_config)
            
            # Crear tag de release
            tag_result = svn_manager.create_release_tag(site_config)
            
            return {
                'success': checkout_result and tag_result,
                'checkout': checkout_result,
                'tag_creation': tag_result
            }
        
        except Exception as e:
            self.logger.error(f"Error en operaciones SVN: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _prepare_tomcat_deployment(self, site_config: Dict) -> Dict:
        """
        Prepara el despliegue para Tomcat basándose en la configuración.
        
        :param site_config: Configuración del sitio
        :return: Resultado de la preparación de despliegue
        """
        try:
            # Extraer información de Tomcat de la configuración
            tomcat_url = site_config.get('tomcat.url', '')
            tomcat_host = site_config.get('tomcat.host', '')
            tomcat_modules = site_config.get('tomcat.modules', '')
            
            # Aquí irían los pasos de preparación para Tomcat
            # Por ejemplo, compilar el proyecto, preparar WAR, etc.
            
            self.logger.info(f"Preparando despliegue para Tomcat: {tomcat_host}")
            
            return {
                'success': True,
                'tomcat_url': tomcat_url,
                'tomcat_host': tomcat_host,
                'modules': tomcat_modules
            }
        
        except Exception as e:
            self.logger.error(f"Error en preparación de despliegue Tomcat: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _manage_tomcat_operations(self, site_config: Dict) -> bool:
        try:
            # Rutas de Tomcat
            tomcat_home = r'C:\Program Files\Apache Software Foundation\Tomcat 9.0'
            webapps_dir = os.path.join(tomcat_home, 'webapps')
            
            # Nombres de archivos
            war_name = site_config.get('war.name', '')
            context_path = site_config.get('context.path', '')
            
            # Detener Tomcat
            self._stop_tomcat(tomcat_home)
            
            # Backup del WAR actual si existe
            war_path = os.path.join(webapps_dir, f"{war_name}.war")
            if os.path.exists(war_path):
                self._backup_war(war_path)
                
            # Copiar nuevo WAR
            self._deploy_war(site_config, webapps_dir)
            
            # Iniciar Tomcat
            self._start_tomcat(tomcat_home)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error en operaciones Tomcat: {str(e)}")
            return False
        
    def _stop_tomcat(self, tomcat_home):
        """
        Detener el servicio de Tomcat
        """
        try:
            # Usar taskkill para forzar la detención
            cmd = [
                'taskkill', '/F', '/IM', 'java.exe', '/FI', f'"IMAGEPATH={tomcat_home}*"'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0 and 'ERROR: No tasks with specified criteria found.' not in result.stderr:
                raise Exception(f"Error al detener Tomcat: {result.stderr}")
            
            self.logger.info("Tomcat detenido exitosamente")
        except Exception as e:
            self.logger.error(f"Error al detener Tomcat: {str(e)}")
            raise

    def _start_tomcat(self, tomcat_home):
        """
        Iniciar el servicio de Tomcat
        """
        try:
            # Usar startup.bat con verificación
            cmd = [
                os.path.join(tomcat_home, 'bin', 'startup.bat')
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                raise Exception(f"Error al iniciar Tomcat: {result.stderr}")
            
            self.logger.info("Tomcat iniciado exitosamente")
        except Exception as e:
            self.logger.error(f"Error al iniciar Tomcat: {str(e)}")
            raise

    def _backup_war(self, war_path):
        """
        Crear backup del archivo WAR existente
        """
        try:
            backup_path = f"{war_path}.bak"
            import shutil
            shutil.copy2(war_path, backup_path)
            self.logger.info(f"Backup de WAR creado en: {backup_path}")
        except Exception as e:
            self.logger.error(f"Error al crear backup de WAR: {str(e)}")
            raise

    def _deploy_war(self, site_config, webapps_dir):
        """
        Desplegar nuevo archivo WAR
        """
        try:
            war_name = site_config.get('war.name', '')
            # Suponiendo que tienes el WAR en un directorio específico
            source_war = os.path.join(os.getcwd(), 'target', f"{war_name}.war")
            
            if not os.path.exists(source_war):
                raise FileNotFoundError(f"Archivo WAR no encontrado: {source_war}")
            
            # Copiar WAR a directorio de webapps
            destination_war = os.path.join(webapps_dir, f"{war_name}.war")
            import shutil
            shutil.copy2(source_war, destination_war)
            
            self.logger.info(f"WAR desplegado: {destination_war}")
        except Exception as e:
            self.logger.error(f"Error al desplegar WAR: {str(e)}")
            raise

def main():
    """
    Ejemplo de uso del DeploymentExecutor
    """
    import sys
    import os
    import logging

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('deployment.log')
        ]
    )

    # Importar funciones de configuración
    from config_reader import read_sites_excel, validate_environment_config

    # Ruta al archivo Excel de configuración
    # NOTA: Ajusta esta ruta según la ubicación real de tu archivo Excel
    excel_path = os.path.join(os.path.dirname(__file__), 'config', 'sites_config.xlsx')
    
    try:
        # Leer configuraciones de sitios desde el Excel
        sites_configs = read_sites_excel(excel_path)
        
        # Ejecutar despliegue para cada sitio
        for site_config in sites_configs:
            # Validar y añadir prefijos a la configuración
            validated_config = validate_environment_config(site_config)
            
            # Inicializar y ejecutar despliegue
            executor = DeploymentExecutor()
            result = executor.execute_site_deployment(validated_config)
            
            # Imprimir resultado detallado
            print("\n--- Resultado de Despliegue ---")
            print(f"Éxito: {result['success']}")
            for step, step_result in result['steps'].items():
                print(f"{step}: {step_result}")
    
    except Exception as e:
        logging.error(f"Error en el proceso de despliegue: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()