from typing import Callable
from app.http_server.methods import HTTPMethod
import re


class Route:
    def __init__(self, method: HTTPMethod, path: str, callback: Callable) -> None:
        assert path.startswith("/"), "Path must start with /"
        self.method = method
        self.path = path
        self.callback = callback

        self.variables = self.extract_variables()
        self.path_regex = self.compile_regex()

    def extract_variables(self) -> list:
        VARIABLES_REGEX = r"{([a-zA-Z]+)}"
        match = re.findall(VARIABLES_REGEX, self.path)
        return {variable: None for variable in match}

    def compile_regex(self) -> re.Pattern:
        regex = "^" + re.escape(self.path) + "$"
        for variable in self.variables:
            regex = regex.replace("\{" + variable + "\}", f"(?P<{variable}>.+)")
        return re.compile(regex)

    def path_matches_regex(self, path: str) -> bool:
        match = re.match(self.path_regex, path)
        return match != None

    def parse_path(self, path: str) -> dict:
        match = re.match(self.path_regex, path)
        if match:
            return match.groupdict()
        return {}
