"""Entrypoint: two-phase dispatch (built-in subcommands, then dynamic service parsers)."""

from __future__ import annotations

import argparse
import json
import sys

from mgs import config, services
from mgs.errors import MgsError, UsageError

# Heavy submodules (executor->client->urllib, schema->csdl->xml.etree, auth->msal) are
# imported lazily inside the branches that need them, so --help / auth / --dry-run stay fast.


def _print_top_help() -> None:
    print("mgs — one CLI for Microsoft 365 (Microsoft Graph)\n")
    print("USAGE:")
    print("  mgs <service> <verb> [flags]")
    print("      verbs: list  get <id>  create  update <id>  delete <id>  <action> <id>  +helper")
    print("  mgs auth <login|logout|status>       browser sign-in (Entra ID)")
    print("  mgs schema <service>                 introspect fields, navigations, bound actions")
    print("  mgs skills install [--target ...]    install agent skills into a repo")
    print("  mgs generate-skills --out <dir>      write the SKILL.md tree to a folder\n")
    print("SERVICES:")
    for s in services.all_services():
        print(f"  {s.aliases[0]:<10} {s.description}")
    print("\nRun `mgs <service> --help` to see that service's verbs and +helpers.")
    print("Global flags: --dry-run  --beta  --page-all  --json  --params  --select/--filter/--top ...")


def _run(argv: list[str]) -> int:
    first = argv[0] if argv else ""

    if first in ("", "-h", "--help"):
        _print_top_help()
        return 0

    cfg = str(config.config_dir())

    if first == "auth":
        from mgs import auth_commands

        action = argv[1] if len(argv) > 1 else "status"
        print(json.dumps(auth_commands.run(action, cfg), indent=2))
        return 0

    if first == "schema":
        from mgs import schema

        alias = argv[1] if len(argv) > 1 else ""
        svc = services.resolve(alias)
        if svc is None:
            raise UsageError(f"unknown service: {alias}")
        print(json.dumps(schema.schema_value(cfg, svc, beta="--beta" in argv), indent=2))
        return 0

    if first == "generate-skills":
        from mgs import skills

        out_dir = "skills"
        filt = None
        rest = argv[1:]
        for i, tok in enumerate(rest):
            if tok == "--out" and i + 1 < len(rest):
                out_dir = rest[i + 1]
            elif tok == "--filter" and i + 1 < len(rest):
                filt = rest[i + 1]
        paths = skills.generate(out_dir=out_dir, filter=filt)
        print(json.dumps({"generated": len(paths), "out": out_dir}, indent=2))
        return 0

    if first == "skills":
        from mgs import skills as skillsmod

        action = argv[1] if len(argv) > 1 else "install"
        rest = argv[2:]
        if action in ("install", "sync"):
            dir_ = "."
            targets = None
            global_ = "--global" in rest
            prune = "--prune" in rest
            for i, tok in enumerate(rest):
                if tok == "--dir" and i + 1 < len(rest):
                    dir_ = rest[i + 1]
                elif tok == "--target" and i + 1 < len(rest):
                    targets = [rest[i + 1]] if rest[i + 1] != "all" else ["claude", "agents"]
            summary = skillsmod.install(dir=dir_, targets=targets, global_=global_, prune=prune)
            print(json.dumps(summary, indent=2))
            return 0
        raise UsageError(f"unknown skills action: {action}")

    svc = services.resolve(first)
    if svc is None:
        raise UsageError(f"unknown service: {first}")

    from mgs import commands, executor
    from mgs.helpers import registry

    sub = argv[1:]
    verb = sub[0] if sub else None

    helper = registry.get(svc.entity_type, verb)
    if helper is not None:
        parser = argparse.ArgumentParser(prog=f"mgs {svc.aliases[0]} {helper.name}")
        helper.add_arguments(parser)
        ns = parser.parse_args(sub[1:])
        opts = executor.opts_from_namespace(ns)
        token = "" if getattr(ns, "dry_run", False) else _get_token(cfg)
        print(json.dumps(helper.run(token, ns, opts), indent=2))
        return 0

    known = executor.GENERIC_VERBS | {h.name for h in registry.for_service(svc.entity_type)}
    if verb is not None and verb not in known and not verb.startswith("-"):
        # Bound action: validate against the metadata operations cache.
        from mgs import csdl

        beta = "--beta" in sub
        valid = {op["name"].lower() for op in csdl.load_operations_bound_to(cfg, svc.entity_type, beta)}
        if verb.lower() not in valid:
            raise UsageError(
                f"unknown action '{verb}' for {svc.aliases[0]}; valid actions: "
                + (", ".join(sorted(valid)) or "(none)")
            )
        ap = argparse.ArgumentParser(prog=f"mgs {svc.aliases[0]} {verb}")
        ap.add_argument("id")
        ap.add_argument("--json")
        ap.add_argument("--params")
        ap.add_argument("--dry-run", action="store_true")
        ap.add_argument("--beta", action="store_true")
        ns = ap.parse_args(sub[1:])
        opts = executor.opts_from_namespace(ns)
        plan = executor.build_plan(svc, verb, ns.id, opts)
        token = "" if opts.dry_run else _get_token(cfg)
        print(json.dumps(executor.execute(plan, opts, token), indent=2))
        return 0

    parser = commands.build_service_parser(svc)
    ns = parser.parse_args(sub)
    opts = executor.opts_from_namespace(ns)
    plan = executor.build_plan(svc, ns.verb, getattr(ns, "id", None), opts)
    token = "" if opts.dry_run else _get_token(cfg)
    out = executor.execute(plan, opts, token)
    print(json.dumps(out, indent=2))
    return 0


def _get_token(cfg: str) -> str:
    from mgs import auth

    return auth.get_token(cfg)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        return _run(argv)
    except MgsError as e:
        print(json.dumps(e.to_json()), file=sys.stderr)
        return e.exit_code
    except BrokenPipeError:
        return 0
