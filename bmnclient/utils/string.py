# JOK++
# TODO tests

def toSnakeCase(source: str) -> str:
    result = ['_' + c.lower() if c.isupper() else c for c in source]
    return "".join(result).lstrip('_')


def toCamelCase(source: str) -> str:
    source = source.split("_")
    return source[0] + "".join(c.title() for c in source[1:])
