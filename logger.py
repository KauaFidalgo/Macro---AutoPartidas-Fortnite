
import logging
from pathlib import Path

from config import PASTA_REFERENCIAS


PASTA_PROJETO = Path(PASTA_REFERENCIAS).parent
ARQUIVO_LOG = PASTA_PROJETO / "historico.log"

logger = logging.getLogger("macro_lab")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.FileHandler(ARQUIVO_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

def registrar(mensagem):
    logger.info("%s", mensagem)
