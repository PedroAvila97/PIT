from werkzeug.security import check_password_hash

# Hash que tienes almacenado
stored_hash = "scrypt:32768:8:1$K05aXKCTNZlOCeuC$3c0fa52ffd41c43f82884eb246b363c47fa765e63ef781a851582507ae389c96f2e9f7682ac0cb36ded44c2a046fc4bcadcec3054a842e2c5e6d17ce8566c7c4"

# Contraseña que el usuario ingresa
password_to_check = "12345"

# Verificar si la contraseña coincide
if check_password_hash(stored_hash, password_to_check):
    print("La contraseña es válida")
else:
    print("La contraseña es incorrecta")
