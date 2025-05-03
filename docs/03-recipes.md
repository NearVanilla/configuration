# Recipes on how to do common stuff

Unless specified otherwise - assumption is your terminal directory is set to the root configuration directory.

## Updating plugins and their configuration

```sh
# Check for newest version of plugins defined in mineager.yml
$ mineager plugin status
# And download latest versions
$ mineager plugin update
# Some plugins will need to be updated manually
# Click on the links given by Mineager and download the updated jars
# Add jars to configuration/plugins and rename to remove any version number
# Update server configuration to use the new plugins,
# Upload them to b2 and run the server to let them perform config changes
$ ./scripts/code/sync_plugins.sh
# Go through all of the changed servers (check output above to see which did change)
# and verify the changes
$ # No command for that, sorry :/
# Push all of the updates
$ ./scripts/code/push_all.sh
```

## Adding new plugin

```sh
# Add the plugin to the MAIN plugins directory
cp ../MyPlugin/target/MyPlugin.jar ./plugins/MyPlugin.jar
# Add the plugin to the server jars config
./manage.py jars add-plugins ./server-config/survival/ ./plugins/MyPlugin.jar
# Upload to B2 - can use the sync_plugins.sh instead
./manage.py synchronize upload
```

After this is done, if you want to update the version of the plugin:

- Replace the jar
- Update the `jars.yaml` file by running `./manage.py jars update ./server-config/survival/`
- Upload the plugin jar with `./manage.py synchronize upload`
