import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.svn_manager import SVNManager

def test_svn_operations():
    try:
        # Crear instancia de SVNManager
        svn_manager = SVNManager()
        
        print("\n1. Probando operaciones básicas de SVN...")
        result = svn_manager.handle_svn_operations({})
        print(f"Resultado operaciones SVN: {'Exitoso' if result else 'Fallido'}")
        
        print("\n2. Probando creación de tag...")
        tag_result = svn_manager.create_release_tag({})
        print(f"Resultado creación tag: {'Exitoso' if tag_result else 'Fallido'}")

    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")

if __name__ == "__main__":
    test_svn_operations()