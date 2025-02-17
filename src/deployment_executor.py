import sys
import os
import subprocess
import logging
import shutil
import time
from datetime import datetime
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
            # Nombre del proyecto
            project_name = site_config.get('upd.environment1.war.name', '')
            
            # Rutas de Tomcat
            tomcat_home = os.path.join('C:\\', 'Program Files', 'Apache Software Foundation', 'Tomcat 9.0')
            webapps_dir = os.path.join(tomcat_home, 'webapps')
            
            # Verificar estado de Tomcat
            def is_tomcat_running():
                try:
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq java.exe'],
                        capture_output=True, 
                        text=True, 
                        shell=True
                    )
                    return 'tomcat' in result.stdout.lower()
                except Exception:
                    return False
            # Usar SVNManager para checkout
            svn_manager = SVNManager(logger=self.logger)
            
            try:
                # 1. Hacer checkout del proyecto
                project_path = svn_manager.checkout_project(project_name)
                
                # 2. Buscar WAR generado
                target_dir = os.path.join(project_path, 'target')
                wars = [
                    f for f in os.listdir(target_dir) 
                    if f.endswith('.war') and 
                    not f.endswith('.original') and 
                    f.startswith(project_name)
                ]

                if not wars:
                    self.logger.error(f"No se encontraron WARs en: {target_dir}")
                    return False

                war_path = os.path.join(target_dir, wars[0])
                destination_war = os.path.join(webapps_dir, f"{project_name}.war")
                
                # 3. Preparar despliegue
                # Intentar detener Tomcat solo si está corriendo
                if is_tomcat_running():
                    self.logger.info("Tomcat está corriendo. Intentando detener...")
                    stop_result = self._execute_tomcat_command('stop', tomcat_home)
                    if not stop_result:
                        self.logger.warning("No se pudo detener Tomcat completamente")
                
                # 4. Gestionar backup y despliegue de WAR
                def remove_existing_war():
                    try:
                        if os.path.exists(destination_war):
                            # Intentar eliminar el WAR existente
                            os.remove(destination_war)
                            # También eliminar el directorio descomprimido si existe
                            webapp_dir = destination_war.replace('.war', '')
                            if os.path.exists(webapp_dir):
                                shutil.rmtree(webapp_dir)
                    except Exception as e:
                        self.logger.error(f"Error al eliminar WAR existente: {e}")
                        return False
                    return True

                # Intentar eliminar WAR existente
                if not remove_existing_war():
                    self.logger.error("No se pudo eliminar WAR existente")
                    return False
                
                # 5. Copiar nuevo WAR
                try:
                    shutil.copy2(war_path, destination_war)
                    self.logger.info(f"WAR desplegado en: {destination_war}")
                except Exception as copy_error:
                    self.logger.error(f"Error al copiar WAR: {copy_error}")
                    return False
                
                # 6. Iniciar Tomcat
                start_result = self._execute_tomcat_command('start', tomcat_home)
                if not start_result:
                    self.logger.warning("No se pudo iniciar Tomcat completamente")
                
                return True
                
            except Exception as build_error:
                self.logger.error(f"Error en proceso de build/deploy: {str(build_error)}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error general en operaciones Tomcat: {str(e)}")
            return False
    def _execute_tomcat_command(self, action: str, tomcat_home: str):
        try:
            if action == 'stop':
                # Intentar detener de múltiples formas
                stop_methods = [
                    [os.path.join(tomcat_home, 'bin', 'shutdown.bat')],
                    ['taskkill', '/F', '/IM', 'java.exe', '/FI', 'WINDOWTITLE eq Apache Tomcat'],
                    ['net', 'stop', '"Apache Tomcat 9.0 Tomcat9"']
                ]

                for method in stop_methods:
                    try:
                        self.logger.info(f"Intentando detener Tomcat con: {' '.join(method)}")
                        result = subprocess.run(
                            method, 
                            capture_output=True, 
                            text=True,
                            shell=True,
                            timeout=30
                        )
                        
                        # Condiciones de éxito más flexibles
                        if result.returncode == 0:
                            self.logger.info(f"Método de detención exitoso: {' '.join(method)}")
                            time.sleep(5)  # Dar tiempo para detener
                            return True
                        
                        # Log de salida en caso de fallo
                        self.logger.warning(f"Método fallido. Código: {result.returncode}")
                        self.logger.warning(f"STDOUT: {result.stdout}")
                        self.logger.warning(f"STDERR: {result.stderr}")

                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"Timeout en método: {method}")
                    except Exception as cmd_error:
                        self.logger.warning(f"Error con método: {cmd_error}")

                # Si ningún método funciona
                self.logger.error("No se pudo detener Tomcat por ningún método")
                return False
                    
            elif action == 'start':
                startup_scripts = [
                    os.path.join(tomcat_home, 'bin', 'startup.bat'),
                    'net start "Apache Tomcat 9.0 Tomcat9"'
                ]

                for script in startup_scripts:
                    try:
                        self.logger.info(f"Intentando iniciar Tomcat con: {script}")
                        result = subprocess.run(
                            script, 
                            capture_output=True, 
                            text=True, 
                            shell=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            self.logger.info(f"Iniciado exitosamente con: {script}")
                            time.sleep(10)  # Dar tiempo para iniciar
                            return True
                        
                        self.logger.warning(f"Método de inicio fallido: {script}")
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"Timeout al iniciar: {script}")
                    except Exception as start_error:
                        self.logger.warning(f"Error al iniciar: {start_error}")

                self.logger.error("No se pudo iniciar Tomcat")
                return False
                    
        except Exception as e:
            self.logger.error(f"Error en {action} Tomcat: {str(e)}")
            return False
    def _deploy_war(self, site_config, webapps_dir):
        """
        Desplegar nuevo archivo WAR
        """
        try:
            # Obtener nombre del WAR de la configuración
            war_name = site_config.get('war.name', '')
            
            # Imprimir información de depuración
            self.logger.info(f"Buscando WAR para: {war_name}")
            self.logger.info(f"Directorio de trabajo actual: {os.getcwd()}")
            
            # Rutas potenciales para encontrar el WAR
            possible_paths = [
                os.path.join(os.getcwd(), 'target', f"{war_name}.war"),
                os.path.join(os.getcwd(), 'build', f"{war_name}.war"),
                os.path.join(os.getcwd(), f"{war_name}.war"),
                os.path.join(os.path.dirname(os.getcwd()), 'target', f"{war_name}.war"),
                os.path.join(os.path.dirname(os.getcwd()), 'build', f"{war_name}.war")
            ]
            
            # Buscar y loguear todas las rutas
            for path in possible_paths:
                self.logger.info(f"Verificando ruta: {path}")
                if os.path.exists(path):
                    self.logger.info(f"WAR encontrado en: {path}")
                    source_war = path
                    break
            else:
                # Si no se encuentra el WAR, listar contenido de directorios
                self.logger.error("Contenido del directorio actual:")
                for item in os.listdir(os.getcwd()):
                    self.logger.error(f"- {item}")
                
                raise FileNotFoundError(f"No se encontró el archivo WAR para {war_name}")
            
            # Resto del código de despliegue...
        except Exception as e:
            self.logger.error(f"Error al desplegar WAR: {str(e)}")
            raise

    def _backup_war(self, war_path):
        """
        Crear backup del archivo WAR existente
        """
        try:
            # Generar ruta de backup con timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{war_path}.{timestamp}.bak"
            
            # Importar shutil para copiar archivos
            import shutil
            
            # Crear backup
            shutil.copy2(war_path, backup_path)
            
            self.logger.info(f"Backup de WAR creado en: {backup_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error al crear backup de WAR: {str(e)}")
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