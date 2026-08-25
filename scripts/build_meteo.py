#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend index.html a partir d'un fichier de donnees JSON.

Ce script ne contacte aucune API : il ne fait que rendre. Les donnees lui sont
fournies par fetch_meteo.py. Separer les deux garantit qu'aucun chiffre ne peut
etre invente ici, et permet de tester le rendu sans acces Pennylane.

Usage: build_meteo.py <data.json> <sortie.html>
"""
import json
import sys
from datetime import date

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
        "aout", "septembre", "octobre", "novembre", "decembre"]
MOIS_ACCENTS = {"fevrier": "février", "aout": "août", "decembre": "décembre"}


def date_fr(iso):
    d = date.fromisoformat(iso)
    mois = MOIS[d.month - 1]
    return "%s %d %s %d" % (JOURS[d.weekday()], d.day, MOIS_ACCENTS.get(mois, mois), d.year)


def n(v):
    """Espace insecable fine comme separateur de milliers, comme la page existante."""
    return "{:,}".format(int(v)).replace(",", chr(32))


def pct(part, total):
    return 0 if not total else round(100.0 * part / total)


def bar(value, vmax):
    """Largeur de barre en %, arrondie comme dans la page d'origine."""
    if not vmax:
        return 0
    return max(1, round(100.0 * value / vmax))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(data, template):
    total = data["dossiers_tenue_complete"]
    transac = data["transactions_a_reconcilier"]
    frs = data["factures_fournisseurs"]
    clts = data["factures_clients"]
    deco = data["bancaire_deconnecte"]

    top = sorted(data["top"], key=lambda r: r["transac"] + r["frs"] + r["clts"], reverse=True)[:10]
    vmax = (top[0]["transac"] + top[0]["frs"] + top[0]["clts"]) if top else 0

    top_rows = []
    for i, r in enumerate(top, 1):
        charge = r["transac"] + r["frs"] + r["clts"]
        w = bar(charge, vmax)
        full = " full" if w >= 100 else ""
        top_rows.append(
            '      <div class="bar-row"><div class="name"><span class="rank">%02d</span>%s</div>'
            '<div class="bar-track"><div class="bar-fill%s" style="width:%d%%"></div></div>'
            '<div class="num">%s</div></div>' % (i, esc(r["nom"]), full, w, n(charge)))

    table_rows = []
    for r in top:
        table_rows.append(
            "          <tr><td>%s</td><td>%s</td>"
            '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
            % (esc(r["nom"]), esc(r["collaborateur"] or "—"),
               n(r["transac"]), n(r["frs"]), n(r["clts"])))

    out = template
    for key, val in [
        ("__DATE_FR__", date_fr(data["date"])),
        ("__DOSSIERS__", n(total)),
        ("__KPI_TRANSAC__", n(transac)),
        ("__KPI_FRS__", n(frs)),
        ("__KPI_CLTS__", n(clts)),
        ("__BAR_FRS__", str(bar(frs, transac))),
        ("__BAR_CLTS__", str(bar(clts, transac))),
        ("__DECO__", n(deco)),
        ("__DECO_PCT__", str(pct(deco, total))),
        ("__TOP_ROWS__", "\n".join(top_rows)),
        ("__TABLE_ROWS__", "\n".join(table_rows)),
        ("__FOOTER_NOTE__", esc(data.get("footer_note", ""))),
    ]:
        out = out.replace(key, val)

    if "__" in out.replace("__", "", 0) and any(k in out for k in ("__DATE_FR__", "__TOP_ROWS__")):
        raise SystemExit("Rendu incomplet : un placeholder n'a pas ete remplace.")
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = json.load(open(sys.argv[1], encoding="utf-8"))

    required = ["date", "dossiers_tenue_complete", "transactions_a_reconcilier",
                "factures_fournisseurs", "factures_clients", "bancaire_deconnecte", "top"]
    missing = [k for k in required if data.get(k) is None]
    if missing:
        raise SystemExit("Donnees incompletes, rendu annule. Champs manquants : %s" % ", ".join(missing))
    if not data["top"]:
        raise SystemExit("Donnees incompletes, rendu annule : le Top 10 est vide.")

    import os
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")
    html = render(data, open(tpl_path, encoding="utf-8").read())
    open(sys.argv[2], "w", encoding="utf-8").write(html)
    print("index.html rendu : %d dossiers, %s transactions." % (
        data["dossiers_tenue_complete"], n(data["transactions_a_reconcilier"])))


if __name__ == "__main__":
    main()
