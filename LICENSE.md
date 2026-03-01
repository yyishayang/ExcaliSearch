# Licencia del Proyecto (Project License)

Este proyecto, **ExcaliSearch**, se distribuye bajo la licencia **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

## ¿Qué significa esta licencia?
La licencia AGPL-3.0 es una licencia de código abierto de copyleft fuerte (*strong copyleft*). Esto significa que tienes total libertad para usar, estudiar, modificar y distribuir este software. Sin embargo, impone una condición fundamental de reciprocidad: **cualquier modificación o trabajo derivado basado en este código también debe ser liberado bajo esta misma licencia AGPL-3.0**, incluso si el software no se distribuye tradicionalmente descargándolo sino que se ofrece como un servicio a través de una red (como un servicio en la nube o SaaS). Si hospedas una versión modificada de ExcaliSearch para que otros la usen por red, debes ofrecerles o facilitarles el acceso al código fuente de tu versión modificada.

## ¿Por qué usamos AGPL-3.0?
La elección de esta licencia viene estrictamente **determinada por nuestra dependencia de la biblioteca `PyMuPDF`** en el motor de extracción y procesamiento de documentos del backend. 

`PyMuPDF` se distribuye oficialmente bajo los términos de la licencia GNU AGPL v3.0. Dado que ExcaliSearch importa, enlaza y confía directamente en esta biblioteca para la manipulación profunda de PDFs, nuestro propio proyecto hereda automáticamente las condiciones de su copyleft, obligándonos a licenciar y liberar todo el código bajo la misma AGPL-3.0 para poder cumplir con dichas obligaciones legales impuestas por los creadores originales de `PyMuPDF`.

## Ausencia de Garantías
Este programa se distribuye de buena fe y con la esperanza de que sea útil, pero **SIN NINGUNA GARANTÍA**; ni siquiera la garantía implícita de COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. 

TODO EL SOFTWARE SE PROPORCIONA "TAL CUAL" (*AS IS*), sin garantías de ningún tipo, ya sean expresas o implícitas. En ningún caso los autores o titulares del copyright (ni los mantenedores de dependencias de terceros) serán responsables de ninguna reclamación, daño u otra responsabilidad, ya sea en una acción de contrato, agravio o de otro tipo, que surja de, o en conexión con el uso de este software o la manipulación de información subida al mismo.

## Texto Legal Completo
Las condiciones completas y los derechos están estipulados en el texto oficial de la Free Software Foundation.
Puedes leer el texto legal inalterado revisando el documento en nuestro propio repositorio: 
- [`LICENSES/AGPL-3.0-or-later.txt`](LICENSES/AGPL-3.0-or-later.txt)

O bien, visitando el sitio web oficial de GNU:
[https://www.gnu.org/licenses/agpl-3.0.html](https://www.gnu.org/licenses/agpl-3.0.html)
