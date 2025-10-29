import firebase_admin
from firebase_admin import credentials, firestore

# Inicializamos Firebase con las credenciales del JSON
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Creamos una instancia del cliente de Firestore
db = firestore.client()
