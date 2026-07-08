_ALIGN_TO_MULTIPLE = 8

def pad_align(name: str) -> str:
    return name + " " * (-len(name) % _ALIGN_TO_MULTIPLE)

# TODO: add a mechanism to update progress on delay
