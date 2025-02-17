from typing import Dict
import os
import subprocess
import logging

class SVNManager:
    def __init__(self, credentials: Dict = None, logger: logging.Logger = None):
        # Configuración para ambiente local
        self.credentials = credentials or {
            'username': 'hudson',  # Usuario
            'password': 'hudson'   # Password
        }
        self.svn_url = "https://localhost:443/svn/test_repo"
        
        # Configurar logging
        self.logger = logger or logging.getLogger(__name__)

    def handle_svn_operations(self, site_config: Dict) -> bool:
        """
        Gestiona las operaciones de SVN usando las credenciales configuradas.
        
        Args:
            site_config (Dict): Configuración del sitio incluyendo datos SVN
            
        Returns:
            bool: True si las operaciones fueron exitosas
        """
        try:
            # Definir path local para el checkout
            local_path = os.path.join(os.getcwd(), 'svn_temp')
            
            self.logger.info(f"Iniciando operaciones SVN en: {local_path}")

            # Crear directorio si no existe
            os.makedirs(local_path, exist_ok=True)

            # Ejecutar comando SVN
            if not os.path.exists(os.path.join(local_path, '.svn')):
                self.logger.info("Realizando checkout inicial...")
                cmd = [
                    'svn', 'checkout',
                    f"{self.svn_url}/branches/SVE_5_7_1_mhcp",
                    local_path,
                    '--username', self.credentials['username'],
                    '--password', self.credentials['password'],
                    '--non-interactive',
                    '--trust-server-cert'
                ]
            else:
                self.logger.info("Realizando update...")
                cmd = [
                    'svn', 'update',
                    local_path,
                    '--username', self.credentials['username'],
                    '--password', self.credentials['password'],
                    '--non-interactive',
                    '--trust-server-cert'
                ]

            # Para Windows, usar shell=True
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                self.logger.error(f"Error en operación SVN: {result.stderr}")
                return False
            
            self.logger.info(f"Operación exitosa: {result.stdout}")
            return True

        except Exception as e:
            self.logger.error(f"Error en operaciones SVN: {str(e)}")
            return False

    def create_release_tag(self, site_config: Dict) -> bool:
        try:
            # Extraer la versión base y el último número
            base_version = "SVE_10_0_"
            
            # Obtener el último número de versión (por defecto comenzar en 39)
            try:
                with open('last_tag_version.txt', 'r') as f:
                    last_version = int(f.read().strip())
            except (FileNotFoundError, ValueError):
                last_version = 39
            
            # Incrementar el número de versión
            new_version = last_version + 2
            full_version = f"{base_version}{new_version}"
            
            self.logger.info(f"Creando tag: {full_version}")

            source_url = f"{self.svn_url}/branches/SVE_5_7_1_mhcp"
            target_url = f"{self.svn_url}/tags/{full_version}"

            cmd = [
                'svn', 'copy',
                source_url,
                target_url,
                '-m', f"Creating release tag {full_version}",
                '--username', self.credentials['username'],
                '--password', self.credentials['password'],
                '--non-interactive',
                '--trust-server-cert'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                self.logger.error(f"Error al crear tag: {result.stderr}")
                return False
            
            # Guardar el nuevo número de versión
            with open('last_tag_version.txt', 'w') as f:
                f.write(str(new_version))
            
            self.logger.info(f"Tag creado exitosamente: {full_version}")
            return True

        except Exception as e:
            self.logger.error(f"Error al crear tag en SVN: {str(e)}")
            return False
        
    def checkout_project(self, project_name):
        """
        Hacer checkout de un proyecto específico de SVN
        """
        try:
            # Ruta base del repositorio SVN
            repo_base_url = "https://localhost/svn/test_repo/branches/SVE_5_7_1_mhcp"
            project_url = f"{repo_base_url}/{project_name}"
            
            # Directorio local para checkout
            local_path = os.path.join(os.getcwd(), 'projects', project_name)
            
            # Crear directorio si no existe
            os.makedirs(local_path, exist_ok=True)
            
            # Comando de checkout de SVN
            checkout_cmd = [
                'svn', 'checkout',
                project_url,
                local_path,
                '--username', self.credentials['username'],
                '--password', self.credentials['password']
            ]
            
            # Ejecutar checkout
            checkout_result = subprocess.run(checkout_cmd, capture_output=True, text=True)
            
            if checkout_result.returncode != 0:
                raise Exception(f"Error en checkout: {checkout_result.stderr}")
            
            return local_path
        
        except Exception as e:
            self.logger.error(f"Error al hacer checkout de {project_name}: {str(e)}")
            raise