def apply_updates(instance, data: dict):
    immutable = getattr(instance, "__immutable_fields__", set())

    for key, value in data.items():
        if key in immutable:
            continue
        if hasattr(instance, key):
            setattr(instance, key, value)