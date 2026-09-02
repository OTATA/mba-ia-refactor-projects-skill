"""Models do domínio.

Importar as três entidades aqui garante que os mapeamentos estejam
registrados no metadata do SQLAlchemy antes de `create_all()` rodar.
"""

from .category import Category
from .task import Task
from .user import User

__all__ = ["Category", "Task", "User"]
