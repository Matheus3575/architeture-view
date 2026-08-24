def execute(registry, name):
    handler = registry[name]
    return handler()
