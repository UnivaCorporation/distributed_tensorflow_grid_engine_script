# tortuga_tensorflow

## Install Puppet module

Build module:

```shell
puppet module build 
```

Install:

```shell
puppet module install pkg/univa-tortuga_tensorflow-0.1.0.tar.gz
```

Add `--force` argument if Puppet module already installed.

## Enable tortuga_tensorflow module

Create the following file `/etc/puppetlabs/code/environments/production/hieradata/tortuga-execd.yaml`:

```yaml
---
version: 5

classes:
  - tortuga_tensorflow
```

to enable installation of Tensorflow on all nodes in the `execd`
software profile.
