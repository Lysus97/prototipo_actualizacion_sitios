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
            # Obtener versión del tag desde la configuración
            version_to = site_config.get('prefix', "SVE_10_0_39")
            
            self.logger.info(f"Creando tag: {version_to}")

            # Construir rutas
            source_url = f"{self.svn_url}/branches/SVE_5_7_1_mhcp"
            target_url = f"{self.svn_url}/tags/{version_to}"

            # Crear comando SVN copy con la opción -F para forzar
            cmd = [
                'svn', 'copy',
                source_url,
                target_url,
                '-m', f"Creating release tag {version_to}",
                '--username', self.credentials['username'],
                '--password', self.credentials['password'],
                '--force',  # Añadir esta opción para sobrescribir tags existentes
                '--non-interactive',
                '--trust-server-cert'
            ]

            # Para Windows, usar shell=True
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                self.logger.error(f"Error al crear tag: {result.stderr}")
                return False
            
            self.logger.info(f"Tag creado exitosamente: {version_to}")
            return True

        except Exception as e:
            self.logger.error(f"Error al crear tag en SVN: {str(e)}")
            return False