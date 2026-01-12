# Custom Addons para Odoo 17 by DWU

Este repositorio contiene módulos personalizados desarrollados para **Odoo 17**.

Los addons aquí incluidos están pensados para ser utilizados junto al repositorio oficial de Odoo, **sin modificar el core**.

---

## 📦 Requisitos

- Odoo 17 (Community o Enterprise)
- Python 3.11
- PostgreSQL 13+
- Entorno virtual Python (recomendado)

---

## 📁 Estructura del proyecto

Para incluir los módulos de este proyecto a tu Odoo 17, creá una carpeta en la raíz del core con el nombre de tu preferencia. 

Por ejemplo, podría llamarse **"custom_addons"**.

Luego, incluir dicha carpeta en tu `odoo.conf` de esta manera:

```
addons_path = addons,custom_addons
```