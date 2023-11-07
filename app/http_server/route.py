import re

from app.http_server.methods import HTTPMethod
from app.http_server.types import HTTPCallback

VARIABLES_REGEX = r"{([a-zA-Z]+)}"


class Route:
    def __init__(self, method: HTTPMethod, path: str, callback: HTTPCallback) -> None:
        if not path.startswith("/"):
            raise ValueError("Path must start with /")

        self.method = method
        self.path = path
        self.callback = callback

        self.variables = self.extract_variables()
        self.path_regex = self.compile_regex()

    def extract_variables(self) -> list:
        return re.findall(VARIABLES_REGEX, self.path)

    def compile_regex(self) -> re.Pattern:
        regex = "^" + re.escape(self.path) + "$"
        for variable in self.variables:
            regex = regex.replace(r"\{" + variable + r"\}", f"(?P<{variable}>.+)")
        return re.compile(regex)

    def path_matches_regex(self, path: str) -> bool:
        match = re.match(self.path_regex, path)
        return match is not None

    def parse_path(self, path: str) -> dict:
        match = re.match(self.path_regex, path)
        if match:
            return match.groupdict()
        return {}
