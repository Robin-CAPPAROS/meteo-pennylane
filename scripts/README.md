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

Un seul endpoint suffit : `getCRMFlowCompanies` (via `run_operations`), celui qui
alimente la page « Mon cabinet > Production ». Il renvoie tout le portefeuille.

```
run_operations  operation_id=getCRMFlowCompanies
                query_params={"page": N, "per_page": 100, "current_fiscal_year": true}
```

`per_page` est **plafonné à 50** côté serveur même si on demande 100 : il faut donc
16 pages pour 776 dossiers. Boucler jusqu'à `pagination.hasNextPage == false`, et
vérifier que le nombre de dossiers collectés égale `pagination.totalEntries` — c'est
le garde-fou contre une page manquante silencieuse. Les réponses sont volumineuses
(~140 000 caractères par page) : elles sont écrites sur disque par le harnais, à
agréger en Python plutôt qu'à lire en contexte.

Ne pas passer par les endpoints par dossier (`getScopeCounts...`) : il en faudrait
environ 3 100 par exécution, soit plus de deux heures, pour le même résultat.

### Périmètre

`file_type == "accounting"` correspond exactement à « tenue complète » : 716
dossiers sur 776 au 25/08/2026, les autres étant `revision` ou `null`.

### Mapping des champs

| Donnée de la page | Champ |
|---|---|
| Raison sociale | `name` |
| Collaborateur | `accountant.full_name` |
| Transactions à réconcilier | `transactions.pending` |
| Factures fournisseurs à saisir | `supplier_invoices.pending` |
| Factures clients à saisir | `customer_invoices.pending` |
| Connexion bancaire déconnectée | `bank_accounts.disconnected_count > 0` |

`pending` vaut `entry + validation_needed` : c'est le total à traiter, et c'est la
colonne « Transac. » / « Fact. frs » / « Fact. clts » de l'export XLSX du cabinet.
Vérifié le 25/08/2026 contre la page validée : 716 dossiers, 89 banques
déconnectées et 1 098 factures clients retrouvés à l'identique.

## Règle de sécurité

Si une seule requête échoue, **ne pas pousser** : `index.html` reste sur son
dernier état valide et l'échec est signalé. Une page à moitié à jour est pire
que pas de mise à jour.

## Vérifier le rendu sans toucher au dépôt

```sh
python3 scripts/build_meteo.py data.json /tmp/preview.html
```
