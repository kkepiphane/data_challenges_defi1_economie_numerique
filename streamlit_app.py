"""
POINT D'ENTREE DE DEPLOIEMENT — Streamlit Cloud
================================================
Streamlit Cloud cherche par defaut un `streamlit_app.py` a la racine du depot.
Ce fichier existe pour ca, et ne fait rien d'autre que deleguer.

Le code de l'application reste ou il doit etre : `dashboard/`. Une plateforme
d'hebergement ne dicte pas l'architecture d'un projet — elle recoit un point
d'entree, c'est tout.

En local, les deux commandes sont equivalentes :
    streamlit run streamlit_app.py
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "dashboard"))

from app import main  # noqa: E402

main()
