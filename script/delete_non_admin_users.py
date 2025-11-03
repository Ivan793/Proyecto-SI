"""
Script para eliminar todos los usuarios de Firebase Authentication
excepto el administrador principal.

Ejecutar desde la raíz del proyecto:
    python -m script.delete_non_admin_users
"""

import asyncio
from firebase_admin import auth
from app.core.firebase import firebase_client


async def delete_non_admin_users():
    """Elimina todos los usuarios excepto el admin definido."""
    admin_email = "admin@unicesar.edu.co"  # correo del admin a conservar

    print("=" * 60)
    print("ELIMINACIÓN MASIVA DE USUARIOS")
    print("=" * 60)
    print(f"\n⚠ Se eliminarán todos los usuarios de Firebase Auth, excepto:")
    print(f"   - {admin_email}")
    print("\nEsta acción no se puede deshacer.")

    confirm = input("\n¿Desea continuar? (s/n): ").lower()
    if confirm != "s":
        print("Operación cancelada.")
        return

    # Inicializar Firebase
    print("\n1. Inicializando Firebase...")
    firebase_client.initialize()
    print("   ✓ Firebase inicializado correctamente")

    try:
        total_deleted = 0
        total_skipped = 0

        # Firebase Auth devuelve usuarios por lotes (máx. 1000 por página)
        print("\n2. Listando usuarios...")
        page = auth.list_users()

        while page:
            for user in page.users:
                if user.email == admin_email:
                    print(f"   ⚠ Se conserva usuario admin: {user.email}")
                    total_skipped += 1
                    continue

                try:
                    auth.delete_user(user.uid)
                    print(f"   ✓ Usuario eliminado: {user.email}")
                    total_deleted += 1
                except Exception as e:
                    print(f"   ❌ Error eliminando {user.email}: {str(e)}")

            # Paginación
            page = page.get_next_page()

        print("\n" + "=" * 60)
        print("   PROCESO FINALIZADO")
        print("=" * 60)
        print(f"Usuarios eliminados: {total_deleted}")
        print(f"Usuarios conservados: {total_skipped}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Ejecuta la limpieza"""
    asyncio.run(delete_non_admin_users())


if __name__ == "__main__":
    main()
