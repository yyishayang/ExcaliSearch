# Contribuir a ExcaliSearch

¡Gracias por tu interés en colaborar con **ExcaliSearch**! Para mantener el código ordenado, seguro y comprensible, hemos definido las siguientes directrices. Participando en este proyecto, te comprometes a seguir este estándar.

## 1. Configurar el Entorno de Desarrollo

Para poder probar, compilar y ejecutar el proyecto localmente, asegúrate de contar con Node.js (v18+) y Python (3.10+):

1. **Clona tu repositorio Forkeado**
   ```bash
   git clone https://github.com/yyishayang/ExcaliSearch.git
   cd ExcaliSearch
   ```

2. **Backend (Python)**
   ```bash
   cd backend
   python -m venv venv
   # En Windows: venv\Scripts\activate
   # En macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend (Vite/React)**
   ```bash
   cd ../frontend
   npm install
   ```

## 2. Estándares de Código

- **Backend (Python)**:
  - Nos adherimos a la convención **PEP 8**. Utiliza un formateador como `black` y valida tu código con `flake8`.
  - Asegúrate de incluir **Type Hints** de Python en todas la firmas de métodos nuevos (ej. `def mi_funcion(texto: str) -> bool:`).
  - Todo el código debe llevar las cabeceras SPDX obligatorias según la especificación **REUSE** (la licencia del proyecto es AGPL-3.0-or-later).

- **Frontend (JavaScript/React)**:
  - Sigue la configuración nativa de **ESLint** y **Prettier** del proyecto. Puedes correr `npm run lint` antes de consolidar tu código.
  - Usa _Functional Components_ y Hooks para nuevos componentes de React. No utilices componentes de clase.
  - Nombrado: Nombres de carpetas y archivos React en `PascalCase` (ej. `ChatPanel.jsx`). Variables estáticas en `camelCase`.

## 3. Convención de Commits

Recuerda usar mensajes en los commits que sean descriptivos, como por ejemplo los definidos en: https://www.conventionalcommits.org/, donde la estructura del mensaje debe ser:
`<tipo>[ámbito opcional]: <descripción>`

**Tipos válidos**:
- `feat`: Una nueva característica.
- `fix`: Corrección de un error o _bug_.
- `docs`: Cambios exclusivos en documentos (README, LICENSE, CONTRIBUTING).
- `style`: Cambios de formato que no afectan al significado de la lógica del código (espacios, comas faltantes, etc).
- `refactor`: Un cambio en el código que ni corrige un error ni añade funcionalidad.
- `test`: Añadir o modificar pruebas.
- `chore`: Tareas o herramientas rutinarias de construcción/actualización.

*Ejemplo*: `feat(ocr): añadir validación de formato png para Tesseract`

## 4. Proceso de Pull Requests

1. Crea una nueva rama (**Branch**) a partir de `main` con un nombre descriptivo: `git checkout -b feature/nombre-de-tu-funcionalidad`.
2. Haz tus cambios localmente y compáralos con el estándar usando la herramienta oficial `reuse lint` para cerciorarte de que no hemos roto las firmas SPDX.
3. Haz un _push_ a tu rama: `git push origin feature/nombre-de-tu-funcionalidad`.
4. Abre una **Pull Request (PR)** hacia la rama principal orientada bajo una plantilla descriptiva que enumere qué solución provees y adjuntes capturas de ser necesario.
6. Si hay una rama develop activa será desde esta desde donde se creen las ramas nuevas de desarrollo.

## 5. Expectativas de Revisión

- **Tiempo de Respuesta**: Los mantenedores (@yyishayang, @david598Uni, @aslangallery, @albabsuarez) tratamos de revisar todas las PRs y _Issues_ en un plazo razonable de unos pocos días a semanas según disponibilidad (alguna vez incluso más tiempo).
- **Iteraciones**: Es muy común que te pidamos pequeños ajustes técnicos o cambios de diseño visual. Mantén la amabilidad del proceso.
- **Build & CI**: La PR no podrá _mergearse_ si arrastra advertencias críticas en el linter (`npm run lint`), omite licencias de REUSE o la evaluación estática falla.
