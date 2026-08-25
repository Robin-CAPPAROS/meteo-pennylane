# Job quotidien « Météo Pennylane »

Reconstruit `index.html` chaque matin ouvré à 7h15 (Paris) à partir des données
de production Pennylane, puis commit et push sur `main`.

## Pièces

| Fichier | Rôle |
|---|---|
| `template.html` | Gabarit. Le bloc `<style>` est repris **octet pour octet** de la page validée : la charte ne peut pas dériver. |
| `build_meteo.py` | Rendu pur `data.json` → `index.html`. Ne contacte aucune API. |

Le rendu est séparé de la collecte pour qu'aucun chiffre ne puisse être fabriqué
à l'étape de rendu : `build_meteo.py` refuse de produire une page si un champ
manque ou si le Top 10 est vide.

## Format de `data.json`

```json
{
  "date": "2026-08-25",
  "dossiers_tenue_complete": 716,
  "transactions_a_reconcilier": 18474,
  "factures_fournisseurs": 4236,
  "factures_clients": 1098,
  "bancaire_deconnecte": 89,
  "footer_note": "Ceci est un envoi de test.",
  "top": [
    {"nom": "...", "collaborateur": "...", "transac": 0, "frs": 0, "clts": 0}
  ]
}
```

## Collecte (via le serveur MCP Pennylane)

Il n'existe pas d'endpoint agrégé au niveau cabinet : tout est **par dossier**.

| Donnée | Appel | Champ |
|---|---|---|
| Liste des dossiers + collaborateur | `list_firm_file` (paginé, 100/page) | `name`, `accountant` |
| Transactions à réconcilier | `getScopeCountsCompanyAccountantsTransactions` | `accounting_needed_count` |
| Factures fournisseurs à saisir | `getScopeCountsV2...CashBasedAccountingInvoices` `direction=supplier` | `unmatched_count` |
| Factures clients à saisir | idem, `direction=customer` | `unmatched_count` |
| Connexion bancaire | `getCompanyAccountConnections` | `connection_status != "connected"` |

## Règle de sécurité

Si une seule requête échoue, **ne pas pousser** : `index.html` reste sur son
dernier état valide et l'échec est signalé. Une page à moitié à jour est pire
que pas de mise à jour.

## Vérifier le rendu sans toucher au dépôt

```sh
python3 scripts/build_meteo.py data.json /tmp/preview.html
```
