# 04 One vault on several machines

Skip this if you use one machine.

I run Claude Code on a laptop and on two always-on machines. All three see the same vault through Syncthing.

## Why Syncthing

- **rsync** is one way. Two machines editing means one loses.
- **git** stalls on merge conflicts, and session logs conflict constantly because every session inserts at the same spot.
- **Syncthing** is two way, live and needs no server. Conflicts become `*.sync-conflict-*` files instead of merge stops.

Git stays, but as local history on one machine, not as the sync channel.

## Setup that worked

1. **Hub and spokes.** One always-on machine is the hub. The others connect only to it.
2. **Write `.stignore` before sharing the folder.** It never syncs, so it must be identical on every device:

   ```
   /secrets
   /.git
   /.trash
   /.obsidian/workspace*.json
   (?d).DS_Store
   (?d)._*
   ```

   Add your search index file if it lives inside the vault (it should not, see [03](03-vault-mcp.md)).
3. **Versioning on two machines.** Syncthing only versions changes that arrive from another device. Turn on staggered versioning on the hub, which catches edits from the laptop, and on the laptop, which catches edits that landed on the hub from anywhere else.
4. **Private network only.** If every device is on your LAN or a VPN, turn off global discovery, relays and usage reporting.

## Living with it

- **Conflicts.** Two machines edit one note while one is offline, and you get a conflict copy. A lint pass should list them, and a person merges them.
- **A paused device pauses sync.** If the VPN drops on one machine, its edits wait. A small watcher that alerts when a device has not been seen for a day pays for itself.
- **Comparing file lists across macOS and Linux:** sort both with `LC_ALL=C`, or the two `sort` commands disagree and you get a false diff.
- **Before the first sync, snapshot.** Tar the vault on each machine and tag the git repo. Merging two existing vaults is where files get lost.
