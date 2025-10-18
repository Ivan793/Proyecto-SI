"""
Script para crear usuario administrador inicial
Ejecutar: python create_admin.py
"""
import asyncio
from datetime import datetime, timezone, date
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.core.firebase import firebase_client
from app.repositories.base_repository import BaseRepository
from app.core.firebase import Collections


async def create_admin_user():
    """Crea un usuario administrador en Firebase Auth y Firestore"""
    
    # Datos del administrador
    admin_email = "admin@unicesar.edu.co"
    admin_password = "Admin123#"  # Cambia esto por tu contraseña deseada
    
    print("=" * 60)
    print("CREANDO USUARIO ADMINISTRADOR")
    print("=" * 60)
    
    try:
        # Inicializar Firebase
        print("\n1. Inicializando Firebase...")
        firebase_client.initialize()
        print("   ✓ Firebase inicializado")
        
        # Verificar si el usuario ya existe en Auth
        print(f"\n2. Verificando si existe usuario en Auth: {admin_email}")
        user_exists = False
        firebase_user = None
        
        try:
            firebase_user = auth.get_user_by_email(admin_email)
            user_exists = True
            print(f"   ⚠ Usuario ya existe en Firebase Auth")
            print(f"   UID: {firebase_user.uid}")
            
            # Preguntar si desea actualizar la contraseña
            response = input("\n   ¿Desea actualizar la contraseña? (s/n): ")
            if response.lower() == 's':
                auth.update_user(
                    firebase_user.uid,
                    password=admin_password
                )
                print("   ✓ Contraseña actualizada en Firebase Auth")
            
        except auth.UserNotFoundError:
            print("   ✓ Usuario no existe, procediendo a crear...")
        
        # Crear usuario en Firebase Auth si no existe
        if not user_exists:
            print(f"\n3. Creando usuario en Firebase Authentication...")
            firebase_user = auth.create_user(
                email=admin_email,
                password=admin_password,
                display_name="Admin Sistema",
                disabled=False
            )
            print(f"   ✓ Usuario creado en Firebase Auth")
            print(f"   UID: {firebase_user.uid}")
        
        # Preparar datos para Firestore
        print(f"\n4. Verificando documento en Firestore...")
        user_repo = BaseRepository(Collections.USUARIOS, id_field="id_usuario")
        
        # Verificar si ya existe en Firestore
        existing_doc = await user_repo.get_by_id(firebase_user.uid)
        
        admin_data = {
            "id_usuario": firebase_user.uid,
            "tipo_documento": "CC",
            "identificacion": "0000000000",
            "nombres": "Admin",
            "apellidos": "Sistema",
            "genero": "Hombre",
            "identidad_sexual": "Heterosexual",
            "fecha_nacimiento": date(1990, 1, 1),
            "direccion": "Calle Principal",
            "pais": "Colombia",
            "ciudad": "Valledupar",
            "telefono": "+573001234567",
            "correo": admin_email,
            "rol": "Administrativo",
            "estado": "ACTIVO",
            "firebase_uid": firebase_user.uid,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        if existing_doc:
            print("   ⚠ Documento ya existe en Firestore")
            response = input("\n   ¿Desea actualizar el documento? (s/n): ")
            if response.lower() == 's':
                await user_repo.update(firebase_user.uid, admin_data)
                print("   ✓ Documento actualizado en Firestore")
        else:
            print("   ✓ Documento no existe, procediendo a crear...")
            await user_repo.create(admin_data, document_id=firebase_user.uid)
            print("   ✓ Documento creado en Firestore")
        
        # Resumen
        print("\n" + "=" * 60)
        print("✅ ADMINISTRADOR CREADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nCredenciales de acceso:")
        print(f"  Email:    {admin_email}")
        print(f"  Password: {admin_password}")
        print(f"  UID:      {firebase_user.uid}")
        print(f"\n⚠ IMPORTANTE: Cambia la contraseña después del primer login")
        print("=" * 60)
        
        return True
        
    except FirebaseError as e:
        print(f"\n❌ Error de Firebase: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def delete_admin_user():
    """Elimina el usuario administrador (útil para empezar de cero)"""
    admin_email = "admin@unicesar.edu.co"
    
    print("=" * 60)
    print("ELIMINANDO USUARIO ADMINISTRADOR")
    print("=" * 60)
    
    try:
        firebase_client.initialize()
        
        # Buscar usuario en Auth
        try:
            firebase_user = auth.get_user_by_email(admin_email)
            
            # Confirmar eliminación
            print(f"\nSe eliminará el usuario:")
            print(f"  Email: {admin_email}")
            print(f"  UID:   {firebase_user.uid}")
            
            response = input("\n¿Está seguro? (s/n): ")
            if response.lower() != 's':
                print("Operación cancelada")
                return
            
            # Eliminar de Auth
            auth.delete_user(firebase_user.uid)
            print("✓ Usuario eliminado de Firebase Auth")
            
            # Eliminar de Firestore
            user_repo = BaseRepository(Collections.USUARIOS)
            await user_repo.soft_delete(firebase_user.uid)
            print("✓ Usuario marcado como inactivo en Firestore")
            
            print("\n✅ Usuario administrador eliminado exitosamente")
            
        except auth.UserNotFoundError:
            print("⚠ Usuario no encontrado en Firebase Auth")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Menú principal"""
    print("\n" + "=" * 60)
    print("GESTIÓN DE USUARIO ADMINISTRADOR")
    print("=" * 60)
    print("\nOpciones:")
    print("  1. Crear/Actualizar administrador")
    print("  2. Eliminar administrador")
    print("  3. Salir")
    
    option = input("\nSeleccione una opción (1-3): ")
    
    if option == "1":
        asyncio.run(create_admin_user())
    elif option == "2":
        asyncio.run(delete_admin_user())
    elif option == "3":
        print("Saliendo...")
    else:
        print("Opción inválida")


if __name__ == "__main__":
    main()