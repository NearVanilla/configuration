# Recipes on how to do common stuff

## Updating plugins and their configuration

```sh
# Check for newest version of plugins defined in mineager.yml
$ mineager plugin status
# And download latest versions
$ mineager plugin update
# Update server configuration to use the new plugins,
# upload them to b2 and run the server to let them perform config changes
$ ./scripts/code/sync_plugins.sh
# Go through all of the changed servers (check output above to see which did change)
# and verify the changes
$ # No command for that, sorry :/
# Push all of the updates
$ ./scripts/code/push_all.sh
```
