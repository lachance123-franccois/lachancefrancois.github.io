from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

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
    "housing": {"enabled": True, "city": "Toulouse", "max_price": 600,
                "crous_tool_id": 44, "bounds": None},
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


def cmd_collect(args, config: dict) -> int:
    session = make_session(config)
    feeds = load_feeds(config["feeds"])
    if not any(v for k, v in feeds.items() if not k.startswith("_")):
        logger.warning(
            "aucun flux configuré dans %s — seul le CROUS sera interrogé. "
            "Utiliser `discover` pour en trouver, puis `check` pour vérifier.",
            config["feeds"])

    housing = config["housing"]
    started = time.time()

    try:
        offers = collect_all(
            session, feeds,
            housing_city=housing["city"],
            housing_max_price=housing["max_price"],
            with_housing=housing["enabled"] and not args.no_housing,
            crous_tool_id=housing.get("crous_tool_id", 44),
            crous_bounds=housing.get("bounds"),
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


def cmd_discover(args, config: dict) -> int:
    """Interroge une page et liste les flux qu'elle déclare elle-même.

    C'est la bonne façon de remplir config/feeds.json : deviner une adresse
    de flux mène à des 404, alors qu'un site qui en publie un le signale
    dans son en-tête HTML.
    """
    session = make_session(config)
    feeds = session.discover_feeds(args.url)

    if not feeds:
        print(f"\nAucun flux déclaré sur {args.url}")
        print("\nÀ essayer :")
        print("  - la page d'accueil du site plutôt qu'une page de résultats")
        print("  - la page « actualités » ou « offres », qui porte souvent le flux")
        print("  - chercher « <nom du site> RSS » dans un moteur de recherche")
        print("\nSi le site n'expose aucun flux, ne pas le contourner :")
        print("  une source qui ne veut pas être lue automatiquement ne doit pas l'être.")
        return 1

    print(f"\n{len(feeds)} flux déclaré(s) sur {args.url}\n")
    for feed in feeds:
        print(f"  {feed['title']}")
        print(f"    {feed['url']}\n")
    print("À recopier dans config/feeds.json, sous la bonne catégorie :")
    print('  { "name": "…", "url": "…" }')
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

    p = sub.add_parser("discover", help="liste les flux RSS déclarés par une page")
    p.add_argument("url", help="adresse de la page à inspecter")
    p.set_defaults(func=cmd_discover)

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