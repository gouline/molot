# Basic

Basic project showing basic targets and environment arguments.

Run the following to see a list of targets:

```
./build.py list
```

Now you can run one of the defined targets:

```
./build.py ls
```

Next one requires an argument called `ENV`, you can either set it as an environment variable:

```
ENV=prod ./build.py hello
```

Alternatively, you can set it with a `--arg` flag:

```
./build.py hello --arg ENV=prod
```

Notice that `--arg` overrides the environment variable if you supply both:

```
ENV=dev ./build.py hello --arg ENV=prod
```

Have a look at the definition of the `hello` target, you'll notice that it's using the `config()` 
extraction from the build.yaml file in the same directory. These are freeform YAML, so you can use
any schema you like.
