def allowed_types_to_str(allowed_types, delimiter=", "):
    if isinstance(allowed_types, tuple):
        return delimiter.join(t.__name__ for t in allowed_types)
    else:
        return allowed_types.__name__


def check_type(element, allowed_types, message=None, checker=isinstance):
    if message is None:
        message = ('The passed object is type: {type_}; '
                   'expected one of: {allowed_types}.')

    if not checker(element, allowed_types):
        raise TypeError(message.format(
            type_=type(element).__name__,
            allowed_types=allowed_types_to_str(allowed_types),
        ))
    else:
        return element
