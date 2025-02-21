<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!--=============== REMIXICONS ===============-->
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.2.0/fonts/remixicon.css" rel="stylesheet">

    <!--=============== CSS ===============-->
    <link rel="stylesheet" href="menu.css">

    <title>Universidad Sudamericana</title>

    <style>
        /* Estilos para el panel centrado */
        .panel {
            display: flex;
            justify-content: center;
            align-items: center;
            height: calc(100vh - 60px); /* Ajusta la altura restando la altura del header */
            background-color: #f0f0f0; /* Color de fondo del panel */
            font-size: 2rem; /* Tamaño de fuente */
            color: #333; /* Color del texto */
            text-align: center; /* Centrar texto */
        }
    </style>
</head>
<body>
    <!--=============== HEADER ===============-->
    <header class="header">
        <nav class="nav container">
            <div class="nav__data">
                <a href="#" class="nav__logo">
                    <i class="ri-school-line"></i> Universidad Sudamericana
                </a>
                
                <div class="nav__toggle" id="nav-toggle">
                    <i class="ri-menu-line nav__burger"></i>
                    <i class="ri-close-line nav__close"></i>
                </div>
            </div>

            <!--=============== NAV MENU ===============-->
            <div class="nav__menu" id="nav-menu">
                <ul class="nav__list">
                    <li><a href="#" class="nav__link">Inicio</a></li>
                    <li><a href="#" class="nav__link">Solicitudes</a></li>
                    <!--=============== DROPDOWN 1 ===============-->
                    <li class="dropdown__item">
                        <div class="nav__link">
                            Tickets <i class="ri-arrow-down-s-line dropdown__arrow"></i>
                        </div>
                        <ul class="dropdown__menu">
                            <li><a href="#" class="dropdown__link"><i class="ri-pie-chart-line"></i> Abiertos</a></li>
                            <li><a href="#" class="dropdown__link"><i class="ri-arrow-up-down-line"></i> Cerrados</a></li>
                            <li><a href="tickets.php" class="dropdown__link"><i class="ri-add-line"></i> Nuevo</a></li>
                        </ul>
                    </li>
                    <li><a href="#" class="nav__link">Contacto</a></li>
                    <!--=============== DROPDOWN 2 ===============-->
                    <li class="dropdown__item">
                        <div class="nav__link">
                            Usuarios <i class="ri-arrow-down-s-line dropdown__arrow"></i>
                        </div>
                        <ul class="dropdown__menu">
                            <li><a href="#" class="dropdown__link"><i class="ri-user-line"></i> Perfil</a></li>
                            <li><a href="#" class="dropdown__link"><i class="ri-lock-line"></i> Cuenta</a></li>
                            <li><a href="#" class="dropdown__link"><i class="ri-folder-add-line"></i> Mensajes</a></li>
                        </ul>
                    </li>
                    <li><a href="#" class="nav__link">Cerrar Sesion</a></li>
                </ul>
            </div>
        </nav>
    </header>


    <!--=============== MAIN JS ===============-->
    <script src="main.js"></script>
</body>
</html>
