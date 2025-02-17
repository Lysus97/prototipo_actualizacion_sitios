import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_reader import read_sites_excel, validate_environment_config

def test_excel_reading():
    try:
        # Leer el Excel
        sites = read_sites_excel("config/sites_config.xlsx")
        print("\nSitios leídos del Excel:")
        for site in sites:
            print(f"\nSitio encontrado:")
            for key, value in site.items():
                print(f"{key}: {value}")

        # Validar y transformar cada sitio
        print("\nSitios procesados con prefijos:")
        for site in sites:
            validated_site = validate_environment_config(site)
            print(f"\nSitio validado:")
            for key, value in validated_site.items():
                print(f"{key}: {value}")

    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")

if __name__ == "__main__":
    test_excel_reading()