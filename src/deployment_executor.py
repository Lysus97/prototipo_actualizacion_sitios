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
            # Loguear toda la configuración para depuración
            self.logger.info("Configuración completa recibida:")
            for key, value in site_config.items():
                self.logger.info(f"{key}: {value}")

            # Nombre del proyecto - IMPORTANTE: usar el prefijo correcto
            project_name = site_config.get('upd.environment1.war.name', '')
            
            self.logger.info(f"Nombre del proyecto extraído: '{project_name}'")
            
            if not project_name:
                raise ValueError("No se pudo extraer el nombre del proyecto. Verifica la configuración.")
            
            # Rutas de Tomcat
            tomcat_home = r'C:\Program Files\Apache Software Foundation\Tomcat 9.0'
            webapps_dir = os.path.join(tomcat_home, 'webapps')
            
            # Usar SVNManager para checkout
            svn_manager = SVNManager(logger=self.logger)
            
            try:
                # 1. Hacer checkout del proyecto
                project_path = svn_manager.checkout_project(project_name)
                self.logger.info(f"Checkout completado en: {project_path}")
                
                # 2. Verificar pom.xml
                pom_path = os.path.join(project_path, 'pom.xml')
                if not os.path.exists(pom_path):
                    raise FileNotFoundError(f"No se encontró pom.xml en {project_path}")
                
                # Después de verificar pom.xml
                maven_home = r'C:\Program Files\Apache Software Foundation\apache-maven-3.9.8'
                maven_cmd = 'mvn clean package -DskipTests=true'
                if os.name == 'nt':  # Windows
                    maven_cmd = f'"{os.path.join(maven_home, "bin", "mvn.cmd")}" clean package -DskipTests=true'
                
                # 3. Ejecutar Maven con todas las variables de entorno necesarias
                maven_env = dict(os.environ)
                maven_env.update({
                    'JAVA_HOME': r'C:\Program Files\Java\jdk-17',
                    'M2_HOME': maven_home,
                    'PATH': f"{maven_env.get('PATH', '')};{os.path.join(maven_home, 'bin')}"
                })

                # Configurar entorno para Maven
                maven_env = os.environ.copy()
                maven_env.update({
                    'JAVA_HOME': r'C:\Program Files\Java\jdk-17',
                    'M2_HOME': maven_home,
                    'PATH': f"{maven_env.get('PATH', '')};{os.path.join(maven_home, 'bin')}"
                })
                
                self.logger.info("Iniciando build con Maven...")
                self.logger.info(f"Comando Maven: {maven_cmd}")
                
                build_result = subprocess.run(
                    maven_cmd,
                    cwd=project_path,
                    env=maven_env,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Log detallado de la compilación
                self.logger.info(f"Build Maven - Código de retorno: {build_result.returncode}")
                self.logger.info(f"Build Maven - STDOUT:\n{build_result.stdout}")
                
                if build_result.returncode != 0:
                    self.logger.error(f"Error en build Maven:\n{build_result.stderr}")
                    return False
                
                # 4. Buscar el WAR generado en la carpeta target
                war_path = os.path.join(project_path, 'target', f"{project_name}-0.0.1-SNAPSHOT.war")
                if not os.path.exists(war_path):
                    # Intentar encontrar cualquier WAR en el directorio target
                    target_dir = os.path.join(project_path, 'target')
                    self.logger.info(f"Buscando WARs en: {target_dir}")
                    wars = [f for f in os.listdir(target_dir) if f.endswith('.war') and not f.endswith('.original')]
                    
                    if wars:
                        war_path = os.path.join(target_dir, wars[0])
                        self.logger.info(f"WAR encontrado: {war_path}")
                    else:
                        self.logger.error(f"No se encontraron WARs en: {target_dir}")
                        return False
                
                # 5. Preparar el despliegue en Tomcat
                destination_war = os.path.join(webapps_dir, f"{project_name}.war")  # Simplificamos el nombre para Tomcat
                
                # 6. Hacer backup si existe
                if os.path.exists(destination_war):
                    backup_path = f"{destination_war}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                    shutil.copy2(destination_war, backup_path)
                    self.logger.info(f"Backup creado en: {backup_path}")
                
                # 7. Detener Tomcat
                self._execute_tomcat_command('stop', tomcat_home)
                
                # 8. Copiar nuevo WAR
                shutil.copy2(war_path, destination_war)
                self.logger.info(f"WAR desplegado en: {destination_war}")
                
                # 9. Iniciar Tomcat
                self._execute_tomcat_command('start', tomcat_home)
                
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
                # Primero intentar detener gracefully
                shutdown_cmd = [os.path.join(tomcat_home, 'bin', 'shutdown.bat')]
                
                # Si falla, matar el proceso por puerto
                kill_cmd = ['taskkill', '/F', '/IM', 'java.exe']
                
                for cmd in [shutdown_cmd, kill_cmd]:
                    try:
                        self.logger.info(f"Intentando {action} Tomcat con: {' '.join(cmd)}")
                        subprocess.run(cmd, shell=True, timeout=30)
                        time.sleep(5)  # Dar tiempo a que se detenga
                    except:
                        continue
                        
                return True
                
            elif action == 'start':
                startup_cmd = os.path.join(tomcat_home, 'bin', 'startup.bat')
                subprocess.run(startup_cmd, shell=True)
                time.sleep(10)  # Dar tiempo a que inicie
                return True
                
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