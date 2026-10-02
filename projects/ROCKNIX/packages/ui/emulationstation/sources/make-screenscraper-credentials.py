#!/usr/bin/env python3
"""Generate an obfuscated header from private release-build credentials.

The key ships with the client: this prevents casual plaintext discovery, not
extraction by a determined user. Never commit the private JSON input.
"""
import json
import secrets
import sys
from pathlib import Path
from urllib.parse import urlencode


def main():
    private, output = map(Path, sys.argv[1:])
    header = "#pragma once\n"
    if private.is_file():
        config = json.loads(private.read_text())
        login, password = config.get("devid", ""), config.get("devpassword", "")
        if not isinstance(login, str) or not isinstance(password, str) or not login or not password:
            raise SystemExit("ScreenScraper private config requires devid and devpassword strings")
        payload = urlencode({"devid": login, "devpassword": password}).encode("ascii")
        key = secrets.token_bytes(len(payload))
        encrypted = bytes(a ^ b for a, b in zip(payload, key))
        numbers = lambda data: ",".join(str(value) for value in data)
        header += "#include <string>\n"
        header += "inline std::string butterflyScreenScraperLogin() {\n"
        header += "  static const unsigned char data[] = {" + numbers(encrypted) + "};\n"
        header += "  static volatile unsigned char key[] = {" + numbers(key) + "};\n"
        header += "  std::string result(sizeof(data), '\\0');\n"
        header += "  for (size_t i = 0; i < sizeof(data); ++i) result[i] = data[i] ^ key[i];\n"
        header += "  return result;\n}\n"
        header += "#ifndef SCREENSCRAPER_DEV_LOGIN\n"
        header += "#define SCREENSCRAPER_DEV_LOGIN butterflyScreenScraperLogin()\n#endif\n"
        header += '#undef SCREENSCRAPER_SOFTNAME\n#define SCREENSCRAPER_SOFTNAME "ButterflyOS"\n'
        print("ScreenScraper: private release credentials enabled (values hidden)")
    else:
        print("ScreenScraper: private release credentials absent; support disabled")
    output.write_text(header)


if __name__ == "__main__":
    main()
