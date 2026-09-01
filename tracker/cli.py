#!/usr/bin/env python3
"""
Point d'entrée unique.

Remplace `main.py`, `collector.py` et `test.py`, qui faisaient trois fois le
même travail avec trois modèles de données différents et n'étaient jamais
d'accord entre eux (`collector.py` écrivait un JSON que personne ne lisait,
`main.py` écrivait en base, `test.py` importait une classe `CROUSScraper` qui
n'existe pas).

Autre changement notable : la pause aléatoire de 30 à 180 secondes placée en
tête de `run_safe_scraping()` a disparu. Elle rendait tout test impossible et
n'apportait rien — l'espacement des requêtes se gère par requête, pas par une
sieste au démarrage. Pour éviter de lancer la collecte à heure fixe, c'est le
`cron` de GitHub Actions qui décale, pas le programme.

Usage :
    python -m tracker.cli collect            collecte + export
    python -m tracker.cli collect --notify   collecte + export + email
    python -m tracker.cli check              teste chaque source, sans rien écrire
    python -m tracker.cli stats              état de la base
    python -m tracker.cli export             régénère le JSON du site
    python -m tracker.cli cleanup --days 90  purge les vieilles offres
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from .db import Store
from .export import export_json
from .http import PoliteSession, DEFAULT_UA
from .models import Offer
from .notify import Mailer, MissingCredentials
from .sources import check_sources, collect_all, load_feeds

logger = logging.getLogger("tracker")

DEFAULT_CONFIG = {
    "database": "data/offers.db",
    "feeds": "config/feeds.json",
    "export": "data/offers.json",
    "cache_dir": ".cache",
    "min_delay_seconds": 2,
    "housing": {"enabled": True, "city": "Toulouse", "max_price": 600},
    "notify": {"enabled": False, "recipient": ""},
}


def load_config(path: str) -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        config.update(json.loads(Path(path).read_text(encoding="utf-8")))
    except FileNotFoundError:
        logger.info("pas de %s : valeurs par défaut utilisées", path)
    except json.JSONDecodeError as exc:
        logger.error("%s est mal formé : %s", path, exc)
        sys.exit(2)
    return config


def make_session(config: dict) -> PoliteSession:
    return PoliteSession(
        user_agent=os.environ.get("TRACKER_USER_AGENT", DEFAULT_UA),
        cache_dir=config["cache_dir"],
        min_delay=float(config["min_delay_seconds"]),
    )


# ---------------------------------------------------------------------------
def cmd_collect(args, config: dict) -> int:
    session = make_session(config)
    feeds = load_feeds(config["feeds"])
    if not feeds:
        logger.error("aucun flux configuré — voir %s", config["feeds"])
        return 1

    housing = config["housing"]
    started = time.time()

    try:
        offers = collect_all(
            session, feeds,
            housing_city=housing["city"],
            housing_max_price=housing["max_price"],
            with_housing=housing["enabled"] and not args.no_housing,
        )
    except Exception as exc:                       # noqa: BLE001
        logger.error("collecte interrompue : %s", exc, exc_info=True)
        return 1

    duration = time.time() - started

    with Store(config["database"]) as store:
        inserted = store.insert(offers)
        store.log_run("all", len(offers), inserted, duration)
        export_json(store, config["export"])

        print(f"\n{len(offers)} offre(s) collectée(s), {inserted} nouvelle(s) "
              f"en {duration:.1f}s")

        if args.notify:
            recipient = config["notify"].get("recipient") or os.environ.get("NOTIFY_TO", "")
            if not recipient:
                logger.error("destinataire absent (config notify.recipient ou NOTIFY_TO)")
                return 1
            pending = store.pending()
            try:
                mailer = Mailer.from_env()
            except MissingCredentials as exc:
                logger.error("%s", exc)
                return 1
            if mailer.send_digest(recipient, pending):
                store.mark_notified([o["id"] for o in pending])
            else:
                return 1
    return 0


def cmd_check(args, config: dict) -> int:
    session = make_session(config)
    feeds = load_feeds(config["feeds"])
    report = check_sources(session, feeds)

    width = max(len(r["source"]) for r in report) if report else 10
    print(f"\n{'Source':<{width}}  {'Type':<11} {'État':<12} {'Entrées':>7}  Temps")
    print("-" * (width + 44))
    for row in report:
        print(f"{row['source']:<{width}}  {row['kind']:<11} "
              f"{row['status']:<12} {row['entries']:>7}  {row['seconds']}s")

    dead = [r for r in report if r["status"] != "ok"]
    print(f"\n{len(report) - len(dead)}/{len(report)} source(s) opérationnelle(s)")
    if dead:
        print("À corriger ou retirer de config/feeds.json :")
        for row in dead:
            print(f"  - {row['source']} ({row['status']})")
    return 0


def cmd_stats(args, config: dict) -> int:
    with Store(config["database"]) as store:
        stats = store.stats()
    print(f"\nTotal : {stats['total']} offre(s), {stats['pending']} en attente de notification")
    for kind, values in sorted(stats["by_kind"].items()):
        print(f"  {kind:<12} {values['total']:>4} (en attente : {values['pending']})")
    if stats["last_runs"]:
        print("\nDernières exécutions :")
        for run in stats["last_runs"]:
            print(f"  {run['started_at']}  {run['found']:>3} vues, "
                  f"{run['inserted']:>3} nouvelles  [{run['status']}]")
    return 0


def cmd_export(args, config: dict) -> int:
    with Store(config["database"]) as store:
        count = export_json(store, config["export"])
    print(f"{count} offre(s) exportée(s) vers {config['export']}")
    return 0


def cmd_cleanup(args, config: dict) -> int:
    with Store(config["database"]) as store:
        removed = store.cleanup_old(args.days)
    session = make_session(config)
    purged = session.purge_cache()
    print(f"{removed} offre(s) et {purged} fichier(s) de cache supprimé(s)")
    return 0


# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracker",
        description="Veille automatisée : stages, thèses et logement étudiant.",
    )
    parser.add_argument("--config", default="config/config.json")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("collect", help="collecte les offres et met à jour la base")
    p.add_argument("--notify", action="store_true", help="envoie le digest par email")
    p.add_argument("--no-housing", action="store_true", help="ignore les logements")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("check", help="teste chaque source sans rien écrire")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("stats", help="affiche l'état de la base")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("export", help="régénère le JSON lu par le site")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("cleanup", help="supprime les offres et le cache anciens")
    p.add_argument("--days", type=int, default=90)
    p.set_defaults(func=cmd_cleanup)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    config = load_config(args.config)
    try:
        return args.func(args, config)
    except KeyboardInterrupt:
        print("\ninterrompu")
        return 130


if __name__ == "__main__":
    sys.exit(main())