"""Safety layer for the tiered Team Quarters crafting stations.

Keeps construction/crafting transactional and limits recipe hit targets to the
visible scroll viewport. Installed after ``farming_stations`` so its wrappers
are seen by the station UI closures through normal module globals.
"""

from __future__ import annotations

import time

import pygame


_INSTALLED = False


def _refund_materials(manager, materials):
    """Return already consumed inputs to the player's normal inventory."""
    inventory = getattr(manager, "inventory", None)
    if not isinstance(inventory, dict):
        manager.inventory = {}
        inventory = manager.inventory
    for name, amount in dict(materials or {}).items():
        amount = max(0, int(amount))
        if amount:
            inventory[name] = int(inventory.get(name, 0)) + amount


def install_farming_stations_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    import citys.mucford.farming_stations as stations

    if not getattr(stations, "_transactional_jobs_installed", False):
        original_begin_recipe = stations.begin_station_recipe
        original_begin_upgrade = stations.begin_station_upgrade

        def begin_station_recipe(manager, station_id, recipe_name, now=None):
            recipes = stations._recipe_catalog(station_id)
            recipe = recipes.get(recipe_name)
            ingredients = dict(recipe.get("ingredients", {})) if recipe else {}
            ok, message = original_begin_recipe(
                manager, station_id, recipe_name, now=now)
            if ok:
                job = stations.station_node(manager, station_id).get("job")
                if isinstance(job, dict):
                    job["consumed_materials"] = ingredients
            return ok, message

        def begin_station_upgrade(manager, station_id, now=None):
            level = stations.station_level(manager, station_id)
            target = level + 1
            definition = stations.STATION_DEFINITIONS.get(station_id, {})
            tier_data = dict(definition.get("tiers", {}).get(target, {}))
            materials = dict(tier_data.get("materials", {}))
            gold = max(0, int(tier_data.get("gold", 0)))
            ok, message = original_begin_upgrade(manager, station_id, now=now)
            if ok:
                job = stations.station_node(manager, station_id).get("job")
                if isinstance(job, dict):
                    job["consumed_materials"] = materials
                    job["consumed_gold"] = gold
            return ok, message

        def process_station_jobs(manager, now=None):
            current = float(time.time() if now is None else now)
            root = stations._root_state(manager)
            completed = []
            for station_id, node in root["stations"].items():
                job = node.get("job")
                if not isinstance(job, dict):
                    continue
                finish_at = float(job.get("finish_at", current + 1.0))
                if current < finish_at:
                    continue

                try:
                    if job.get("kind") == "upgrade":
                        target = int(job.get("target_level", node.get("level", 0)))
                        node["level"] = max(
                            0, min(stations.MAX_STATION_TIER, target))
                        display = job.get("display_name", "upgrade")
                        message = f"Station completed: {display}."
                    else:
                        recipe_name = str(job.get("recipe", ""))
                        message = stations._complete_recipe(
                            manager, station_id, recipe_name)
                    node["completed_jobs"] = int(
                        node.get("completed_jobs", 0)) + 1
                    root["crafting_xp"] = int(root.get("crafting_xp", 0)) + 5
                except Exception as exc:
                    _refund_materials(manager, job.get("consumed_materials", {}))
                    refund_gold = max(0, int(job.get("consumed_gold", 0)))
                    if refund_gold:
                        manager.gold = int(getattr(manager, "gold", 0)) + refund_gold
                    title = stations.STATION_DEFINITIONS.get(
                        station_id, {}).get("title", station_id)
                    message = (
                        f"{title} job failed; all costs refunded: {exc}"
                    )

                node["job"] = None
                completed.append(message)
                stations._set_message(manager, message, current)
            return completed

        stations.begin_station_recipe = begin_station_recipe
        stations.begin_station_upgrade = begin_station_upgrade
        stations.process_station_jobs = process_station_jobs
        stations._transactional_jobs_installed = True

    if not getattr(stations, "_visible_recipe_hits_installed", False):
        original_draw_detail = stations._draw_station_detail

        def _draw_station_detail(menu, screen, station_id):
            original_draw_detail(menu, screen, station_id)
            panel = pygame.Rect(125, 55,
                                stations.SCREEN_WIDTH - 250,
                                stations.SCREEN_HEIGHT - 110)
            list_rect = pygame.Rect(panel.x + 30, panel.y + 280,
                                    panel.w - 60, panel.h - 335)
            viewport = pygame.Rect(list_rect.x + 10, list_rect.y + 45,
                                   list_rect.w - 20, list_rect.h - 55)
            menu.station_recipe_rects = [
                (rect, recipe_name)
                for rect, recipe_name in menu.station_recipe_rects
                if viewport.contains(rect)
            ]

        stations._draw_station_detail = _draw_station_detail
        stations._visible_recipe_hits_installed = True

    _INSTALLED = True
