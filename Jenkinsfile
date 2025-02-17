pipeline {
    agent any
    
    // Parámetros que definimos antes
    parameters {
        file(name: 'SITES_CONFIG', description: 'Excel con la configuración de sitios')
        choice(name: 'MAX_PARALLEL', choices: ['5', '3', '1'], description: 'Número máximo de actualizaciones paralelas')
        booleanParam(name: 'SKIP_DB_UPDATE', defaultValue: false, description: 'Omitir actualización de base de datos')
    }
    
    stages {
        stage('Setup') {
            steps {
                echo "Usando archivo de configuración: config/sites_config.xlsx"
            }
        }
        
        stage('Read Configuration') {
            steps {
                script {
                    sh 'python src/config_reader.py config/sites_config.xlsx'
                }
            }
        }
        
        stage('SVN Operations') {
            steps {
                script {
                    // Ejecutar operaciones SVN
                    sh 'python tests/test_svn_manager.py'
                }
            }
        }
        
        stage('Deploy Sites') {
            steps {
                script {
                    // Ejecutar el deployment
                    sh 'python tests/test_deployment.py'
                }
            }
        }
    }
    
    post {
        always {
            // Limpiar workspace
            cleanWs()
        }
        success {
            echo 'Pipeline ejecutado exitosamente'
        }
        failure {
            echo 'Pipeline falló'
        }
    }
}